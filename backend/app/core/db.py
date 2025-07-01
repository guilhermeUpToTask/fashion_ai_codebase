from sqlmodel import SQLModel, select, create_engine, Session
from sqlalchemy.engine import URL
from core.config import settings

url_object = URL.create(
    "postgresql+psycopg2",
    username=settings.DATABASE_USERNAME,
    password=settings.DATABASE_PASSWORD, 
    host=settings.DATABASE_HOST,
    database=settings.DATABASE_NAME,
)
engine = create_engine(url_object, echo=True)


