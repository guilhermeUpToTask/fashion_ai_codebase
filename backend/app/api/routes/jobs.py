

# routes/jobs.py - Dedicated job management
from io import BytesIO
import logging
from fastapi import APIRouter, HTTPException, Header, UploadFile, File
from typing import Annotated, Optional
import uuid
from PIL import Image
from backend.app.api.deps import SessionDep
from backend.app.core import storage
from backend.app.core.config import settings
from backend.app.models.image import ImageFile
from backend.app.models.job import Job, JobStatus, JobResponse, JobType
from backend.app.models.product import Product, ProductImage
from backend.app.utils.image_helpers import build_image_filename, create_and_verify_pil_img
from backend.app.worker.tasks import indexing_orchestrator_task

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Logger
logger = logging.getLogger(__name__)

# ---Constants--- Later all constants will be feeded from env vars
MAX_RESOLUTION = 4096
ALLOWED_TYPES = {"image/jpeg", "image/png"}

# Helpers
async def read_and_validate_file(
    file: UploadFile, chunk_size: int, max_size: int
) -> BytesIO:
    stream = BytesIO()
    size = 0

    while chunk := await file.read(chunk_size):
        size += len(chunk)
        if size > max_size:
            raise ValueError(
                f"File is too large. Maximum size is {max_size // 1024 // 1024}MB."
            )
        stream.write(chunk)

    if not stream.getbuffer().nbytes:
        raise ValueError(f"Empty file uploaded")

    stream.seek(0)
    return stream



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
        file=img_file, chunk_size=chunk_size, max_size=settings.MAX_IMAGE_SIZE_BYTES
    )
    
    pil_img = create_and_verify_pil_img(img_stream)
    
    new_img_id = uuid.uuid4()
    
    img_filename = build_image_filename(img=pil_img, id=new_img_id, prefix="product") 
    
    s3_path = storage.upload_file_to_s3(
        file_obj=img_stream,
        bucket_name=settings.S3_PRODUCT_BUCKET_NAME,
        object_name=img_filename,
    )
    img_metadata = ImageFile(
        id=new_img_id,
        filename=img_filename,
        width=pil_img.width,
        height=pil_img.height,
        format=pil_img.format,
        path=s3_path,
    )
    # No original_id - this is an original image
    return img_metadata


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


@router.post("/indexing")
async def create_indexing_job(
    session: SessionDep,
    content_length: Annotated[int, Header()],
    image_file: Annotated[UploadFile, File(description="Product image to be indexed")],
    product_id: uuid.UUID,
) -> JobResponse:
    """
    Create a new indexing job.
    Handle image upload, create job, start orchestrator"""

    
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
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="No product founded for giving id")
        
    
    try:
        with session.begin():
            img_metadata = await procces_image(img_file=image_file,session=session)
            session.add(img_metadata)
            session.flush()
            
            img_product_link = ProductImage(image_id=img_metadata.id, product_id=product_id)
            session.add(img_product_link)
            session.flush()
            
            job = Job(
                type=JobType.INDEXING,
                status=JobStatus.QUEUED,
                input_img_id=img_metadata.id,
                processing_details="Job queued for processing"
                
            )
            session.add(job)
            session.flush()
            
            indexing_orchestrator_task.delay(job.id)
            
            #we can refactor later to spread the job args and join the bools
            return JobResponse(
                job_id=job.id,
                status=job.status,
                job_type=job.type,
                message=job.processing_details,
                created_at=job.created_at,
                is_completed=False,
                is_failed=False,
                is_processing=False #still queued
            )
            
    except Exception as e:
        logger.error(f"Error creating indexing job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create indexing job")
    
    # Handle image upload, create job, start orchestrator
    pass

@router.post("/querying")
async def create_querying_job(
    image: UploadFile = File(...),
    session: SessionDep
) -> JobResponse:
    """
    Create a new querying job.
    Handle image upload, create job, start orchestrator
    """


    pass

@router.get("/{job_id}/status")
async def get_job_status(
    job_id: uuid.UUID,
    session: SessionDep,
    include_full_results: bool = False
) -> JobResponse:
    """Get job status and results"""
    pass

@router.get("/")
async def list_jobs(
    session: SessionDep,
    status: Optional[JobStatus] = None,
    job_type: Optional[JobType] = None,
    limit: int = 50,
    offset: int = 0
) -> List[JobResponse]:
    """List jobs with optional filtering"""
    pass

@router.delete("/{job_id}")
async def cancel_job(job_id: uuid.UUID, session: SessionDep):
    """Cancel a running job"""
    pass

@router.post("/{job_id}/retry")
async def retry_failed_job(job_id: uuid.UUID, session: SessionDep):
    """Retry a failed job"""
    pass
