from fastapi import APIRouter
from api import img_inference
api_router = APIRouter()
api_router.include_router(img_inference.router)

