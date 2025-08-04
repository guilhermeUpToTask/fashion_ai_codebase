#refactor here.

from io import BytesIO
from PIL import Image
from typing import Annotated
from fastapi import APIRouter, File, HTTPException, Header, UploadFile
import uuid
from models.job import Job, JobStatus, JobType
from models.product import Product, ProductImage
from worker.tasks import indexing_orchestrator_task

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

async def procces_image(img_file: UploadFile, session:SessionDep) -> ImageFile:
        chunk_size = 1024 * 1024
        img_stream = await read_and_validate_file(img_file=img_file, chunk_size=chunk_size, max_size=settings.MAX_IMAGE_SIZE_BYTES)
        img = await safe_create_pil_img(img_stream)
        img_format = get_extesion_type_for_img(img)
        width, height = img.size
        img_filename = f"originals/{uuid.uuid4().hex}.{img_format}"
        s3_path = storage.upload_file_to_s3(
            file_obj=img_stream,
            bucket_name=settings.S3_PRODUCT_BUCKET_NAME,
            object_name=img_filename,
        )
        img_metadata = ImageFile(filename=img_filename, width=width, height=height, format=img_format, path=s3_path)
        return img_metadata



#the index and the query image uses quite similar processing, later we will refactor both to consume helper functions for processing image in atomic way.
@router.post("/{product_id}/upload")
async def upload_image_for_product(
    session: SessionDep,
    content_length: Annotated[int, Header()],
    image_file: Annotated[UploadFile, File(description="Product image to be indexed")],
    product_id: uuid.UUID
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
        
        img_product_link = ProductImage(image_id=img_metadata.id, product_id=product_id)
        session.add(img_product_link)
        session.commit()
        
        return img_metadata.id
        
    except Exception as e:
        # Log the error later
        raise HTTPException(
            status_code=500, detail=f"Failed to upload image to storage: {e}"
        )

@router.post('/{product_id}/{img_id}/index', status_code=202)
async def index_product_image(product_id:uuid.UUID, img_id:uuid.UUID, session:SessionDep) -> uuid.UUID:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="No product founded for giving id")
    img_metadata = session.get(ImageFile, img_id)
    if not img_metadata:
        raise HTTPException(status_code=404, detail="No Image founded for giving id")   
    new_job = Job(input_img_id=img_id, input_product_id=product_id, type=JobType.INDEXING, status=JobStatus.QUEUED)
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
        new_job= Job(input_img_id=img_metadata.id, type=JobType.QUERY, status=JobStatus.QUEUED)
        session.commit()
        #query_orchestrator_task.apply_async(job_id=new_job.id)
        return new_job.id
        
    except HTTPException as e:
        raise e  # Re-raise vallidation exceptions
    except Exception as e:
        raise e




@router.get("/job/status/{job_id}")
async def get_job_status(job_id: uuid.UUID, session: SessionDep) -> JobStatus:
    job = session.get(Job,job_id)
    if not job:
        raise HTTPException(status_code=404, detail="No job founded for this id")
    return job.status

