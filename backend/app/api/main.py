from fastapi import APIRouter
from api.routes import users, auth, upload_images

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(upload_images.router)



