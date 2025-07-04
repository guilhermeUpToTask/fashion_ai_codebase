import uuid
from sqlmodel import Session, select
from models.image import ImageCreate, ImageDB, ImageUpdate

def get_image_by_id(*,  id:uuid.UUID, session:Session) -> ImageDB | None:
    statement = select(ImageDB).where(ImageDB.id == id)
    session_image = session.exec(statement).first()
    return session_image
  
def create_image(*, session:Session, image_in:ImageCreate ) -> ImageDB: 
    db_image = ImageDB.model_validate(image_in)
    
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    
    return db_image

def update_image(*, session:Session, image_in: ImageUpdate, db_image: ImageDB):
    image_data= image_in.model_dump(exclude_unset=True)
    db_image.sqlmodel_update(image_data)
    
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    
    return db_image


def delete_image(id:int, session:Session):
    pass

