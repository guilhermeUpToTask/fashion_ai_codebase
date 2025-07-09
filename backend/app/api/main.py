from fastapi import APIRouter
from api.routes import users, auth
from api.routes.images import ingest_image, get_images, crop_image, upload_images

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(upload_images.router)
api_router.include_router(crop_image.router)
api_router.include_router(ingest_image.router)
api_router.include_router(get_images.router)
