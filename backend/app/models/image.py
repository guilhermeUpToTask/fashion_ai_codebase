from datetime import datetime, timezone
import uuid
from sqlmodel import (
    JSON,
    Relationship,
    SQLModel,
    Field,
    Column,
)
from typing import List, Optional
from models.label import StructuredLabel


class ImageFile(SQLModel, table=True):
    __tablename__= "images" #type: ignore
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    path: str
    filename: str
    width: int | None
    height: int | None
    format: str | None
    label: StructuredLabel | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )
    
    #self relationship logic
    original_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="images.id",
        description="ID of original image if this is a crop",
    )
    original: Optional["ImageFile"] = Relationship(
        back_populates="crops", sa_relationship_kwargs={"remote_side": "ImageFile.id"}
    )
    crops: List["ImageFile"] = Relationship(back_populates="original")
    



class ImagePublic(SQLModel):
    id: uuid.UUID
    label: str | None
    path: str
    # later we need to pass the image itself as streaming response.


class ImageUpdate(SQLModel):
    filename: str | None = Field(default=None)
    label: StructuredLabel | None = Field(default=None)
    format: str | None = Field(
        default=None, description="Image format, e.g., PNG, JPEG"
    )
    is_primary_crop: bool = Field(default=False)


class ImageDelete:
    id: uuid.UUID
