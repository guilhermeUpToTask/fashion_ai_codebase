from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    ForeignKey,
    Text,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship

from src.infrastructure.db.orm_base import Base

# TODO:Create a repository for image artifact aswell, as its does not depends on the image analysis domain
class ImageAnalysisORM(Base):
    """
    ORM model for ImageAnalysisAggregate root.

    Represents the aggregate root with references to child entities.
    """

    __tablename__ = "image_analysis"

    id = Column(String(36), primary_key=True, nullabe=False)

    created_at = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)

    status = Column(String(50), nullable=False, index=True)

    # TODO: change it later for foregn key setted to image artifact
    source_image_id = Column(String(36), nullable=False, index=True)
    preprocessed_image_id = Column(String(36), nullable=True, index=True)

    error_message = Column(Text, nullable=True)
    error_origin = Column(String(255), nullable=True)

    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    clothing_items = relationship(
        "ClothingItemORM",
        back_populates="image_analysis",
        cascade_delete="all, delete-orphan",
        lazy="select",  # Explicit loading
    )

    processing_steps = relationship(
        "ProcessingStepORM",
        back_populates="image_analysis",
        cascade="all, delete-orphan",
        order_by="ProcessingStepORM.timestamp",
        lazy="select",
    )

    __table_args__ = (
        Index("idx_status_created", "status", "created_at"),
        Index("idx_source_image", "source_image_id"),
        Index("idx_deleted"),
    )

    def __repr__(self):
        return f"<ImageAnalysisORM(id={self.id}, status={self.status})>"


class ClothingItemORM(Base):
    """
    ORM model for ClothingItem entity.

    Child entity of ImageAnalysisAggregate.
    """

    __tablename__ = "clothing_items"  

    id = Column(String(36), primary_key=True, nullable=False)
    image_aggregate_id = Column(
        String(36),
        ForeignKey("image_analysis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    bbox_min_x = Column(Integer, nullable=False)
    bbox_min_y = Column(Integer, nullable=False)
    bbox_max_x = Column(Integer, nullable=False)
    bbox_max_y = Column(Integer, nullable=False)

    label_category = Column(String(50), nullable=True)
    label_pattern = Column(String(50), nullable=True)
    label_style = Column(String(50), nullable=True)
    label_color = Column(String(50), nullable=True)


    cropped_image_id = Column(String(36), nullable=True, index=True)
    embedding_id = Column(String(36), nullable=True, index=True)

    # Relationship back to aggregate
    image_analysis = relationship("ImageAnalysisORM", back_populates="clothing_items")

    # Indexes
    __table_args__ = (Index("idx_aggregate_item", "image_aggregate_id", "id"),)


class ProcessingStepORM(Base):
    """
    ORM model for ProcessingStep value object.

    Part of ProcessingHistory, child of ImageAnalysisAggregate.
    Steps are append-only and never updated.
    """

    __tablename__ = "processing_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)

    image_aggregate_id = Column(
        String(36),
        ForeignKey("image_analysis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True))
    message = Column(Text, nullable=True)
    attempt = Column(Integer, nullable=False, default=1)

    image_analysis = relationship("ImageAnalysisORM", back_populates="processing_steps")

    __table_args__ = (
        Index("idx_aggregate_timestamp", "image_aggregate_id", "timestamp"),
        Index("idx_status_timestamp", "status", "timestamp"),
    )

    def __repr__(self):
        return f"<ProcessingStepORM(status={self.status}, attempt={self.attempt})>"
