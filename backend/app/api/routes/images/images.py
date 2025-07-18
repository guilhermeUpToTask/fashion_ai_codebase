from io import BytesIO
import os
from PIL import Image
from typing import Annotated
from fastapi import APIRouter, File, HTTPException, Header, UploadFile
import uuid

import numpy as np
from sqlalchemy import Delete

# --- Core Application Imports ---
from api.deps import ChromaSessionDep, SessionDep
from backend.app.core.vector_db.img_vector_crud import (
    delete_img_in_collection,
    get_image_data,
    get_images_ids,
)
from core.config import settings
from core.image_crud import (
    create_image,
    get_image_by_id,
    get_image_list,
    get_image_list_by_ids,
)
from core import storage

# --- Model & Workflow Imports ---
from models.image import ImageCreate, ImageDB, ImagePublic, StatusEnum
from app.worker.pipeline import start_indexing_pipeline

# ---Constants---
MAX_FILE_SIZE = settings.MAX_IMAGE_SIZE_BYTES
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


def get_extesion_type_for_img(img: Image.Image) -> str:
    image_format = img.format
    if not image_format:
        raise ValueError("Could not determine image format.")
    file_extension = image_format.lower()
    if file_extension == "jpeg":
        file_extension = "jpg"
    return file_extension


@router.post("/index", response_model=ImagePublic, status_code=202)
async def index_new_image(
    session: SessionDep,
    content_length: Annotated[int, Header()],
    image_file: Annotated[UploadFile, File(description="Product image to be indexed")],
) -> ImagePublic:
    """
    Accepts an image, uploads it to storage, creates a job record in the database,
    and starts the asynchronous indexing pipeline
    """

    if image_file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Invalid file type. Allowed types are: {', '.join(ALLOWED_TYPES)}",
        )
    if content_length > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB.",
        )

    try:
        chunk_size = 1024 * 1024 #1MB
        img_stream = await read_and_validate_file(img_file=image_file, chunk_size=chunk_size, max_size=MAX_FILE_SIZE)

        img = Image.open(img_stream)
        img.verify()  # verify integrity

        img_stream.seek(0)
        img = Image.open(img_stream)
        img.load()

        width, height = img.size
        if width > MAX_RESOLUTION or height > MAX_RESOLUTION:
            raise HTTPException(
                status_code=413,
                detail=f"Image resolution too large. Max is {MAX_RESOLUTION}",
            )

        file_extension = get_extesion_type_for_img(img=img)
    except HTTPException as e:
        raise e  # Re-raise vallidation exceptions
    except Exception:
        #log the error here
        raise HTTPException(status_code=422, detail="Invalid or corrupted image file.")

    s3_object_name = f"originals/{uuid.uuid4().hex}.{file_extension}"

    try:
        s3_path = storage.upload_file_to_s3(
            file_obj=img_stream,
            bucket_name=settings.S3_PRODUCT_BUCKET_NAME,
            object_name=s3_object_name,
        )
    except Exception as e:
        # Log the error later
        raise HTTPException(
            status_code=500, detail=f"Failed to upload image to storage: {e}"
        )

    img_in = ImageCreate(
        path=s3_path,
        filename=s3_object_name,
        width=width,
        height=height,
        format=img.format,
        status=StatusEnum.QUEUED,  # use to show its waitin for a worker
        processing_details="Job created and queued for processing.",
    )
    image_db = create_image(session=session, image_in=img_in)

    # start the asynchronous pipeline
    start_indexing_pipeline(image_db.id)

    # return the initial public model of the job, and the 202 accepted status code.
    return ImagePublic.model_validate(image_db)


@router.post("/")
async def upload_single_img(
    session: SessionDep,
    content_length: Annotated[int, Header()],
    image_file: Annotated[UploadFile, File(description="Image File")],
) -> ImagePublic:
    if image_file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")

    if content_length > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    safe_filename = f"{uuid.uuid4().hex}_{image_file.filename}"  # later we see the need to sanataze the filename

    size = 0
    chunk_size = 1024 * 1024  # 1MB calculate later and save the result to a enum
    img_stream = BytesIO()

    while chunk := await image_file.read(chunk_size):  # chunk reading
        size += len(chunk)
        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        img_stream.write(chunk)

    try:
        img_stream.seek(0)  # set the pointer to the initial state
        img = Image.open(img_stream)
        img.verify()  # after the verify the image cannot be used

        img_stream.seek(0)
        img = Image.open(img_stream)
        img.load()

        width, heigth = img.size
        if width > 4000 and heigth > 4000:
            raise HTTPException(status_code=400, detail="Image Resolution too large")
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Image")

    img_stream.seek(0)

    os.makedirs("imgs", exist_ok=True)
    dest_path = f"imgs/{safe_filename}"
    with open(dest_path, "wb") as out_file:
        out_file.write(img_stream.getvalue())

    img_in = ImageCreate(
        path=dest_path,
        filename=safe_filename,
        width=width,
        height=heigth,
        format=img.format if hasattr(img, "format") else None,
        status=StatusEnum.UPLOADED,
    )
    print(f"image_in:{img_in}")

    image_db = create_image(session=session, image_in=img_in)
    image_public = ImagePublic.model_validate(image_db)

    # here we will initializate the pipeline of the tasks
    return image_public


@router.get("/")
async def get_imgs_data(session: SessionDep):
    imgs = get_image_list(session=session)

    return imgs


@router.get("/vector")
def get_imgs_in_vector_db(
    session: SessionDep, chroma: ChromaSessionDep
) -> list[ImagePublic]:
    imgs_collection = chroma.get_collection(name="imgs_colletion")
    imgs_ids = get_images_ids(collection=imgs_collection)
    imgs_data = get_image_list_by_ids(ids_list=imgs_ids, session=session)
    if not imgs_data:
        raise HTTPException(status_code=404, detail="No images found in the vector db")
    imgs_out = [ImagePublic.model_validate(img) for img in imgs_data]
    return imgs_out


@router.get("/vector/{img_id}")
async def get_image_vector_by_id(
    session: SessionDep, chroma_session: ChromaSessionDep, img_id: uuid.UUID
):
    # 1. Retrieve image from DB
    img = get_image_by_id(id=img_id, session=session)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    # 2. Get ChromaDB collection
    image_collection = chroma_session.get_collection(name="imgs_colletion")

    # 3. Retrieve image vector & metadata from Chroma
    img_in_chroma = get_image_data(img_id=img_id, collection=image_collection)

    if not img_in_chroma or not img_in_chroma.get("ids"):
        raise HTTPException(
            status_code=404, detail="Image vector not found in ChromaDB"
        )

    img_vector = None
    if img_in_chroma and img_in_chroma.get("embeddings") is not None:
        if (
            isinstance(img_in_chroma["embeddings"], np.ndarray)
            and img_in_chroma["embeddings"].size > 0
        ):
            img_vector = img_in_chroma["embeddings"][0].tolist()

    return {"image": img, "image_vector": img_vector}


@router.delete("/vector/{img_id}")
async def delete_img_in_vector_db(
    session: SessionDep, chroma: ChromaSessionDep, img_id: uuid.UUID
):
    collection = chroma.get_collection(name="imgs_colletion")
    img = get_image_by_id(id=img_id, session=session)
    if not img:
        raise HTTPException(status_code=404, detail="No image found with this id")

    delete_img_in_collection(img_id=img.id, collection=collection)
    return img


@router.delete("/sqldb/all")
def delete_all_images_in_db(session: SessionDep):
    session.execute(Delete(ImageDB))
    session.commit()
