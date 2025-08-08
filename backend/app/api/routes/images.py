# refactor here.

from datetime import datetime
from io import BytesIO
from PIL import Image
from typing import Annotated, List, Optional
from fastapi import APIRouter, File, HTTPException, Header, UploadFile
import uuid

from pydantic import BaseModel
from sqlmodel import func, select
from models.result import (
    IndexingResult,
    QueryResult,
    QueryResultCloth,
    QueryResultProductImage,
)
from models.job import Job, JobStatus, JobType
from models.product import Product, ProductImage
from worker.tasks import indexing_orchestrator_task, querying_orchestrator_task

# --- Core Application Imports ---
from api.deps import CurrentUser, SessionDep
from core.config import settings
from core import storage

# --- Model & Workflow Imports ---
from models.image import ImageFile, 


router = APIRouter(prefix="/images", tags=["images"])

@router.get("/{image_id}")
async def get_image_metadata(image_id: uuid.UUID, session: SessionDep):
    """Get image metadata - read-only operations"""
    img = session.get(ImageFile, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    return img

#needs pagination
@router.get("/")
async def list_imgs_metadata(image_id: uuid.UUID, session: SessionDep) -> List[ImageFile]:
    """Get all crops for an image"""
    return []


#here we need to pass a bucket name based on the image type or something
@router.get("/{image_id}/download")
async def download_image(image_id: uuid.UUID, session: SessionDep):
    """Download image file from S3"""
    img = session.get(ImageFile, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Return S3 download URL or stream file
    return storage.download_file_from_s3(img.path)

@router.get("/{image_id}/crops")
async def get_image_crops(image_id: uuid.UUID, session: SessionDep):
    """Get all crops for an image"""
    img = session.get(ImageFile, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return [crop for crop in img.crops]



# NO upload endpoints in images.py - those are handled by jobs!