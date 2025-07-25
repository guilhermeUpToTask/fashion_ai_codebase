# This file ensures that all models are loaded by SQLAlchemy in the correct order.

# Import models with no or simple dependencies first
from .user import User
from .image import ImageDB

# Import models that have foreign keys to the above tables
from .query import QueryImage, QuerySimilarProduct

# Import any other models here...