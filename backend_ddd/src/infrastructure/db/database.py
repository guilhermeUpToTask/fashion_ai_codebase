from collections.abc import Generator
from functools import lru_cache
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.engine import URL

from src.infrastructure.db.config import get_db_settings


@lru_cache()
def get_engine():
    settings = get_db_settings()
    url_object = URL.create(
        "postgresql+psycopg2",
        username=settings.DATABASE_USERNAME,
        password=settings.DATABASE_PASSWORD,
        host=settings.DATABASE_HOST,
        database=settings.DATABASE_NAME,
    )
    return create_engine(url_object, echo=True)
