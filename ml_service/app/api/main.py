from fastapi import APIRouter
from api import img_inference
from api import text_inferece

api_router = APIRouter()
api_router.include_router(img_inference.router)
api_router.include_router(text_inferece.router)
