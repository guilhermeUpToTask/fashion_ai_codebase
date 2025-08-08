# This file ensures that all models are loaded by SQLAlchemy in the correct order.

# Import models with no or simple dependencies first
from .user import User
from .image import ImageFile

# Import models that have foreign keys to the above tables
from .product import Product, ProductImage
from .result import IndexingResult, QueryResult, QueryResultCloth, QueryResultProductImage
from .job import Job
