from fastapi import APIRouter
from api.routes import users, auth
from api.routes.images import images, retrive_images

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(images.router)
api_router.include_router(retrive_images.router)
