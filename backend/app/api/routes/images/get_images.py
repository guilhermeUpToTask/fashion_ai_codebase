from io import BytesIO
import os
from pathlib import Path
from PIL import Image
from typing import Annotated, Any
from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
import uuid

import numpy as np
from api.deps import SessionDep, CurrentUser, ChromaSessionDep
from models.image import ImageCreate, ImagePublic
from core.image_crud import get_image_list, get_image_by_id
from core.vector_db.img_vector_crud import get_image_data

# need to use status enum for status code response!

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5mb // calculate youself later
ALLOWED_TYPES = {"image/jpeg", "image/png"}

router = APIRouter(prefix="/get_images", tags=["get_images"])


@router.get("/")
async def get_images_data(session: SessionDep) -> list[ImagePublic]:
    imgs = get_image_list(session=session)
    imgs_out = [ImagePublic.model_validate(img) for img in imgs]

    return imgs_out


@router.get("/vector")
async def get_image_data_by_id(
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
    print("all_imgs_in_chroma", image_collection.get())
    print("img_in_chroma:", img_in_chroma)

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
