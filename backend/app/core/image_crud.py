from typing import List
import uuid
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, col
from models.query import QueryImage
from models.image import ImageCreate, ImageDB, ImageUpdate, StatusEnum
from sqlmodel import col


def get_image_by_id(*, id: uuid.UUID, session: Session) -> ImageDB | None:
    statement = select(ImageDB).where(ImageDB.id == id)
    session_image = session.exec(statement).first()
    return session_image


def get_image_list(session: Session) -> list[ImageDB]:
    statement = select(ImageDB)
    results = session.exec(statement).all()
    return list(results)


def get_image_list_by_ids(session: Session, ids_list: List[uuid.UUID]) -> List[ImageDB]:
    statement = select(ImageDB).where(col(ImageDB.id).in_(ids_list))
    result = session.exec(statement).all()
    return list(result)


def create_image(*, session: Session, image_in: ImageCreate) -> ImageDB:
    db_image = ImageDB.model_validate(image_in)
    print("db image:", db_image)
    session.add(db_image)
    session.commit()
    session.refresh(db_image)

    return db_image


def update_image(*, session: Session, image_in: ImageUpdate, db_image: ImageDB):
    image_data = image_in.model_dump(exclude_unset=True)
    db_image.sqlmodel_update(image_data)
    session.add(db_image)
    session.commit()
    session.refresh(db_image)

    return db_image


def update_job_status(
    session: Session,
    job_image: ImageDB,
    new_status: StatusEnum,
    details: str | None = None,
):
    "function design to update the parents jobs status. that we use to track the tasks processing"

    update_data: ImageUpdate = ImageUpdate(status=new_status)
    if details:
        update_data.processing_details = details
        
    return update_image(session=session, image_in=update_data, db_image=job_image)
    
def get_query_image_by_id(*, session: Session, query_id: uuid.UUID) -> QueryImage | None:
    """
    Retrieves a QueryImage by its ID, eagerly loading its similar_products.
    """
    statement = (
        select(QueryImage)
        .where(QueryImage.id == query_id)
        .options(selectinload(getattr(QueryImage, "similar_products"))) # Eagerly load relationship
    )
    result = session.exec(statement).first()
    return result


def delete_image(id: int, session: Session):
    pass
