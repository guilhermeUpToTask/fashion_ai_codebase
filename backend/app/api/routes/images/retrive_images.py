# here we gonna get a cropped img id and process itm update the table to a labelled img, then res the idc

from io import BytesIO
import os
from pathlib import Path
from PIL import Image
from typing import Annotated, Any, List
from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
import uuid
from api.deps import SessionDep, CurrentUser, ChromaSessionDep
from models.image import ImageCreate, ImageDB, ImagePublic, ImageUpdate, StatusEnum
from core.image_crud import update_image, get_image_by_id
from core.ingestors import ingest_img
from core.retriver.img_retriver import retrive_most_similar_img


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


@router.post("/query")
async def ingest_image_query(
    session: SessionDep,
    chroma: ChromaSessionDep,
    image_id: uuid.UUID,
):
    image = get_image_by_id(id=image_id, session=session)
    image = validate_cropped_image(image=image)
    ingested_info = ingest_img.ingest(img_path=image.path)

    # here we will retrive
    imgs_collection = chroma.get_collection(name="imgs_colletion")
    similar_img = retrive_most_similar_img(
        img_vector=ingested_info["img_vector"],
        label_vector=ingested_info["label_vector"],
        collection=imgs_collection,
        session=session,
    )
    
    return similar_img
