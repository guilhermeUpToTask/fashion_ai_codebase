#here we will crop the main image into small croped imgs, creating few images crop in the db,
from io import BytesIO
import os
from pathlib import Path
from PIL import Image
from typing import Annotated, Any, List
from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
import uuid
from api.deps import SessionDep, CurrentUser
from models.image import ImageCreate, ImageDB, ImagePublic, StatusEnum
from core.image_crud import create_image, get_image_by_id
from core.cloth_detection.yolo import crop_img

router = APIRouter(prefix="/crop_image", tags=["crop_image"])


@router.post("/")
async def crop_uploaded_image(
     session:SessionDep,
     image_id:uuid.UUID,
     
) :
    img=get_image_by_id(id=image_id, session=session)
    if not img:
        raise HTTPException(status_code=404, detail="image not found")
    crop_paths = crop_img(image_id=img.id, image_path=img.path)
    
    if not crop_paths:
        raise HTTPException(status_code=500, detail="Could not crop the image")
    print(f"crop paths:{crop_paths}")
    print()
    
    cropped_img_ids: List[str] = []
    
    for c_path in crop_paths:
        img_crop = ImageCreate(
            path=c_path,
            filename="",
            status=StatusEnum.CROPPED,
            original_id=img.id
        )
        img_db = create_image(session=session, image_in=img_crop)
        cropped_img_ids.append(str(img_db.id))
    return cropped_img_ids

def get_cropedd_imgs_from_id():
    pass

def save_croped_images():
    pass

def return_croped_images_ids():
    pass 