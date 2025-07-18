# update the database from the worker tasks
from io import BytesIO
from typing import List, cast
from uuid import UUID
import celery
from celery import chain, group
import requests
from sqlmodel import Session
from app.celery import celery_app
from core import storage
from core.vector_db.img_vector_crud import add_image_embedding
from models.image import ImageDB, ImageUpdate, StatusEnum, ImageCreate
from models.label import LabelingResponse
from core.vector_db.chroma_db import persistent_client as chroma_client
from core.db import engine
from core.image_crud import (
    update_image,
    update_job_status,
    get_image_by_id,
    create_image,
)
from core.config import Settings
import mimetypes
import base64
import logging

logger = logging.getLogger(__name__)

# Helper Functions
def send_s3_img_to_ml_service(
    img_filename: str, bucket_name: str, service_url: str, timeout: int = 30
) -> requests.Response:
    """Downloads an image from S3 and send its to an ML service."""
    img_file = storage.download_file_from_s3(bucket=bucket_name, key=img_filename)
    mime_type, _ = mimetypes.guess_type(img_filename)
    files = {"file": (img_filename, img_file, mime_type or "application/octet-stream")}
    response = requests.post(url=service_url, files=files, timeout=timeout)
    return response


def parse_and_retry(response: requests.Response, task: celery.Task, expected_type=list):
    """
    Parse JSON payload from a requests.Response and retry on failure.

    Args:
        response (requests.Response): HTTP response to parse.
        task (celery.Task): Bound Celery task instance (self) for retry.
        expected_type (type): Expected Python type of the JSON payload.

    Returns:
        The parsed JSON payload if it matches expected_type.

    Raises:
        Retry exception via task.retry if parsing fails or type mismatches.
    """
    try:
        payload = response.json()
        if not isinstance(payload, expected_type):
            raise ValueError(
                f"Expected {expected_type.__name__} got {type(payload).__name__}"
            )
        return payload
    except (ValueError, requests.JSONDecodeError) as err:
        logger.error("Malformed response from ML service", exc_info=True)
        # retry the taks with the original exception
        raise task.retry(
            exc=err
        )  # maybe we need to add this to the autoretry for in the task


# ---CELERY TASKS ---
@celery_app.task(
    name="tasks.crop_image_task",
    bind=True,
    autoretry_for=(requests.RequestException),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)  # bind gets acces to 'self'
def crop_image_task(self, job_id: UUID) -> list[UUID]:
    """_summary_

    Args:
        job_id (UUID): the id of the main image uploaded

    Task to crop an original image
    """
    with Session(engine) as session:
        try:
            logger.info(f"Starting crop image task for job:{job_id}")
            job_img = get_image_by_id(id=job_id, session=session)
            if not job_img:
                raise ValueError("No job image was found")

            update_job_status(
                session=session,
                job_image=job_img,
                new_status=StatusEnum.CROPPING,
                details="Step 1 of 3: Decting clothing items...",
            )

            logger.info(f"Sending request to ml service for job:{job_id}")

            # sending image to cropping process - needs retry logic
            response = send_s3_img_to_ml_service(
                img_filename=job_img.filename,
                bucket_name=Settings.S3_PRODUCT_BUCKET_NAME,
                service_url=f"{Settings.ML_SERVICE_URL}/crop_clothes",
                timeout=20,
            )
            response.raise_for_status()

            logger.info(
                f"request succeffuly made it to service to crop cloth pieces. job:{job_id}"
            )
            logger.info(f"Starting to parse the cloth images recived. job:{job_id}")

            # parse the response
            b64_images: list[str] = parse_and_retry(
                response=response, task=self, expected_type=list
            )
            logger.info(f"{len(b64_images)} cloth pieces scanned. job:{job_id}")

            cropped_img_ids: list[UUID] = []
            for idx, b64_str in enumerate(b64_images):
                # decode and convert base64 to BytesIO in memory
                img_file = BytesIO(base64.b64decode(b64_str))
                # determinincstic s3 key
                img_filename = f"cropped_img_{idx}_{job_id}.png"
                s3_path = storage.upload_file_to_s3(
                    file_obj=img_file,
                    bucket_name=Settings.S3_PRODUCT_BUCKET_NAME,
                    object_name=img_filename,
                )
                logger.info(
                    f"{idx} image file saved of {len(b64_images)}. img_path:{s3_path}, job:{job_id}"
                )

                # create a imagedb for each crop - addl later atomacy db with transactions or session.begin
                # If the ML service returns the same bad payload repeatedly, exponential retries will repeat until max, which is fine. But if you retry after having already saved some crops, the task will duplicate records.
                # Suggestion: Before creating a new crop image, check if one for this job_id and this index already exists—skip or update instead of blindly inserting duplicates.
                img_in = ImageCreate(
                    path=s3_path,
                    filename=img_filename,
                    status=StatusEnum.CROPPED,
                    original_id=job_img.id,
                )
                new_img = create_image(session=session, image_in=img_in)

                cropped_img_ids.append(new_img.id)
                logger.info(
                    f"{idx} image metadata save into db from ${len(b64_images)}. job:{job_id}"
                )

            logger.info(f"all crop images saved succefully. job:{job_id}")
            update_job_status(
                session=session,
                job_image=job_img,
                new_status=StatusEnum.CROPPED,
                details="Step 1 of 2: Cloth Items Detected and Cropped.",
            )
            logger.info("crop image task finished!")

            return cropped_img_ids
        except Exception as e:
            logger.error(f"[{job_id}] Error while cropping image", exc_info=True)
            raise e


@celery_app.task(name="tasks.label_image_task", bind=True)  # bind gets acces to 'self'
def label_image_task(
    self, job_id: UUID, cropped_img_id: UUID, current_cropped_idx: int
) -> List[float]:  # < return the vector that will be insert into the first arg of the save vector task
    """_summary_

    Args:
        job_id (UUID): the id of the main image uploaded
        cropped_img_id (UUID): the id of the cropped image
    Task to label a cropped image of a cloth piece and gets the final vector representation.
    """
    with Session(engine) as session:
        job_img_metadata = get_image_by_id(id=job_id, session=session)
        cropped_img_metadata = get_image_by_id(id=cropped_img_id, session=session)

        if not job_img_metadata:
            raise ValueError(f"No job image metadata found for this job_id:{job_id}")
        if not cropped_img_metadata:
            raise ValueError(
                f"No cropped image metadata found for this cropp_img_id:{cropped_img_id}"
            )

        job_img_metadata = update_job_status(
            session=session,
            job_image=job_img_metadata,
            new_status=StatusEnum.ANALYZING,
            details=f"Step 2 of 3: Analyzing clothing items... current item:[{current_cropped_idx+1}]",
        )

        logger.info(
            f"Seingnd request with cropped_img:{cropped_img_id} to ml_service[label] for job:{job_id}"
        )
        response = send_s3_img_to_ml_service(
            img_filename=cropped_img_metadata.filename,
            bucket_name=Settings.S3_PRODUCT_BUCKET_NAME,
            service_url=f"{Settings.ML_SERVICE_URL}/label",
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        parsed_response = LabelingResponse(**data)
        logger.info(
            f"request succeffuly made it to service to analyze cloth piece:{cropped_img_id}. job:{job_id}"
        )

        new_cropped_img = ImageUpdate(
            label=parsed_response.label_data, status=StatusEnum.LABELLED
        )
        cropped_img_metadata = update_image(
            session=session, image_in=new_cropped_img, db_image=cropped_img_metadata
        )

        job_img_metadata = update_job_status(
            session=session,
            job_image=job_img_metadata,
            new_status=StatusEnum.ANALYZING,
            details=f"Step 2 of 3: Anazying clothing items... cloth item[{current_cropped_idx+1}] completed!",
        )

    return parsed_response.storage_vector


@celery_app.task(
    name="tasks.save_image_vector_task", bind=True
)  # bind gets acces to 'self'
def save_image_vector_task(
    self,
    storage_vector: list[float],  # <-- This MUST be the first
    job_id: UUID,
    cropped_img_id: UUID,
    current_cropped_idx: int,
    collection_name: str,
) -> UUID:
    """_summary_

    Args:
        job_id (UUID): the id of the main image uploaded

    Task to save the merged vector of image and its label into a vector db(chromadb) with the structured label as metadata.
    """
    with Session(engine) as session:
        job_img_metadata = get_image_by_id(id=job_id, session=session)
        cropped_img_metadata = get_image_by_id(id=cropped_img_id, session=session)

        if not job_img_metadata:
            raise ValueError(f"No job image metadata found for this job_id:{job_id}")
        if not cropped_img_metadata:
            raise ValueError(
                f"No cropped image metadata found for this cropp_img_id:{cropped_img_id}"
            )

        job_img_metadata = update_job_status(
            session=session,
            job_image=job_img_metadata,
            new_status=StatusEnum.STORING,
            details=f"Step 3 of 3:Storing clothing items embeddings into vector database... current item:[{current_cropped_idx+1}]",
        )

        if not cropped_img_metadata.label:
            raise ValueError("cropped image metadata is missing its label!")

        stored_img_id = add_image_embedding(
            img_id=cropped_img_id,
            img_vector=storage_vector,
            chroma_session=chroma_client,
            img_label=cropped_img_metadata.label,
            collection_name=collection_name,
        )
        if stored_img_id != cropped_img_metadata.id:
            raise ValueError(
                f"Critical error, ids mismatch - cropped_img_id:{cropped_img_id} stored_img_id:{stored_img_id}"
            )

        cropped_img_metadata = update_job_status(
            session=session,
            job_image=cropped_img_metadata,
            new_status=StatusEnum.STORED,
        )
        job_img_metadata = update_job_status(
            session=session,
            job_image=job_img_metadata,
            new_status=StatusEnum.STORING,
            details=f"Step 3 of 3:Storing clothing items embeddings into vector database... cloth item[{current_cropped_idx+1}] stored!",
        )

    return cropped_img_id


@celery_app.task(name="tasks.finalize_indexing_job_task")
def finalize_indexing_job_task(results, job_id: UUID):
    # results is the output of the group (list of crop IDs that were saved)
    logger.info(f"Finalizing job {job_id}. {len(results)} items processed.")
    with Session(engine) as session:
        job_img = get_image_by_id(id=job_id, session=session)
        if not job_img:
            logger.error(f"image matedata not found for this job_id:{job_id}")
            raise ValueError("no Job img metadata found")

        update_job_status(
            session=session,
            job_image=job_img,
            new_status=StatusEnum.COMPLETE,
            details="All items indexed successfully.",
        )


@celery_app.task(name="tasks.split_for_indexing_task")
def split_for_indexing_task(cropped_img_ids: list[UUID], job_id: UUID):
    """Fans out the processing for each crop."""
    logger.info(f"Splitting job {job_id} into {len(cropped_img_ids)} parallel tasks.")
    finalize_indexing = cast(celery.Task, finalize_indexing_job_task)
    if not cropped_img_ids:
        finalize_indexing.apply_async(kwargs={"results": [], "job_id": job_id})
        return

    # create the parallel group of chains(label -> save)
    label_image = cast(celery.Task, label_image_task)
    save_image_vector = cast(celery.Task, save_image_vector_task)
    header = group(
        (
            chain(
                label_image.s(
                    job_id=job_id, cropped_img_id=img_id, current_cropped_idx=idx
                ),
                save_image_vector.s(
                    job_id=job_id,
                    cropped_img_id=img_id,
                    current_cropped_idx=idx,
                    collection_name=Settings.IMAGES_COLLECTION_NAME,
                ),
            )
        )
        for idx, img_id in enumerate(cropped_img_ids)
    )
    # create the chord: run the group and then the finalizer
    (header | finalize_indexing.s(job_id=job_id)).apply_async()
