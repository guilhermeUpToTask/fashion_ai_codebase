import uuid
from typing import List, Optional
from sqlmodel import JSON, Field, PrimaryKeyConstraint, SQLModel, Column, Relationship

from models.product import Product, ProductImage

class IndexingResult(SQLModel, table=True):
    __tablename__= "indexing_result" #type: ignore
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    job_id: uuid.UUID = Field(foreign_key="job.id", unique=True)
    #input image and its crops created
    created_crop_ids: List[uuid.UUID] = Field(sa_column=Column(JSON))
    #stores the id of the specific image crop that was chosen as primary.
    selected_crop_id: uuid.UUID = Field(foreign_key="image.id")
    model_version: str = Field(max_length=50)
    
class QueryResultImage(SQLModel, table=True):
    __tablename__ = "query_result_product" #type: ignore
    __table_args__ = (PrimaryKeyConstraint("query_result_id", "product_id"),)
    
    query_result_id: uuid.UUID = Field(foreign_key="query_result.id")
    matched_image_id: uuid.UUID = Field(foreign_key="image.id")
    rank: int
    score: float
    
    #--- Relationships ---
    product: Product = Relationship()
    matched_product_image: "ProductImage" = Relationship()


class QueryResult(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    job_id: uuid.UUID = Field(foreign_key="job.id", unique=True)
    model_version: str = Field(max_length=50)
    
    similar_products: List["QueryResultImage"] = Relationship()
