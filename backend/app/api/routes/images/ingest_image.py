#here we gonna get a cropped img id and process itm update the table to a labelled img, then res the idc
 
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
from core.vector_db import img_vector_crud

def verify_status(*,img:ImageDB, desired_status:StatusEnum) -> bool : 
    return img.status == desired_status

router = APIRouter(prefix="/ingest_image", tags=["ingest_image"])


def validate_cropped_image(image:ImageDB | None) -> ImageDB:
    if not image:
        raise HTTPException(status_code=404,detail="No image Found")
    #image needs to be cropped into a cloth piece to search for that
    if not verify_status(img=image,desired_status=StatusEnum.CROPPED):
        raise HTTPException(status_code=401,detail="Image not in cropped status")
    
    return image

@router.post("/")
async def ingest_image(
     session:SessionDep,
     chroma:ChromaSessionDep,
     image_id:uuid.UUID,
):
    image = get_image_by_id(id=image_id, session=session)
    if not image:
        raise HTTPException(status_code=404,detail="No image Found")
    
    #image needs to be cropped into a cloth piece to search for that
    if not verify_status(img=image,desired_status=StatusEnum.CROPPED):
        raise HTTPException(status_code=401,detail="Image not in cropped status")
    
    #here we ingest the image and recive the img_vector, as the label for it and its vector
    result = ingest_img.ingest(img_path=image.path)
    label = result["label"]
    img_vector = result["img_vector"]
    label_vector = result["label_vector"]
    
    #possibility of saving the label before saving in the chomadb, if vector server faield, the process can be redone using less process, needs to analize later. 
    
    #here we merge both vectors and then save it into a chomadb, the id is the same as the image metadata, the colletion needs to be setted later, as well a colletion for the label database
    vector_id= img_vector_crud.add_image_data(img_id=image_id, img_vector=img_vector, label_vector=label_vector, session=chroma)
    if not vector_id:
        raise HTTPException(status_code=500, detail="Server Failed to save embeddings into vector db")
    
    #here we update the image metadata changed its status state to stored, meaning its vectors are stored in a vector database, aswell save the label for metadata
    image_in = ImageUpdate(status=StatusEnum.STORED, label=label)
    updated_img = update_image(session=session,image_in=image_in, db_image=image)
    
    return ImagePublic.model_validate(updated_img)
    
    
    