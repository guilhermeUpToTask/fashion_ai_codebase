# update the database from the worker tasks
from io import BytesIO
import time
from typing import List, cast
from uuid import UUID
from celery import chain, group, Task
import requests
from sqlmodel import Session
from models.query import QueryImage, QuerySimilarProduct
from celery_app import app as celery_app
from core import storage
from core.vector_db.img_vector_crud import add_image_embedding
from backend.app.models.image import ImageDB, ImageUpdate, StatusEnum, ImageCreate
from models.label import LabelingResponse, StructuredLabel
from core.vector_db.chroma_db import chroma_client_wrapper
from core.vector_db.img_vector_crud import query_similar_imgs
from core.db import engine
from core.image_crud import (
    update_image,
    update_job_status,
    get_image_by_id,
    create_image,
)
from core.config import settings
import mimetypes
import base64
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def add(self, x, y):
    return x + y


# Helper Functions
def send_s3_img_to_ml_service(
    img_filename: str, bucket_name: str, service_url: str, timeout: int = 30
) -> requests.Response:
    """Downloads an image from S3 and send its to an ML service."""
    img_file = storage.download_file_from_s3(bucket=bucket_name, key=img_filename)
    mime_type, _ = mimetypes.guess_type(img_filename)
    files = {
        "img_file": (img_filename, img_file, mime_type or "application/octet-stream")
    }
    response = requests.post(url=service_url, files=files, timeout=timeout)
    return response


def parse_and_retry(response: requests.Response, task: Task, expected_type=list):
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
    autoretry_for=([requests.RequestException]),
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
                bucket_name=settings.S3_PRODUCT_BUCKET_NAME,
                service_url=f"{settings.ML_SERVICE_URL}/inference/image/crop_clothes",
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
                    bucket_name=settings.S3_PRODUCT_BUCKET_NAME,
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
) -> List[
    float
]:  # < return the vector that will be insert into the first arg of the save vector task
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
            bucket_name=settings.S3_PRODUCT_BUCKET_NAME,
            service_url=f"{settings.ML_SERVICE_URL}/inference/image/label",
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        # Using LabelingResponse(**data) is clean, but if the service returns extra fields you don’t expect, it’ll error. Consider .dict() in pydantic to filter unknowns, e.g. LabelingResponse.parse_obj(data) with Config.extra = "ignore".
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

    chroma_client = chroma_client_wrapper.get_client()
    with Session(engine) as session:
        cropped_img_metadata = get_image_by_id(id=cropped_img_id, session=session)

        if not cropped_img_metadata:
            logger.error(
                "[Job %s][Crop %s] → metadata not found, aborting",
                job_id,
                cropped_img_id,
            )
            raise ValueError("Cropped image metadata not found")

        logger.info(
            f"[Job %s][Crop %s] → about to set status STORING:{job_id} {cropped_img_id}"
        )

        cropped_img_metadata = update_job_status(
            session=session,
            job_image=cropped_img_metadata,
            new_status=StatusEnum.STORING,
            details=f"Step 3 of 3:Storing clothing items embeddings into vector database... current item:[{current_cropped_idx+1}]",
        )

        if not cropped_img_metadata.label:
            raise ValueError("cropped image metadata is missing its label!")

        logger.info(
            "[Job %s][Crop %s] → after STORING status: %s",
            job_id,
            cropped_img_id,
            cropped_img_metadata.status,
        )
        logger.info(
            f"[Job {job_id}][Crop {cropped_img_id}] → Preparing to store embedding with args:\n"
            f"  • img_id: {cropped_img_id}\n"
            f"  • vector_len: {len(storage_vector) if hasattr(storage_vector, '__len__') else 'N/A'}\n"
            f"  • label: {cropped_img_metadata.label}\n"
            f"  • collection: {collection_name}\n"
            f"  • chroma_session: {type(chroma_client).__name__}"
        )
        logger.info(
            f"[Job {job_id}][Crop {cropped_img_id}] → Embedding preview: {storage_vector[:5]}"
        )
        logger.info(
            f"[Job {job_id}][Crop {cropped_img_id}] → entering add_image_embedding"
        )

        try:
            label_obj = cropped_img_metadata.label
            if isinstance(label_obj, dict):
                label_obj = StructuredLabel(**label_obj)

            stored_img_id = add_image_embedding(
                img_id=cropped_img_id,
                img_vector=storage_vector,
                chroma_session=chroma_client,
                img_label=label_obj,
                collection_name=collection_name,
            )
        except Exception as e:
            logger.exception(
                "[Job %s][Crop %s] → Failed to store embedding: %s",
                job_id,
                cropped_img_id,
                str(e),
            )
            raise e

        if stored_img_id != cropped_img_metadata.id:
            raise ValueError(
                f"Critical error, ids mismatch - cropped_img_id:{cropped_img_id} stored_img_id:{stored_img_id}"
            )
        logger.info(
            "[Job %s][Crop %s] → embedding saved to vector DB",
            job_id,
            cropped_img_id,
        )
        cropped_img_metadata = update_job_status(
            session=session,
            job_image=cropped_img_metadata,
            new_status=StatusEnum.STORED,
            details=f"Cloth item[{current_cropped_idx+1}] vectors stored!",
        )

    return cropped_img_id


@celery_app.task(
    name="tasks.query_image_vector_task", bind=True
)  # bind gets acces to 'self'
def query_image_vector_task(
    self,
    query_vector: list[float],  # <-- This MUST be the first
    job_id: UUID,  # <- just for logging
    cropped_img_id: UUID,
    current_cropped_idx: int,
    collection_name: str,
) -> UUID:
    chroma_client = chroma_client_wrapper.get_client()
    query_id: UUID | None = None 
    with Session(engine) as session:
        query = QueryImage(
            input_image_id=cropped_img_id, model_version="yolo8-fashionCLIP"
        )
        query.similar_products = query_similar_imgs(
            query_vector=query_vector,
            n_results=3,
            collection_name=collection_name,
            chroma_session=chroma_client,
        )
        session.add(query)
        session.commit()
        query_id = query.id
        
    if not query_id:
        raise ValueError("Failed to create and retrieve QueryImage ID from the database.")
    return query_id


# this is wrong in the case of a empty array
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
    finalize_indexing = cast(Task, finalize_indexing_job_task)
    if not cropped_img_ids:
        finalize_indexing.apply_async(kwargs={"results": [], "job_id": job_id})
        return

    # create the parallel group of chains(label -> save)
    label_image = cast(Task, label_image_task)
    save_image_vector = cast(Task, save_image_vector_task)
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
                    collection_name=settings.IMAGES_COLLECTION_NAME,
                ),
            )
        )
        for idx, img_id in enumerate(cropped_img_ids)
    )
    # Context Passing: Be cautious that results passed to finalize_indexing_job_task is exactly the list of return values from save_image_vector_task. If any task errors, the chord may never fire, leaving the job in limbo. Consider adding an error callback or leveraging chord_error handlers to mark the job as failed.
    # create the chord: run the group and then the finalizer
    (header | finalize_indexing.s(job_id=job_id)).apply_async()


@celery_app.task(name="tasks.split_for_querying_task")
def split_for_querying_task(cropped_img_ids: list[UUID], job_id: UUID):
    logger.info(
        f"Spliting job {job_id} into {len(cropped_img_ids)} paralell tasks for querying"
    )
    finalize_querying = cast(Task, finalize_querying_job_task)
    if not cropped_img_ids:
        finalize_querying_job_task.apply_async(kwargs={"results": [], "job_id": job_id})  # type: ignore
    label_image = cast(Task, label_image_task)
    query_image = cast(Task, query_image_vector_task)

    header = group(
        (
            chain(
                label_image.s(
                    job_id=job_id, cropped_img_id=img_id, current_cropped_idx=idx
                ),
                query_image.s(
                    job_id=job_id,
                    cropped_img_id=img_id,
                    current_cropped_idx=idx,
                    collection_name=settings.IMAGES_COLLECTION_NAME,
                ),
            )
        )
        for idx, img_id in enumerate(cropped_img_ids)
    )
    (header | finalize_querying.s(job_id=job_id)).apply_async()


@celery_app.task(name="tasks.finalize_querying_job_task")
def finalize_querying_job_task(results, job_id: UUID):
    # results is the output of the group (list of crop IDs that were saved)
    logger.info(
        f"Finalizing job {job_id}. {len(results)} items processed for querying."
    )
    with Session(engine) as session:
        job_img = get_image_by_id(id=job_id, session=session)
        if not job_img:
            logger.error(f"image matedata not found for this job_id:{job_id}")
            raise ValueError("no Job img metadata found")
        message = "All items retrieved successfully"
        status = StatusEnum.COMPLETE
        if not results:
            message = "No cloth piece found in this image"
            status = StatusEnum.FAILED
        update_job_status(
            session=session,
            job_image=job_img,
            new_status=status,
            details=message,
        )
