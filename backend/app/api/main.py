from fastapi import APIRouter
from api.routes import users, auth, products, images, jobs
# routes/
# ├── __init__.py
# ├── jobs.py          ← Dedicated jobs routes
# ├── images.py        ← Image CRUD operations
# ├── products.py      ← Product CRUD operations


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(images.router)
api_router.include_router(products.router)
api_router.include_router(jobs.router)
