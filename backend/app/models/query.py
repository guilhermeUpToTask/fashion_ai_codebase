from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from sqlmodel import Field, PrimaryKeyConstraint, Relationship, SQLModel


class QuerySimilarProduct(SQLModel, table=True):
    __tablename__ = "query_similar_product"  # type: ignore
    __table_args__ = (PrimaryKeyConstraint("image_query_id", "product_id"),)

    image_query_id: UUID = Field(default=None, foreign_key="query_image.id")
    product_id: UUID = Field(default=None, foreign_key="image.id")
    score: float = Field(default=0.0)
    rank: int = Field(default=0)

    query_image: Optional["QueryImage"] = Relationship(
        back_populates="similar_products"
    )


class QueryImage(SQLModel, table=True):
    __tablename__ = "query_image"  # type: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID | None = Field(default=None, foreign_key="user.id")
    input_image_id: UUID = Field(foreign_key="image.id")
    model_version: str = Field(max_length=50)
    # Ptyhon: " lambda: " = Javascript: "() =>"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    similar_products: List["QuerySimilarProduct"] = Relationship(
        back_populates="query_image"
    )

class QuerySimilarProductPublic(SQLModel):
    """Public representation of a single similar product result."""
    product_id: UUID
    score: float
    rank: int
    # You could add more product details here later by joining with the ImageDB table

class QueryImagePublic(SQLModel):
    """Public representation of a complete query result."""
    id: UUID
    input_image_id: UUID
    model_version: str
    created_at: datetime
    similar_products: List[QuerySimilarProductPublic] = []