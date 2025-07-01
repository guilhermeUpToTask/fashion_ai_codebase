from io import BytesIO
import os
from PIL import Image
from typing import Annotated, Any
from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
import uuid
from api.deps import SessionDep, CurrentUser

MAX_FILE_SIZE = 5 * 1024 * 1024 # 5mb // calculate youself later
ALLOWED_TYPES = {"image/jpeg", "image/png"}

router = APIRouter(prefix="/upload_images", tags=["upload_images"])

@router.post("/")
async def upload_single_img(
     content_length: Annotated[int, Header()],
     image_file: Annotated[UploadFile, File(description="Image File")],
) :
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
          
     return{
          "name": image_file.filename,
          "safe_filename": safe_filename,
          "type": image_file.content_type,
          "content_length": content_length,
          "width": width,
          "height": heigth,
           "size_bytes": size,
          }