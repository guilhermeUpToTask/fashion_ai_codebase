from io import BytesIO
import os
from pathlib import Path
from PIL import Image
from typing import Annotated, Any
from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
import uuid
from api.deps import SessionDep, CurrentUser
from models.image import ImageCreate, ImagePublic, StatusEnum
from core.image_crud import create_image

#need to use status enum for status code response!

MAX_FILE_SIZE = 5 * 1024 * 1024 # 5mb // calculate youself later
ALLOWED_TYPES = {"image/jpeg", "image/png"}

router = APIRouter(prefix="/upload_images", tags=["upload_images"])


@router.post("/")
async def upload_single_img(
     session:SessionDep,
     content_length: Annotated[int, Header()],
     image_file: Annotated[UploadFile, File(description="Image File")],
)-> ImagePublic :
     if image_file.content_type not in ALLOWED_TYPES:
           raise HTTPException(status_code=400, detail="Invalid file type")
     
     if content_length > MAX_FILE_SIZE:
          raise HTTPException(status_code=400, detail="File too large")
     
     safe_filename = f"{uuid.uuid4().hex}_{image_file.filename}" # later we see the need to sanataze the filename

     size= 0
     chunk_size = 1024 * 1024 # 1MB calculate later and save the result to a enum
     img_stream = BytesIO()

     while chunk := await image_file.read(chunk_size): # chunk reading
          size += len(chunk)
          if size > MAX_FILE_SIZE:
               raise HTTPException(status_code=400, detail="File too large")
          img_stream.write(chunk)
     
    
     try:
          img_stream.seek(0) # set the pointer to the initial state
          img = Image.open(img_stream)               
          img.verify() # after the verify the image cannot be used
          
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
          status=StatusEnum.UPLOADED  
     )
     print(f"image_in:{img_in}")
     
     image_db = create_image(session=session, image_in=img_in)
     image_public = ImagePublic.model_validate(image_db)

     return image_public