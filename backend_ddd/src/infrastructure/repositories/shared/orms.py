from datetime import datetime
from sqlmodel import (
    Column,
    Field,
    String,
    DateTime,
    Integer,
    Index,
    JSON,
    SQLModel,
)


class EmbeddingORM(SQLModel, table=True):
    __tablename__ = "embeddings"  # pyright: ignore[reportAssignmentType]

    id: str = Field(sa_column=Column(String(36), primary_key=True))
    model_name: str = Field(sa_column=Column(String(100), nullable=False, index=True))
    vector: list[float] = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    __table_args__ = (Index("idx_embedding_model_created", "model_name", "created_at"),)


# TODO:valuate the need of timestamps for image artifact
class ImageArtifactORM(SQLModel, table=True):
    __tablename__ = "image_artifacts"  # pyright: ignore[reportAssignmentType]
    id: str = Field(sa_column=Column(String(36), primary_key=True, nullable=False))
    blob_ref: str = Field(sa_column=Column(String(150), nullable=False))
    mime_type: str = Field(sa_column=Column(String(36), nullable=False))
    width: int = Field(sa_column=Column(Integer, nullable=False))
    height: int = Field(sa_column=Column(Integer, nullable=False))
