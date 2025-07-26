import uuid
from typing import List
from sqlmodel import JSON, Field, PrimaryKeyConstraint, SQLModel, Column, Relationship
from .image import ImagePublic

class IndexingResult(SQLModel, table=True):
    __tablename__= "indexing_result" #type: ignore
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    job_id: uuid.UUID = Field(foreign_key="job.id", unique=True)
    #should i add a product id here aswell?
    created_crop_ids: List[uuid.UUID] = Field(sa_column=Column(JSON))
    primary_crop_id : uuid.UUID = Field(foreign_key="image.id")

    model_version: str = Field(max_length=50)
    
class QueryResultProduct(SQLModel, table=True):
    __tablename__ = "query_result_product" #type: ignore
    
    __table_args__ = (PrimaryKeyConstraint("query_result_id", "product_id"),)
    query_result_id: uuid.UUID = Field(foreign_key="query_result.id")
    product_id: uuid.UUID = Field(foreign_key="product.id")
    rank: int
    score: float

class QueryResult(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    job_id: uuid.UUID = Field(foreign_key="job.id", unique=True)
    model_version: str = Field(max_length=50)
    similar_products: List["QueryResultProduct"] = Relationship(
        back_populates="query_result_product"
    )
