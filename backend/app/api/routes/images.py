# refactor here.

from datetime import datetime
from io import BytesIO
import logging
from PIL import Image
from typing import Annotated, List, Literal, Optional
from fastapi import APIRouter, File, HTTPException, Header, Query, UploadFile
import uuid

from fastapi.responses import StreamingResponse
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
from models.image import ImageFile


router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)

@router.get("/{image_id}")
async def get_image_metadata(image_id: uuid.UUID, session: SessionDep):
    """Get image metadata"""
    img = session.get(ImageFile, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    return img


@router.get("/", response_model=List[ImageFile])
async def list_imgs_metadata(
    session: SessionDep,
    limit: int = Query(10, ge=1, le=20),
    offset: int = Query(0, ge=0),
):
    """List image metadata (paginated)"""
    results = session.exec(select(ImageFile).limit(limit).offset(offset)).all()

    return list(results)


# we changed for now we will only stream the img, when we prepare for prod we can utilize a get presigned url,
#TODO: for now its needs a field to determine the bucket, but later we need a field in the image to get wich bucket is the img
# needs cache headers aswell
# remender to fix it before prod, this is a major vunerabilitie for data leak
VALID_BUCKETS = [settings.S3_PRODUCT_BUCKET_NAME, settings.S3_QUERY_BUCKET_NAME]


@router.get("/{img_id}/download")
async def download_img(
    session: SessionDep,
    img_id: uuid.UUID,
    bucket: str = Query(..., description="Bucket name", enum=VALID_BUCKETS),
) -> StreamingResponse:
    if bucket not in VALID_BUCKETS:
        raise HTTPException(status_code=400, detail="Invalid Bucket name")

    try:
        img_metadata = session.get(ImageFile, img_id)
        if not img_metadata:
            raise HTTPException(status_code=404, detail="Img metadata not founded")
        s3_client = storage.get_s3_client()
        img_data = s3_client.get_object(Bucket=bucket, Key=img_metadata.filename)
        content_type = img_data.get("ContentType", "application/octet-stream")
        return StreamingResponse(
            img_data["Body"],
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={img_metadata.filename}",
                "Cache-Control": "public, max-age=86400",#cache for frontend max:1day
            },
        )

    except Exception as e:
        logger.error(f"Error downloading image {img_id} from bucket {bucket}: {e}", exc_info=True)
        raise e


@router.get("/{image_id}/crops")
async def get_image_crops(image_id: uuid.UUID, session: SessionDep):
    """Get all crops for an image"""
    img = session.get(ImageFile, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    return [crop for crop in img.crops]


# NO upload endpoints in images.py - those are handled by jobs!
