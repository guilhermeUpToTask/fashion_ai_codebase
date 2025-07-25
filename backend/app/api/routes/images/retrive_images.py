# here we gonna get a cropped img id and process itm update the table to a labelled img, then res the idc

from io import BytesIO
import os
from pathlib import Path
from PIL import Image
from typing import Annotated, Any, List
from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
import uuid

import numpy as np
from api.deps import SessionDep, CurrentUser, ChromaSessionDep
from core.config import Settings
from core.vector_db.img_vector_crud import delete_img_in_collection, get_image_data, get_images_ids
from models.image import ImageCreate, ImageDB, ImagePublic, ImageUpdate, StatusEnum
from core.image_crud import get_image_list_by_ids, update_image, get_image_by_id


def verify_status(*, img: ImageDB, desired_status: StatusEnum) -> bool:
    return img.status == desired_status


router = APIRouter(prefix="/retrive_img", tags=["ingest_image"])


def validate_cropped_image(image: ImageDB | None) -> ImageDB:
    if not image:
        raise HTTPException(status_code=404, detail="No image Found")
    # image needs to be cropped into a cloth piece to search for that
    if not verify_status(img=image, desired_status=StatusEnum.CROPPED):
        raise HTTPException(status_code=401, detail="Image not in cropped status")

    return image

# we will try a different pipeline of tasks, where will be using the croping and labeling pipeline of the query cloths,and add new task in the place of saving, will be querring, and to finalize will group all similar products and return its ids
#we will use a new query model to store the similar products, and later that what we will use with the agentic model to chose best matching product.
@router.post("/query")
async def ingest_image_query(
    session: SessionDep,
    chroma: ChromaSessionDep,
    image_id: uuid.UUID,
):
    image = get_image_by_id(id=image_id, session=session)
    image = validate_cropped_image(image=image)
    #ingested_info = ingest_img.ingest(img_path=image.path)

    # here we will retrive
    imgs_collection = chroma.get_collection(name="imgs_colletion")
    # similar_img = retrive_most_similar_img(
    #     img_vector=ingested_info["img_vector"],
    #     label_vector=ingested_info["label_vector"],
    #     collection=imgs_collection,
    #     session=session,
    # )
    
    return "similar_img"


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
    img = get_image_by_id(id=img_id, session=session)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    img_in_chroma = get_image_data(img_id=img_id, chroma_session=chroma_session, collection_name=Settings.IMAGES_COLLECTION_NAME)

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
