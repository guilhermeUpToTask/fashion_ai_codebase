import logging
from PIL import Image
from typing import Annotated, List
from fastapi import APIRouter, HTTPException, Header, Path, Query, status
import uuid

from fastapi.responses import StreamingResponse
from sqlmodel import  select
from api.deps import CurrentUser, SessionDep
from core.config import settings
from core import storage
from models.image import ImageFile


router = APIRouter(prefix="/images", tags=["images"])
logger = logging.getLogger(__name__)

@router.get(
    "/{image_id}",
    response_model=ImageFile,
    responses={404: {"description": "Image not found"}},
)
async def get_image_metadata(
    image_id: Annotated[uuid.UUID, Path(description="ID of the image")],
    session: SessionDep,
) -> ImageFile:
    """
    Get image metadata by ID.
    """
    img = session.get(ImageFile, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    return img


@router.get(
    "/",
    response_model=List[ImageFile],
    responses={500: {"description": "Internal server error"}},
)
async def list_imgs_metadata(
    session: SessionDep,
    limit: int = Query(10, ge=1, le=50, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> List[ImageFile]:
    """
    List image metadata (paginated).
    """
    results = session.exec(select(ImageFile).limit(limit).offset(offset)).all()
    return list(results)


# we changed for now we will only stream the img, when we prepare for prod we can utilize a get presigned url,
#TODO: for now its needs a field to determine the bucket, but later we need a field in the image to get wich bucket is the img
# needs cache headers aswell
# remender to fix it before prod, this is a major vunerabilitie for data leak
VALID_BUCKETS = [settings.S3_PRODUCT_BUCKET_NAME, settings.S3_QUERY_BUCKET_NAME]
@router.get(
    "/{img_id}/download",
    response_class=StreamingResponse,
    responses={
        200: {"description": "Image binary stream"},
        400: {"description": "Invalid bucket or request"},
        404: {"description": "Image metadata not found"},
        500: {"description": "Internal server error"},
    },
)
async def download_img(
    img_id: Annotated[uuid.UUID, Path(description="ID of the image to download")],
    session: SessionDep,
    bucket: Annotated[str, Query(..., description="Bucket name", enum=VALID_BUCKETS)],
) -> StreamingResponse:
    """
    Stream image bytes from S3/MinIO to client.
    Note: if using boto3 (sync) consider offloading to a threadpool to avoid blocking the event loop.
    """
    
    
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
            status_code=status.HTTP_200_OK,
        )

    except ValueError as e:
        logger.warning(f"Validation error downloading image {img_id} from bucket {bucket}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error downloading image {img_id} from bucket {bucket}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to download image")




@router.get(
    "/{image_id}/crops",
    response_model=List[ImageFile],  # replace Dict with a proper Crop model if you have one
    responses={404: {"description": "Image not found"}, 500: {"description": "Internal server error"}},
)
async def get_image_crops(
    image_id: Annotated[uuid.UUID, Path(description="ID of the image")],
    session: SessionDep,
) -> List[ImageFile]:
    """
    Get all crops for an image.
    Returns a list of crop objects (replace with real model when available).
    """
    img = session.get(ImageFile, image_id)
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    try:
        crops = [crop for crop in img.crops]
        return crops
    except Exception as e:
        logger.error(f"Error fetching crops for image {image_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch crops")

