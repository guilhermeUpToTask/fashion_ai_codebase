from enum import Enum
import uuid
from sqlmodel import JSON, CheckConstraint, Relationship, SQLModel, Field, Column, String
from pydantic import ConfigDict, field_validator
from pathlib import Path
from typing import List, Optional, Union
from models.label import StructuredLabel
from sqlalchemy import Enum as SAEnum

class StatusEnum(str, Enum):  # < needs to change the satatus for a better one
    UPLOADED = "uploaded"
    QUEUED = "queued"
    CROPPING = "cropping"
    ANALYZING = "analyzing"
    CROPPED = "cropped"
    LABELLED = "labelled"
    STORING = "storing"
    STORED = "stored"
    COMPLETE = "complete"
    FAILED = "failed"


class ImageBase(SQLModel):
    model_config = ConfigDict(use_enum_values=True) # type: ignore
    
    path: str = Field(..., description="S3 storage object path to the image")
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


# we will use for now the parent job status for main tracking, later we can study alternatives like tracking status of all the crops images for more granular observability.
class ImageDB(ImageBase, table=True):
    __tablename__ = "image"  # type: ignore
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    label: Optional[StructuredLabel] = Field(default=None, sa_column=Column(JSON))
    status: StatusEnum = Field(
        sa_column=Column(
            String(20),
            CheckConstraint(
                # Update this constraint with new values
                f"status IN ({', '.join(repr(s.value) for s in StatusEnum)})",
                name="check_status_enum"
            ),
            nullable=False
        ),
        description="Process status of the image",
    )
    
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
    label: Optional[StructuredLabel] = Field(default=None)
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
