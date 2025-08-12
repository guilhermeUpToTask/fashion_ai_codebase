from datetime import datetime, timezone
from enum import Enum
import uuid
from sqlmodel import (
    JSON,
    CheckConstraint,
    Relationship,
    SQLModel,
    Field,
    Column,
    String,
)
from typing import Any, Dict, Final, List, Optional
from core.config import settings
from models.label import StructuredLabel


# STATIC ENUM
class BucketName(str, Enum):
    PRODUCT = "product"
    QUERY = "query"


# RUNTIME MAPPING

BUCKET_NAME_TO_S3: Final[dict[BucketName, str]] = {
    BucketName.PRODUCT: settings.S3_PRODUCT_BUCKET_NAME,
    BucketName.QUERY: settings.S3_QUERY_BUCKET_NAME,
}


class ImageFile(SQLModel, table=True):
    __tablename__ = "images"  # type: ignore
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    bucket: BucketName = Field(
        sa_column=Column(
            String(20),
            CheckConstraint(
                # Update this constraint with new values
                f"bucket IN ({', '.join(repr(t.value) for t in BucketName)})",
                name="check_type_enum",
            ),
            nullable=False,
        ),
    )
    path: str
    filename: str
    width: int | None
    height: int | None
    format: str | None
    # needs to create a new table for label later on
    label: Dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    # self relationship logic
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


class ImageUpdate(SQLModel):
    filename: str | None = Field(default=None)
    label: StructuredLabel | None = Field(default=None)
    format: str | None = Field(
        default=None, description="Image format, e.g., PNG, JPEG"
    )
    is_primary_crop: bool = Field(default=False)


class ImageDelete:
    id: uuid.UUID
