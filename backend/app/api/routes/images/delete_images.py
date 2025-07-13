
from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
import uuid

import numpy as np
from sqlalchemy import delete
from api.deps import SessionDep, CurrentUser, ChromaSessionDep
from models.image import ImageCreate, ImageDB, ImagePublic
from core.image_crud import get_image_list, get_image_by_id, get_image_list_by_ids
from core.vector_db.img_vector_crud import delete_img_in_collection


router = APIRouter(prefix="/delete_images", tags=["delete_images"])


@router.delete("/vector/{img_id}")
async def delete_img_in_vector_db(session: SessionDep, chroma:ChromaSessionDep, img_id: uuid.UUID):
    collection = chroma.get_collection(name="imgs_colletion")
    img = get_image_by_id(id=img_id, session=session)
    if not img:
        raise HTTPException(status_code=404, detail="No image found with this id")
    
    delete_img_in_collection(img_id=img.id, collection=collection)
    return img

@router.delete("/sqldb")
def delete_all_images_in_db(session: SessionDep):
    session.execute(delete(ImageDB))
    session.commit()
