# update the database from the worker tasks
from io import BytesIO
import time
from typing import List, cast
from uuid import UUID
import uuid
from celery import Task, chain, chord, group
from celery.canvas import Signature
from psycopg2 import IntegrityError
import requests
from sqlmodel import Session, select
from models.job import Job, JobStatus, JobType
from models.product import Product, ProductImage
from models.result import IndexingResult, QueryResult
from celery_app import app as celery_app
from core import storage
from core.vector_db.img_vector_crud import add_image_embedding
from models.image import ImageFile
from models.label import LabelingResponse, StructuredLabel
from core.vector_db.chroma_db import chroma_client_wrapper
from core.db import engine
from core.config import settings
from utils.image_helpers import (
    build_image_filename,
    create_and_verify_pil_img,
    send_s3_img_to_service,
)
from utils.helpers import parse_json_response, safe_post_and_parse
import mimetypes
import base64
import logging
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


# celery tasks
# needs retry logic
@celery_app.task(name="task.cloth_detection_task", bind=True)
def cloth_detection_task(self, img_id: UUID) -> list[UUID]:
    logger.info(f"Starting cloth detection task for img_id={img_id}")
    with Session(engine) as session:
        try:
            with session.begin():
                img_metadata = session.get(ImageFile, img_id)
                if not img_metadata:
                    raise ValueError(f"No image metadata found for id={img_id}")

                logger.info("Calling ML service for cloth detection")
                ml_service_res = send_s3_img_to_service(
                    img_filename=img_metadata.filename,
                    bucket_name=settings.S3_PRODUCT_BUCKET_NAME,
                    service_url=f"{settings.ML_SERVICE_URL}/inference/image/crop_clothes",
                )
                cloth_imgs_encoded: List[str] = parse_json_response(
                    response=ml_service_res, expected_type=List[str]
                )
                if not cloth_imgs_encoded:
                    raise ValueError("No cloths found")

                logger.info(
                    f"Processing {len(cloth_imgs_encoded)} detected cloth crops"
                )
                for idx, img_encoded in enumerate(cloth_imgs_encoded):
                    cloth_img_file = BytesIO(base64.b64decode(img_encoded))
                    cloth_img = create_and_verify_pil_img(
                        img_bytes=cloth_img_file, logger=logger
                    )
                    img_filename = build_image_filename(
                        img=cloth_img, idx=idx, prefix="cloth"
                    )
                    s3_path = storage.upload_file_to_s3(
                        file_obj=cloth_img_file,
                        bucket_name=settings.S3_PRODUCT_BUCKET_NAME,
                        object_name=img_filename,
                    )

                    cloth_crop_metadata = ImageFile(
                        path=s3_path,
                        filename=img_filename,
                        width=cloth_img.width,
                        height=cloth_img.height,
                        format=cloth_img.format,
                        original_id=img_metadata.id,  # link back to original
                    )
                    # Append to parent image's crops relationship
                    img_metadata.crops.append(cloth_crop_metadata)

                session.add(img_metadata)
                logger.info(
                    f"Successfully added {len(cloth_imgs_encoded)} crops for image {img_id}"
                )
                return [crop.id for crop in img_metadata.crops]

        # later we will use a retry logic here
        except IntegrityError as e:
            logger.error(f"IntegrityError in cloth detection task occurred: {e}")
            raise
        except ValidationError as e:
            logger.error(f"ValidationError in cloth detection task occurred: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}", exc_info=True)
            raise


class LabelImgResult(BaseModel):
    img_id: UUID
    label: StructuredLabel
    img_vector: List[float]  # adjust type as needed


@celery_app.task(name="task.label_img_task", bind=True)
def label_img_task(self, img_id: UUID) -> LabelImgResult:
    logger.info(f"Starting labeling task for img_id={img_id}")
    with Session(engine) as session:
        try:
            with session.begin():
                img_metadata = session.get(ImageFile, img_id)
                if not img_metadata:
                    raise ValueError(f"No image metadata found for id={img_id}")

                logger.info("Calling ML service for image labeling")
                res = send_s3_img_to_service(
                    img_filename=img_metadata.filename,
                    bucket_name=settings.S3_PRODUCT_BUCKET_NAME,
                    service_url=f"{settings.ML_SERVICE_URL}/inference/image/label",
                )

                labelling_res = LabelingResponse.model_validate(res.json())
                img_metadata.label = labelling_res.label_data
                session.add(img_metadata)

                logger.info(f"Successfully labeled image {img_id}")
                return LabelImgResult(
                    img_id=img_metadata.id,
                    label=img_metadata.label,
                    img_vector=labelling_res.storage_vector,
                )

        except IntegrityError as e:
            logger.error(f"IntegrityError in label_img_task: {e}", exc_info=True)
            raise
        except ValidationError as e:
            logger.error(f"ValidationError in label_img_task: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in label_img_task: {e}", exc_info=True)
            raise


class BestMatchingRequest(BaseModel):
    candidates: List[str]
    target: str


class BestMatchingResponse(BaseModel):
    index: int
    best_match: str  # the label with the highest match
    score: float  # similarity score (0.0 - 1.0)


@celery_app.task(name="task.select_img_for_product_task", bind=True)
def select_img_for_product_task(
    self, img_labels: List[LabelImgResult], product_id: UUID
) -> LabelImgResult:
    logger.info(f"Starting select_img_for_product_task for product_id={product_id}")
    with Session(engine) as session:
        try:
            with session.begin():
                product = session.get(Product, product_id)
                if not product:
                    raise ValueError(f"No product found for id={product_id}")

                labels = [img.label.to_text() for img in img_labels]
                logger.info(
                    f"[select_img_for_product_task] Comparing {len(labels)} image labels against product '{product.name}'"
                )

                payload = BestMatchingRequest(
                    candidates=labels, target=product.name
                ).model_dump()
                endpoint = f"{settings.ML_SERVICE_URL}/inference/text/matching"

                best_match_res = safe_post_and_parse(
                    url=endpoint,
                    payload=payload,
                    model=BestMatchingResponse,
                    logger=logger,
                )
                # hardcoded, prefer: settings.MATCH_SCORE_THRESHOLD
                if best_match_res.score < 0.7:
                    raise ValueError(
                        "No substantial product match found in image labels"
                    )
                matched_img_label = img_labels[best_match_res.index]

                new_image_product = ProductImage(
                    product_id=product_id,
                    image_id=matched_img_label.img_id,
                    is_primary_crop=True,
                )
                session.add(new_image_product)
                
                logger.info(
                    f"[select_img_for_product_task] Linked image {matched_img_label.img_id} as primary crop for product {product_id}"
                )

                return matched_img_label

        except IntegrityError as e:
            logger.error(
                f"IntegrityError in select_img_for_product_task for product_id={product_id}: {e}",
                exc_info=True,
            )
            raise
        except ValidationError as e:
            logger.error(
                f"ValidationError in select_img_for_product_task for product_id={product_id}: {e}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in select_img_for_product_task for product_id={product_id}: {e}",
                exc_info=True,
            )
            raise


# we may have data consistency here, because if this task fail, the whole pipeline is not idempotent.
@celery_app.task(name="task.save_image_in_vector_db_task", bind=True)
def save_image_in_vector_db_task(
    self, selected_result: LabelImgResult, collection_name: str
) -> UUID:

    try:
        chroma_client = chroma_client_wrapper.get_client()
        img_collection = chroma_client.get_or_create_collection(collection_name)

        # Ensure idempotency: check if ID already exists (if Chroma API supports it)
        if img_collection.get(ids=[str(selected_result.img_id)]).get("ids"):
            logger.info(
                f"Image {selected_result.img_id} already exists in collection {collection_name}. skipping"
            )
            return selected_result.img_id

        img_collection.add(
            ids=[str(selected_result.img_id)],
            embeddings=[selected_result.img_vector],
            metadatas=[selected_result.label.model_dump()],
        )

        logger.info(
            f"Successfully saved image {selected_result.img_id} to collection '{collection_name}'"
        )
        return selected_result.img_id

    except ValueError as e:
        logger.error(
            f"Value error while saving image {selected_result.img_id} to collection '{collection_name}': {e}"
        )
        raise
    except ConnectionError as e:
        logger.warning(
            f"Connection error while saving image {selected_result.img_id}, retrying...: {e}"
        )
        # retrying logic will be here
        raise self.retry(exc=e)
    except Exception as e:
        logger.exception(
            f"Unexpected error saving image {selected_result.img_id} to collection '{collection_name}'"
        )
        raise


@celery_app.task(name="task.finalize_orchestrator_task", bind=True)
def finalize_orchestrator_task(
    self,
    selected_img_id: UUID,
    created_crops: list[UUID],
    job_id: UUID,
    model_version: str,
) -> UUID:
    logger.info("")

    with Session(engine) as session:
        try:
            with session.begin():
                job = session.get(Job, job_id)
                if not job:
                    raise ValueError("No Job founded")

                if job.type == JobType.INDEXING:
                    idx_result = IndexingResult(
                        job_id=job.id,
                        selected_crop_id=selected_img_id,
                        created_crop_ids=created_crops,
                        model_version=model_version,
                    )
                    session.add(idx_result)
                    return idx_result.id
                else:
                    return uuid.uuid4()

        except Exception as e:
            raise


@celery_app.task(name="task.update_job_status_task", bind=True)
def update_job_status_task(
    self, job_id: UUID, status: JobStatus, message: str | None = None
):
    # *only* this task knows about the Job model
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            raise ValueError("No job founded for this id:")

        job.status = status
        job.processing_details = message
        session.add(job)
        session.commit()


# later we will test this aprouch after we tested the prototype, then we can refactor using this function
def build_dynamic_chord(
    entry_task: Signature, fanout_task: Signature, body_chain: Signature
) -> Signature:
    """
    Builds a dynamic pipeline:
    1. Runs entry_task → produces a list of items.
    2. Fans out each item using fanout_task.
    3. Aggregates the results and runs the body_chain.

    Args:
        entry_task: Task that produces a list of items for the fan-out.
        fanout_task: Task to run in parallel for each item.
        body_chain: Chain of tasks to run after fan-out results are collected.
    """

    @celery_app.task(bind=True)
    def _start_dynamic_chord(self, items):
        header = [fanout_task.clone(args=[item]) for item in items]
        return chord(header)(body_chain)

    return chain(entry_task, _start_dynamic_chord.s())


@celery_app.task(name="task.start_labeling_chord", bind=True)
def start_labeling_chord(self, crop_ids, product_id, job_id):
    header = [label_img_task.s(c) for c in crop_ids]
    body = chain(
        select_img_for_product_task.s(product_id),
        save_image_in_vector_db_task.s(settings.CHROMA_PRODUCT_IMAGE_COLLECTION),
        finalize_orchestrator_task.s(job_id, settings.MODEL_VERSION),
    )
    return chord(header)(body)


# for now only set the state of the job from started completed and failed, later we will wrap aroud the steps of the worker
@celery_app.task(name="task.indexing_orchestratro_task", bind=True)
def indexing_orchestrator_task(self, job_id: UUID) -> UUID:
    logger.info("Starting the indexing pipeline")
    with Session(engine) as session:
        try:
            with session.begin():
                # do some idempotency here, like checks if the job alread exist with a given img_id, just jump the creation

                job = session.get(Job, job_id)
                if not job:
                    raise ValueError("No Job founded for this job id")
                if job.type != JobType.INDEXING:
                    raise ValueError("Wrong job type for indexing")
                if not job.input_product_id:
                    raise ValueError(
                        "No product_id founded for this job. its necessary for indexing job"
                    )

                img_id = job.input_img_id
                product_id = job.input_product_id

                update_job_status_task.delay(
                    job_id, JobStatus.STARTED, "Job is indexing Product Image"
                )

                workflow = chain(
                    cloth_detection_task.s(img_id),
                    start_labeling_chord.s(product_id, job_id),
                )
                workflow.apply_async(
                    link_error=update_job_status_task.s(
                        job_id, JobStatus.FAILED, "Job Failed in indexing Product Image"
                    )
                )
                return job_id

        except Exception as e:
            raise
