from functools import lru_cache
from pydantic import computed_field
from pydantic_settings import BaseSettings
from pydantic_core import MultiHostUrl


class DatabaseSettings(BaseSettings):
    DATABASE_USERNAME: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_NAME: str
    DATABASE_PORT: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> MultiHostUrl:
        return MultiHostUrl.build(  # change later for only use a database uri
            scheme="postgresql+psycopg2",
            username=self.DATABASE_USERNAME,
            password=self.DATABASE_PASSWORD,
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            path=self.DATABASE_NAME,
        )

@lru_cache()   # memoizes a function
def get_db_settings() -> DatabaseSettings:
    return DatabaseSettings() # type: ignore[call-arg] | because we load the args from the env
