from pydantic import PostgresDsn
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import (
    PostgresDsn,
    computed_field,
)
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # Vai de .../app/core/config.py até /project


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_ignore_empty=True,
        extra="ignore",
    )
    
    PROJECT_NAME: str
    DATABASE_USERNAME : str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_NAME: str
    DATABASE_PORT: int
    SECRET_KEY: str
    ALGORITHM: str
    ADMIN_USER: str
    ADMIN_PASSWORD: str
    ML_SERVICE_URL: str
    IMAGES_COLLECTION_NAME: str = "images_collection"
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_PRODUCT_BUCKET_NAME: str
    MAX_IMAGE_SIZE_BYTES: int = 5 * 1024 * 1024 # 5mb
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> MultiHostUrl:
        return MultiHostUrl.build(#change later for only use a database uri
            scheme="postgresql+psycopg2",
            username=self.DATABASE_USERNAME,
            password=self.DATABASE_PASSWORD,
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            path=self.DATABASE_NAME,
        )
    all_cors_origins: list[str] = ["*"]

settings = Settings()# type: ignore[call-arg] | because we load the args from the env
