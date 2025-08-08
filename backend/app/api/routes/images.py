# refactor here.

from datetime import datetime
from io import BytesIO
from PIL import Image
from typing import Annotated, List, Optional
from fastapi import APIRouter, File, HTTPException, Header, UploadFile
import uuid

from pydantic import BaseModel
from sqlmodel import func, select
from models.result import (
    IndexingResult,
    QueryResult,
    QueryResultCloth,
    QueryResultProductImage,
)
from models.job import Job, JobStatus, JobType
from models.product import Product, ProductImage
from worker.tasks import indexing_orchestrator_task, querying_orchestrator_task

# --- Core Application Imports ---
from api.deps import CurrentUser, SessionDep
from core.config import settings
from core import storage

# --- Model & Workflow Imports ---
from models.image import ImageFile, ImagePublic

# ---Constants---
MAX_RESOLUTION = 4096
ALLOWED_TYPES = {"image/jpeg", "image/png"}

router = APIRouter(prefix="/images", tags=["images"])


# Helpers
async def read_and_validate_file(
    img_file: UploadFile, chunk_size: int, max_size: int
) -> BytesIO:
    img_stream = BytesIO()
    size = 0

    while chunk := await img_file.read(chunk_size):
        size += len(chunk)
        if size > max_size:
            raise ValueError(
                f"File is too large. Maximum size is {max_size // 1024 // 1024}MB."
            )
        img_stream.write(chunk)

    if not img_stream.getbuffer().nbytes:
        raise ValueError(f"Empty file uploaded")

    img_stream.seek(0)
    return img_stream


async def safe_create_pil_img(img_file: BytesIO) -> Image.Image:
    img_file.seek(0)
    img = Image.open(img_file)
    img.verify()
    img_file.seek(0)
    img = Image.open(img_file)
    return img


def get_extesion_type_for_img(img: Image.Image) -> str:
    image_format = img.format
    if not image_format:
        raise ValueError("Could not determine image format.")
    file_extension = image_format.lower()
    if file_extension == "jpeg":
        file_extension = "jpg"
    return file_extension


async def procces_image(img_file: UploadFile, session: SessionDep) -> ImageFile:
    chunk_size = 1024 * 1024
    img_stream = await read_and_validate_file(
        img_file=img_file, chunk_size=chunk_size, max_size=settings.MAX_IMAGE_SIZE_BYTES
    )
    img = await safe_create_pil_img(img_stream)
    img_format = get_extesion_type_for_img(img)
    width, height = img.size
    img_filename = f"originals/{uuid.uuid4().hex}.{img_format}"
    s3_path = storage.upload_file_to_s3(
        file_obj=img_stream,
        bucket_name=settings.S3_PRODUCT_BUCKET_NAME,
        object_name=img_filename,
    )
    img_metadata = ImageFile(
        filename=img_filename,
        width=width,
        height=height,
        format=img_format,
        path=s3_path,
    )
    return img_metadata


# the index and the query image uses quite similar processing, later we will refactor both to consume helper functions for processing image in atomic way.
# to many request to get the end result, later lets refactor both the upload image for product and indexing image in the same endpoint, or maybe we can register a product with images aswell, and then a endpoint for indexing all images from a product


@router.post("/{product_id}/upload")
async def upload_image_for_product(
    session: SessionDep,
    content_length: Annotated[int, Header()],
    image_file: Annotated[UploadFile, File(description="Product image to be indexed")],
    product_id: uuid.UUID,
) -> uuid.UUID:
    """
    Accepts an image, uploads it to storage, creates a job record in the database,
    and starts the asynchronous indexing pipeline
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
        img_metadata = await procces_image(img_file=image_file, session=session)
        session.add(img_metadata)
        session.commit()
        session.refresh(img_metadata)

        # maybe needs to change here to create a more explicit relationship
        img_product_link = ProductImage(image_id=img_metadata.id, product_id=product_id)
        session.add(img_product_link)
        session.commit()

        return img_metadata.id

    except Exception as e:
        # Log the error later
        raise HTTPException(
            status_code=500, detail=f"Failed to upload image to storage: {e}"
        )


@router.post("/{product_id}/{img_id}/index", status_code=202)
async def index_product_image(
    product_id: uuid.UUID, img_id: uuid.UUID, session: SessionDep
) -> uuid.UUID:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="No product founded for giving id")
    img_metadata = session.get(ImageFile, img_id)
    if not img_metadata:
        raise HTTPException(status_code=404, detail="No Image founded for giving id")
    new_job = Job(
        input_img_id=img_id,
        input_product_id=product_id,
        type=JobType.INDEXING,
        status=JobStatus.QUEUED,
    )
    session.add(new_job)
    session.commit()

    indexing_orchestrator_task.delay(new_job.id)
    return new_job.id


@router.post("/query", status_code=202)
async def query_new_image(
    session: SessionDep,
    content_length: Annotated[int, Header()],
    image_file: Annotated[UploadFile, File(description="Product image to be indexed")],
) -> uuid.UUID:
    """
    Accepts an image, uploads it to storage, creates a job record in the database,
    and starts the asynchronous indexing pipeline
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
        img_metadata = await procces_image(img_file=image_file, session=session)
        session.add(img_metadata)

        new_job = Job(
            input_img_id=img_metadata.id, type=JobType.QUERY, status=JobStatus.QUEUED
        )
        session.add(new_job)

        session.commit()

        querying_orchestrator_task.delay(new_job.id)
        return new_job.id

    except HTTPException as e:
        raise e  # Re-raise vallidation exceptions
    except Exception as e:
        raise e


@router.get("/products/all")
async def get_all_products_images(session: SessionDep):
    statement = select(ProductImage)
    result = session.exec(statement).all()
    return list(result)


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


class JobStatusResponse(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
    job_type: JobType
    message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    progress: Optional[dict] = None  # For progress tracking
    result: Optional[dict] = None  # Only present when completed

    # Frontend-friendly fields
    is_completed: bool
    is_failed: bool
    is_processing: bool


class QueryResultSummary(BaseModel):
    """Lightweight summary for frontend display"""

    total_cloths_found: int
    total_matches: int
    best_match_score: Optional[float] = None
    cloths: List[dict]


@router.get("/job/status/{job_id}")
async def get_job_status(
    job_id: uuid.UUID,
    session: SessionDep,
) -> JobStatusResponse:
    """
    Get job status with optional results - optimized for frontend polling

    """
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="No job found for this id")

    # Base response
    response = JobStatusResponse(
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

    if job.status == JobStatus.STARTED or job.status == JobStatus.FAILED:
        return response

    if job.status == JobStatus.COMPLETED:

        if job.type == JobType.QUERY:
            response.result = await generate_query_result(
                session=session, job_id=job_id
            )
        elif job.type == JobType.INDEXING:
            response.result = await generate_indexing_result(
                session=session, job_id=job_id
            )

    return response
