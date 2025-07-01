import logging

from sqlalchemy import Engine
from sqlmodel import Session, select, MetaData
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.db import engine
from backend.app.core.config import settings
from backend.app.core.user_crud import create_user
from backend.app.models.user import User, UserCreate, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init(db_engine: Engine) -> None:
    try:
        with Session(db_engine) as session:
            # Try to create session to check if DB is awake
            MetaData.create_all(engine)
            
            user = session.exec(
                select(User).where(User.email == settings.ADMIN_USER)
                ).first()
            if not user:
                user_create = UserCreate(
                email=settings.ADMIN_USER,
                password=settings.ADMIN_PASSWORD,
                role=UserRole.ADMIN
            )
            user = create_user(session=session, user_create=user_create)

    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    logger.info("Initializing service")
    init(engine)
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
