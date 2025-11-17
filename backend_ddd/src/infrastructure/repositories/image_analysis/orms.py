from datetime import datetime
from typing import List
from sqlmodel import (
    Column,
    PrimaryKeyConstraint,
    String,
    DateTime,
    Integer,
    ForeignKey,
    Text,
    Boolean,
    Index,
    SQLModel,
    Field,
    Relationship
)
from sqlalchemy.orm import relationship

class ImageAnalysisORM(SQLModel, table=True):
    """
    ORM model for ImageAnalysisAggregate root.

    Represents the aggregate root with references to child entities.
    """

    __tablename__ = "image_analysis"  # pyright: ignore[reportAssignmentType]

    id: str = Field(sa_column=Column(String(36), primary_key=True, nullable=False))

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    started_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    completed_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    status: str = Field(sa_column=Column(String(50), nullable=False, index=True))

    source_image_id: str = Field(
        sa_column=Column(String(36), nullable=False, index=True)
    )
    preprocessed_image_id: str | None = Field(
        sa_column=Column(String(36), nullable=True, index=True)
    )

    error_message: str | None = Field(sa_column=Column(Text, nullable=True))
    error_origin: str | None = Field(sa_column=Column(String(255), nullable=True))

    clothing_items: List["ClothingItemORM"] = Relationship(
        back_populates="image_analysis",
        sa_relationship=relationship(
            cascade="all, delete-orphan",
            lazy="select",
        ),
    )
    processing_steps: List["ProcessingStepORM"] = Relationship(
        back_populates="image_analysis",
        sa_relationship=relationship(
            cascade="all, delete-orphan",
            lazy="select",
        ),
    )

    __table_args__ = (
        Index("idx_status_created", "status", "created_at"),
        Index("idx_source_image", "source_image_id"),
    )

    def __repr__(self):
        return f"<ImageAnalysisORM(id={self.id}, status={self.status})>"


#TODO: consider utilizes mapped colum instead of sqlmodel to see if its better compatibility or not.
class ClothingItemORM(SQLModel, table=True):
    """
    ORM model for ClothingItem entity.

    Child entity of ImageAnalysisAggregate.
    """

    __tablename__ = "clothing_items"  # pyright: ignore[reportAssignmentType]

    id: str = Field(sa_column=Column(String(36), primary_key=True, nullable=False))
    image_aggregate_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("image_analysis.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    bbox_x_min: int = Field(sa_column=Column(Integer, nullable=False))
    bbox_y_min: int = Field(sa_column=Column(Integer, nullable=False))
    bbox_x_max: int = Field(sa_column=Column(Integer, nullable=False))
    bbox_y_max: int = Field(sa_column=Column(Integer, nullable=False))

    label_category: str | None = Field(sa_column=Column(String(50), nullable=True))
    label_pattern: str | None = Field(sa_column=Column(String(50), nullable=True))
    label_style: str | None = Field(sa_column=Column(String(50), nullable=True))
    label_color: str | None = Field(sa_column=Column(String(50), nullable=True))

    cropped_image_id: str | None = Field(
        sa_column=Column(String(36), nullable=True, index=True)
    )
    embedding_id: str | None = Field(
        sa_column=Column(String(36), nullable=True, index=True)
    )

    # Relationship back to aggregate
    image_analysis: "ImageAnalysisORM" = Relationship(
        back_populates="clothing_items",
    )

    # Indexes
    __table_args__ = (Index("idx_aggregate_item", "image_aggregate_id", "id"),)


class ProcessingStepORM(SQLModel, table=True):
    """
    ORM model for ProcessingStep value object.

    Part of ProcessingHistory, child of ImageAnalysisAggregate.
    Steps are append-only and never updated.
    """

    __tablename__ = "processing_steps"  # pyright: ignore[reportAssignmentType]
    # TODO: be aware to microseconds mismatch betwen persistence layer and domain layer. create a suit of tests to verify if the processing steps are preservated
    __table_args__ = (
        PrimaryKeyConstraint("image_aggregate_id", "timestamp", "status"),
        Index("idx_aggregate_timestamp", "image_aggregate_id", "timestamp"),
        Index("idx_status_timestamp", "status", "timestamp"),
    )

    image_aggregate_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("image_analysis.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    status: str = Field(sa_column=Column(String(50), nullable=False, index=True))
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    message: str | None = Field(sa_column=Column(Text, nullable=True))
    attempt: int = Field(sa_column=Column(Integer, nullable=False))

    image_analysis: "ImageAnalysisORM" = Relationship(
        back_populates="processing_steps",
    )

    def __repr__(self):
        return f"<ProcessingStepORM(status={self.status}, attempt={self.attempt})>"
