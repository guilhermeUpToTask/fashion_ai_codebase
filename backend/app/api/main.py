from fastapi import APIRouter
from api.routes import users, auth, products
from api.routes.images import images

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(images.router)
api_router.include_router(products.router)
