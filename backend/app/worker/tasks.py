from io import BytesIO
from typing import List
from uuid import UUID
import uuid
from celery import chain, chord, group
from psycopg2 import IntegrityError
from sqlmodel import Session, select
from models.job import Job, JobStatus, JobType
from models.product import Product, ProductImage
from models.result import (
    IndexingResult,
    QueryResult,
    QueryResultCloth,
    QueryResultProductImage,
)
from celery_app import app as celery_app
from core import storage
from models.image import BucketName, ImageFile, BUCKET_NAME_TO_S3
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
import base64
import logging
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

logger = logging.getLogger(__name__)


def procces_image(
    img_stream: BytesIO, session: Session, img_type: str, bucket_name: BucketName
) -> ImageFile:

    pil_img = create_and_verify_pil_img(img_stream)
    new_img_id = uuid.uuid4()
    img_filename = build_image_filename(img=pil_img, id=new_img_id, prefix=img_type)

    real_bucket = BUCKET_NAME_TO_S3[bucket_name]
    s3_path = storage.upload_file_to_s3(
        file_obj=img_stream,
        bucket_name=real_bucket,
        object_name=img_filename,
    )
    return ImageFile(
        id=new_img_id,
        bucket=bucket_name,
        filename=img_filename,
        width=pil_img.width,
        height=pil_img.height,
        format=pil_img.format,
        path=s3_path,
    )


# celery tasks
# needs retry logic
# needs to use 2 buckets names, one for product images, one for query images
# logs are not showing up in the celery worker
# we may see conflicts bugs in the future because of filename generator, with only cloth_[N].png we may create varius images filenames with the same name/value
# job is not being proper saved its state
@celery_app.task(name="task.cloth_detection_task", bind=True)
def cloth_detection_task(self, img_id: UUID, bucket_name: str) -> list[UUID]:
    logger.info(f"Starting cloth detection task for img_id={img_id}")
    try:
        bucket = BucketName(bucket_name)  # matches by enum value
    except ValueError as e:
        raise ValueError(f"invalid bucket {bucket_name}") from e

    with Session(engine) as session:
        try:
            with session.begin():
                img_metadata = session.get(ImageFile, img_id)
                if not img_metadata:
                    raise ValueError(f"No image metadata found for id={img_id}")

                # Idempotency guard
                if img_metadata.crops:
                    logger.info(
                        f"Crops already exist for img_id={img_id}, skipping detection."
                    )
                    return [crop.id for crop in img_metadata.crops]

                logger.info("Calling ML service for cloth detection")
                real_bucket = BUCKET_NAME_TO_S3[bucket]
                ml_service_res = send_s3_img_to_service(
                    img_filename=img_metadata.filename,
                    bucket_name=real_bucket,
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
                    cloth_crop_metadata = procces_image(
                        img_stream=cloth_img_file,
                        session=session,
                        img_type="png",
                        bucket_name=bucket,
                    )
                    # Append to parent image's crops relationship
                    # this is not idepotent, as another run for the same image id will append the new crops with the old crops
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
    label: dict
    img_vector: List[float]  # adjust type as needed
    # Make the model JSON serializable
    model_config = ConfigDict(
        json_encoders={uuid.UUID: str},
        str_strip_whitespace=True,
    )

    # Handle UUID string conversion
    @field_validator("img_id", mode="before")
    def parse_uuid(cls, v):
        if isinstance(v, str):
            return uuid.UUID(v)
        return v

    def get_structured_label(self) -> StructuredLabel:
        """Convert label dict back to StructuredLabel"""
        return StructuredLabel(**self.label)


@celery_app.task(name="task.label_img_task", bind=True)
def label_img_task(self, img_id: UUID, bucket_name: str) -> dict:
    logger.info(f"Starting labeling task for img_id={img_id}")
    try:
        bucket = BucketName(bucket_name)  # matches by enum value
    except ValueError as e:
        raise ValueError(f"invalid bucket {bucket_name}") from e

    with Session(engine) as session:
        try:
            with session.begin():
                img_metadata = session.get(ImageFile, img_id)
                if not img_metadata:
                    raise ValueError(f"No image metadata found for id={img_id}")

                logger.info("Calling ML service for image labeling")
                real_bucket = BUCKET_NAME_TO_S3[bucket]
                res = send_s3_img_to_service(
                    img_filename=img_metadata.filename,
                    bucket_name=real_bucket,
                    service_url=f"{settings.ML_SERVICE_URL}/inference/image/label",
                )

                labelling_res = LabelingResponse.model_validate(res.json())

                img_metadata.label = labelling_res.label_data.model_dump()
                session.add(img_metadata)

                logger.info(f"Successfully labeled image {img_id}")
                result = LabelImgResult(
                    img_id=img_metadata.id,
                    label=labelling_res.label_data.model_dump(),
                    img_vector=labelling_res.storage_vector,
                )
                return result.model_dump()
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
    text: str  # the label with the highest match
    score: float  # similarity score (0.0 - 1.0)


# needs to rollback and delete all the data from the images of best match res score is below the necessary
@celery_app.task(name="task.select_img_for_product_task", bind=True)
def select_img_for_product_task(
    self, img_labels_data: List[dict], product_id: UUID
) -> dict:
    logger.info(f"Starting select_img_for_product_task for product_id={product_id}")
    with Session(engine) as session:
        try:
            with session.begin():
                product = session.get(Product, product_id)
                if not product:
                    raise ValueError(f"No product found for id={product_id}")

                img_labels = [
                    LabelImgResult.model_validate(data) for data in img_labels_data
                ]

                labels = [img.get_structured_label().to_text() for img in img_labels]
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
                        f"No substantial product match found in image labels, best_match:{best_match_res.model_dump()} target:{product.name}"
                    )
                matched_img_label = img_labels[best_match_res.index]

                # idempotency check, if already selected the same product image, skip
                existing = session.exec(
                    select(ProductImage).where(
                        ProductImage.product_id == product_id,
                        ProductImage.image_id == matched_img_label.img_id,
                    )
                ).first()
                if not existing:

                    new_image_product = ProductImage(
                        product_id=product_id,
                        image_id=matched_img_label.img_id,
                        is_primary_crop=True,
                    )
                    session.add(new_image_product)
                    logger.info(
                        f"[select_img_for_product_task] Linked image {matched_img_label.img_id} as primary crop for product {product_id}"
                    )
                else:
                    logger.info(
                        f"ProductImage ({product_id}, {matched_img_label.img_id}) already exists, skipping"
                    )

                return matched_img_label.model_dump()

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
    self, selected_result_data: dict, collection_name: str
) -> str:

    try:
        selected_result = LabelImgResult.model_validate(selected_result_data)

        chroma_client = chroma_client_wrapper.get_client()
        img_collection = chroma_client.get_or_create_collection(collection_name)

        # Ensure idempotency: check if ID already exists (if Chroma API supports it)
        if img_collection.get(ids=[str(selected_result.img_id)]).get("ids"):
            logger.info(
                f"Image {selected_result.img_id} already exists in collection {collection_name}. skipping"
            )
            return str(selected_result.img_id)

        img_collection.add(
            ids=[str(selected_result.img_id)],
            embeddings=[selected_result.img_vector],
            metadatas=[selected_result.label],
        )

        logger.info(
            f"Successfully saved image {selected_result.img_id} to collection '{collection_name}'"
        )
        return str(selected_result.img_id)

    except ValueError as e:
        logger.error(
            f"Value error while saving image {selected_result_data} to collection '{collection_name}': {e}"
        )
        raise
    except ConnectionError as e:
        logger.warning(
            f"Connection error while saving image {selected_result_data}, retrying...: {e}"
        )
        # retrying logic will be here
        raise self.retry(exc=e)
    except Exception as e:
        logger.exception(
            f"Unexpected error saving image {selected_result_data} to collection '{collection_name}' {e}"
        )
        raise


@celery_app.task(name="task.query_image_in_vector_db_task", bind=True)
def query_image_in_vector_db_task(
    self, label_img_result_data: dict, query_result_id: UUID, collection_name: str
) -> UUID:
    # if did not find a closer score, return a empty list of products images:
    logger.info("querying cloth item...")
    label_img_result = LabelImgResult.model_validate(label_img_result_data)

    chroma_client = chroma_client_wrapper.get_client()
    img_collection = chroma_client.get_or_create_collection(collection_name)

    with Session(engine) as session:
        try:
            with session.begin():
                result = img_collection.query(
                    query_embeddings=[label_img_result.img_vector], n_results=3
                )
                ids = result["ids"][0]
                if not result["distances"]:
                    raise ValueError(
                        "No distances founded in the query result for similar images"
                    )
                # here we can guard later fo only get a valid result based in a minimal score
                distances = result["distances"][0]

                cloth = QueryResultCloth(
                    query_result_id=query_result_id, crop_img_id=label_img_result.img_id
                )
                session.add(cloth)

                for idx, id_str in enumerate(ids):
                    product_image = QueryResultProductImage(
                        cloth_id=cloth.id,
                        matched_image_id=UUID(id_str),
                        score=1 - distances[idx],
                        rank=idx + 1,
                    )
                    session.add(product_image)

                return cloth.id

        except Exception as e:
            raise


@celery_app.task(name="task.finalize_orchestrator_task", bind=True)
def finalize_indexing_task(
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

                idx_result = IndexingResult(
                    job_id=job.id,
                    selected_crop_id=selected_img_id,
                    created_crop_ids=[str(c) for c in created_crops],
                    model_version=model_version,
                )
                session.add(idx_result)

                return idx_result.id

        except Exception as e:
            raise


@celery_app.task(name="task.update_job_status_task", bind=True)
def update_job_status_task(
    self, job_id: UUID, status: JobStatus, message: str | None = None
):
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            raise ValueError("No job founded for this id:")

        job.status = status
        job.processing_details = message
        session.add(job)
        session.commit()


@celery_app.task(name="task.start_indexing_chord", bind=True)
def start_indexing_chord(self, crop_ids: List[UUID], product_id: UUID, job_id: UUID):
    header = [
        label_img_task.s(c, BucketName.PRODUCT).set(
            link_error=update_job_status_task.s(
                job_id, JobStatus.FAILED, "Job Failed in indexing Product Image"
            )
        )
        for c in crop_ids
    ]
    body = chain(
        select_img_for_product_task.s(product_id),
        save_image_in_vector_db_task.s(settings.CHROMA_PRODUCT_IMAGE_COLLECTION),
        finalize_indexing_task.s(
            created_crops=crop_ids,
            job_id=job_id,
            model_version=settings.MODEL_VERSION,
        ),
        update_job_status_task.si(
            job_id, JobStatus.COMPLETED, "Indexing Completed"
        ).set(
            link_error=update_job_status_task.s(
                job_id, JobStatus.FAILED, "Job Failed in indexing Product Image"
            )
        ),
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
                    cloth_detection_task.s(img_id, BucketName.PRODUCT),
                    start_indexing_chord.s(product_id, job_id),
                )
                workflow.apply_async(
                    link_error=update_job_status_task.si(
                        job_id, JobStatus.FAILED, "Job Failed in indexing Product Image"
                    )
                )
                return job_id

        except Exception as e:
            raise


@celery_app.task(name="task.start_querying_pipeline_task", bind=True)
def start_querying_pipeline_task(
    self,
    crop_ids: list[UUID],
    job_id: UUID,
    query_result_id: UUID,
    collection_name: str,
):
    header = [
        chain(
            label_img_task.s(c, BucketName.QUERY),
            query_image_in_vector_db_task.s(
                query_result_id=query_result_id, collection_name=collection_name
            ),
        ).set(
            link_error=update_job_status_task.s(
                job_id, JobStatus.FAILED, "Job Failed in querying pipeline"
            )
        )
        for c in crop_ids
    ]
    body = update_job_status_task.si(job_id, JobStatus.COMPLETED, "Query Completed")

    return chord(header)(body)


# For consistency, also update the indexing orchestrator to follow the same pattern
@celery_app.task(name="task.querying_orchestrator_task", bind=True)
def querying_orchestrator_task(self, job_id: UUID) -> UUID:
    logger.info("starting querying taks")

    with Session(engine) as session:
        try:
            with session.begin():
                job = session.get(Job, job_id)
                if not job:
                    raise ValueError("No job founded for this id")
                img_id = job.input_img_id

                new_query = QueryResult(
                    job_id=job_id, model_version=settings.MODEL_VERSION
                )
                session.add(new_query)

                update_job_status_task.delay(
                    job_id=job_id,
                    status=JobStatus.STARTED,
                    message="Starting to query...",
                )

                workflow = chain(
                    cloth_detection_task.s(img_id, BucketName.QUERY),
                    start_querying_pipeline_task.s(
                        job_id=job_id,
                        query_result_id=new_query.id,
                        collection_name=settings.CHROMA_PRODUCT_IMAGE_COLLECTION,
                    ),
                )
                workflow.apply_async(
                    link_error=update_job_status_task.si(  # fix: changed for si, to not blow up when a error happens
                        job_id, JobStatus.FAILED, "Job Failed in indexing Product Image"
                    )
                )
                return job_id

        except Exception as e:
            raise
