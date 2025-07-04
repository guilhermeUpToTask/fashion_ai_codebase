import uuid
from sqlmodel import Relationship, SQLModel, Field
from pydantic import field_validator
from pathlib import Path
from typing import List, Optional

class ImageBase(SQLModel):
    path: Path = Field(..., description="Filesystem path to the image")
    label: Optional[str] = Field(None, description="Label (e.g., sweater, jacket, etc.)")
    label_vector: Optional[List[float]] = Field(None, description="Vector embedding of the label")
    img_vector: Optional[List[float]] = Field(None, description="Vector embedding of the image")
    width: Optional[int] = Field(None, gt=0, description="Image width in pixels")
    height: Optional[int] = Field(None, gt=0, description="Image height in pixels")
    format: Optional[str] = Field(None, description="Image format, e.g., PNG, JPEG")
    
    is_crop: Optional[bool] = Field(False, description="Indicates if this image is a cropped part of a larger image")
    original_id: Optional[uuid.UUID] = Field(default=None, foreign_key="image.id", description="ID of original image if this is a crop")


    @field_validator("path")
    def path_must_exist(cls, v: Path):
        if not v.exists():
            raise ValueError(f"Image path does not exist: {v}")
        return v

class ImageDB(ImageBase, table=True):
    __tablename__ = "image" # type: ignore
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    original: Optional["ImageDB"] = Relationship(back_populates="crops", sa_relationship_kwargs={"remote_side": "ImageDB.id"})
    crops: List["ImageDB"] = Relationship(back_populates="original")
   
class ImageCreate(ImageBase):
    pass

class ImagePublic(SQLModel):
    id:uuid.UUID
    label:str = Field(description="Label (e.g., sweater, jacket, etc.)")

class ImageUpdate(SQLModel):
    label: Optional[str] = Field(None, description="Label (e.g., sweater, jacket, etc.)")
    label_vector: Optional[List[float]] = Field(None, description="Vector embedding of the label")
    img_vector: Optional[List[float]] = Field(None, description="Vector embedding of the image")

class ImageDelete():
    id: uuid.UUID


class ProductImage():
    pass
class ProductImageDB():
    pass
class ProductImageCreate():
    pass
class ProductImageDelete():
    pass