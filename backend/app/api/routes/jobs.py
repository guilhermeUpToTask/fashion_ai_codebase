# routes/jobs.py - Dedicated job management
from io import BytesIO
import logging
from fastapi import (
    APIRouter,
    HTTPException,
    Header,
    Path,
    Query,
    UploadFile,
    File,
    status,
)
from typing import Annotated, List, Optional
import uuid
from PIL import Image
from sqlmodel import select
from api.deps import SessionDep
from core.config import settings
from core import storage
from models.image import BucketName, ImageFile, BUCKET_NAME_TO_S3
from models.job import Job, JobStatus, JobResponse, JobType
from models.product import Product, ProductImage
from models.result import IndexingResult, QueryResult
from utils.image_helpers import build_image_filename, create_and_verify_pil_img

from utils.helpers import read_and_validate_file
from worker.tasks import indexing_orchestrator_task, querying_orchestrator_task

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Logger
logger = logging.getLogger(__name__)

# ---Constants--- Later all constants will be feeded from env vars
MAX_RESOLUTION = 4096
ALLOWED_TYPES = {"image/jpeg", "image/png"}


# Helpers
async def procces_image(
    img_file: UploadFile, session: SessionDep, img_type: str, bucket_name: BucketName
) -> ImageFile:
    chunk_size = 1024 * 1024

    img_stream = await read_and_validate_file(
        file=img_file, chunk_size=chunk_size, max_size=settings.MAX_IMAGE_SIZE_BYTES
    )
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
        filename=img_filename,
        bucket=bucket_name,
        width=pil_img.width,
        height=pil_img.height,
        format=pil_img.format,
        path=s3_path,
    )


async def generate_query_result(session: SessionDep, job_id: uuid.UUID) -> dict:

    query_result = session.exec(
        select(QueryResult).where(QueryResult.job_id == job_id)
    ).first()
    if not query_result:
        raise ValueError("No query result founded for this job id")

    cloths_data = []
    for cloth in query_result.cloths:
        similar_products_imgs = cloth.similar_products

        cloth_matches = []

        for similar_img in similar_products_imgs:
            # Join with ProductImage and Product for full details
            product_image = session.exec(
                select(ProductImage).where(
                    ProductImage.image_id == similar_img.matched_image_id
                )
            ).first()

            match_data = {
                "image_id": str(similar_img.matched_image_id),
                "score": similar_img.score,
                "rank": similar_img.rank,
            }

            if product_image and product_image.product:
                match_data.update(
                    {
                        "product_id": str(product_image.product_id),
                        "product_name": product_image.product.name,
                        "product_description": product_image.product.description,
                        # Add image URL if you have it
                    }
                )

            cloth_matches.append(match_data)

        cloth_data = {
            "cloth_id": str(cloth.id),
            "crop_img_id": str(cloth.crop_img_id),
            "matched_images": cloth_matches,
        }
        cloths_data.append(cloth_data)

    return {
        "type": "querying",
        "model_version": query_result.model_version,
        "cloths": cloths_data,
    }


async def generate_indexing_result(session: SessionDep, job_id: uuid.UUID) -> dict:
    indexing_result = session.exec(
        select(IndexingResult).where(IndexingResult.job_id == job_id)
    ).first()
    if not indexing_result:
        raise ValueError("No Indexing result founded for this job_id")

    return {
        "type": "indexing",
        "selected_crop_id": str(indexing_result.selected_crop_id),
        "total_crops_created": len(indexing_result.created_crop_ids),
        "model_version": indexing_result.model_version,
    }


# Endpoits
# TODO: create a a list of images to be indexed
@router.post(
    "/indexing",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        413: {"description": "File too large"},
        415: {"description": "Unsupported media type"},
        404: {"description": "Product not found"},
        500: {"description": "Internal server error"},
    },
)
async def create_indexing_job(
    session: SessionDep,
    content_length: Annotated[
        int, Header(description="Content-Length of the uploaded file")
    ],
    image_file: Annotated[UploadFile, File(description="Product image to be indexed")],
    product_id: Annotated[uuid.UUID, Query(description="ID of the product to index")],
) -> JobResponse:
    """
    Create a new indexing job. Handles image upload, validates and starts processing.
    """

    if image_file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Invalid file type. Allowed types are: {', '.join(ALLOWED_TYPES)}",
        )
    if content_length > settings.MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_IMAGE_SIZE_BYTES // 1024 // 1024}MB.",
        )

    try:
        with session.begin():
            product = session.get(Product, product_id)
            if not product:
                raise HTTPException(
                    status_code=404, detail="No product found for given id"
                )

            img_metadata = await procces_image(
                img_file=image_file,
                session=session,
                img_type="product",
                bucket_name=BucketName.PRODUCT,
            )
            session.add(img_metadata)
            session.flush()

            img_product_link = ProductImage(
                image_id=img_metadata.id, product_id=product_id
            )
            session.add(img_product_link)
            session.flush()

            job = Job(
                type=JobType.INDEXING,
                status=JobStatus.QUEUED,
                input_img_id=img_metadata.id,
                input_product_id=product.id,
                processing_details="Job queued for processing",
            )
            session.add(job)
            session.flush()

            indexing_orchestrator_task.delay(job.id)

            # we can refactor later to spread the job args and join the bools
            return JobResponse(
                job_id=job.id,
                status=job.status,
                job_type=job.type,
                message=job.processing_details,
                created_at=job.created_at,
                is_completed=False,
                is_failed=False,
                is_processing=False,  # still queued
            )
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating indexing job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create indexing job")


@router.post(
    "/querying",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        413: {"description": "File too large"},
        415: {"description": "Unsupported media type"},
        500: {"description": "Internal server error"},
    },
)
async def create_querying_job(
    session: SessionDep,
    content_length: Annotated[
        int, Header(description="Content-Length of the uploaded file")
    ],
    image_file: Annotated[UploadFile, File(description="Product image to be queried")],
) -> JobResponse:
    """
    Create a new querying job. Handles image upload, validates and starts processing.
    """

    # this can be refactored later by a injected dependency
    if image_file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Invalid file type. Allowed types are: {', '.join(ALLOWED_TYPES)}",
        )
    if content_length > settings.MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_IMAGE_SIZE_BYTES // 1024 // 1024}MB.",
        )

    try:
        with session.begin():
            img_metadata = await procces_image(
                img_file=image_file,
                session=session,
                img_type="query",
                bucket_name=BucketName.QUERY,
            )
            session.add(img_metadata)
            session.flush()

            job = Job(
                type=JobType.QUERYING,
                status=JobStatus.QUEUED,
                input_img_id=img_metadata.id,
                processing_details="Job queued for processing",
            )
            session.add(job)
            session.flush()

            querying_orchestrator_task.delay(job.id)

            return JobResponse(
                job_id=job.id,
                status=job.status,
                job_type=job.type,
                message=job.processing_details,
                created_at=job.created_at,
                is_completed=False,
                is_failed=False,
                is_processing=False,
            )
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating query job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create query job")


@router.get(
    "/{job_id}/status",
    response_model=JobResponse,
    responses={
        404: {"description": "Job not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_job_status(
    job_id: Annotated[uuid.UUID, Path(description="ID of the job")],
    session: SessionDep,
) -> JobResponse:
    """
    Get job status with optional results - optimized for frontend polling.
    """
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No job found for this id"
        )

    response = JobResponse(
        job_id=job.id,
        status=job.status,
        job_type=job.type,
        message=job.processing_details,
        created_at=job.created_at,
        updated_at=job.updated_at,
        is_completed=job.status == JobStatus.COMPLETED,
        is_failed=job.status == JobStatus.FAILED,
        is_processing=job.status in [JobStatus.QUEUED, JobStatus.STARTED],
    )

    if job.status in [JobStatus.STARTED, JobStatus.FAILED]:
        return response

    if job.status == JobStatus.COMPLETED:
        if job.type == JobType.QUERYING:
            response.result = await generate_query_result(
                session=session, job_id=job_id
            )
        elif job.type == JobType.INDEXING:
            response.result = await generate_indexing_result(
                session=session, job_id=job_id
            )

    return response


@router.get(
    "/",
    response_model=List[Job],
    responses={500: {"description": "Internal server error"}},
)
async def list_jobs(
    session: SessionDep,
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    job_type: Optional[JobType] = Query(None, description="Filter by job type"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
) -> List[Job]:
    """
    List jobs with optional filtering.
    """
    query = select(Job)
    if status:
        query = query.where(Job.status == status)
    if job_type:
        query = query.where(Job.type == job_type)

    results = session.exec(query.limit(limit).offset(offset)).all()

    return list(results)


@router.delete("/{job_id}")
async def cancel_job(job_id: uuid.UUID, session: SessionDep):
    """Cancel a running job"""
    pass


@router.post("/{job_id}/retry")
async def retry_failed_job(job_id: uuid.UUID, session: SessionDep):
    """Retry a failed job"""
    pass
