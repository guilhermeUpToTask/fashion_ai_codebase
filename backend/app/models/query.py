from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4
from sqlmodel import Field, Relationship, SQLModel


class QuerySimilarProduct(SQLModel, table=True):
    __name__= "query_similar_product"  # type: ignore
    image_query_id: UUID = Field(
        default=None, foreign_key="image_query.id", primary_key=True
    )
    # for now we will use the image id, later we will have a product model
    product_id: UUID = Field(default=None, foreign_key="image.id")
    score: float = Field(default=0.0)
    rank: int = Field(default=0)


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
