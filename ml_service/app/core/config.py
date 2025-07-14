from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str
    all_cors_origins: list[str] = ["*"]

settings = Settings()# type: ignore[call-arg] | because we load the args from the env
