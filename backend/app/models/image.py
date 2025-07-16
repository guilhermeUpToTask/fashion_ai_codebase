from enum import Enum
import uuid
from sqlmodel import JSON, Relationship, SQLModel, Field
from pydantic import field_validator
from pathlib import Path
from typing import List, Optional, Union
from models.label import StructuredLabel


class StatusEnum(str, Enum):  # < needs to change the satatus for a better one
    UPLOADED = "uploaded"
    QUEUED = "queued"
    CROPPING = "croppping"
    ANALYZING = "analyzing"
    CROPPED= "CROPPED"
    STORED = "stored"
    COMPLETE = "complete"
    FAILED = "failed"


class ImageBase(SQLModel):
    path: str = Field(..., description="Filesystem path to the image")
    filename: str
    label: StructuredLabel | None = Field(
        default=None, description="Label structured in color, style, category and etc."
    )
    width: int | None = Field(default=None, gt=0, description="Image width in pixels")
    height: int | None = Field(default=None, gt=0, description="Image height in pixels")
    format: str | None = Field(
        default=None, description="Image format, e.g., PNG, JPEG"
    )
    status: StatusEnum = Field(description="Process status of the image")
    processing_details: str | None = Field(
        default=None, description="Details about the current processing step"
    )
    original_id: Optional[uuid.UUID] = Field(
        default=None,
        foreign_key="image.id",
        description="ID of original image if this is a crop",
    )

    @field_validator("path")
    def path_must_exist(cls, v: str):  # Change type hint to str
        # Convert to Path object for validation, then discard or don't store it
        if not Path(v).exists():  # Convert string to Path for existence check
            raise ValueError(f"Image path does not exist: {v}")
        return v  # Return the string, as the field is now str


# we will use for now the parent job status for main tracking, later we can study alternatives like tracking status of all the crops images for more granular observability.
class ImageDB(ImageBase, table=True):
    __tablename__ = "image"  # type: ignore
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    original: Optional["ImageDB"] = Relationship(
        back_populates="crops", sa_relationship_kwargs={"remote_side": "ImageDB.id"}
    )
    crops: List["ImageDB"] = Relationship(back_populates="original")


class ImageCreate(ImageBase):
    pass


class ImagePublic(SQLModel):
    id: uuid.UUID
    label: str | None
    status: StatusEnum


class ImageUpdate(SQLModel):
    filename: str | None = Field(default=None)
    status: StatusEnum | None = Field(default=None)
    label: Optional[str] = Field(default=None)
    processing_details: str | None = Field(default=None)


class ImageDelete:
    id: uuid.UUID


class ProductImage:
    pass


class ProductImageDB:
    pass


class ProductImageCreate:
    pass


class ProductImageDelete:
    pass
