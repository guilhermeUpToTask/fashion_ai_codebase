import uuid
from typing import List, Optional
from pydantic import ConfigDict
from sqlmodel import JSON, Field, PrimaryKeyConstraint, SQLModel, Column, Relationship, UniqueConstraint

from models.product import Product, ProductImage

class IndexingResult(SQLModel, table=True):
    __tablename__= "indexing_results" #type: ignore
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    job_id: uuid.UUID = Field(foreign_key="jobs.id", unique=True)
    #input image and its crops created
    created_crop_ids: List[str] = Field(sa_column=Column(JSON))
    #stores the id of the specific image crop that was chosen as primary.
    selected_crop_id: uuid.UUID = Field(foreign_key="images.id")
    model_version: str = Field(max_length=50)
    
    
    
    
class QueryResultProductImage(SQLModel, table=True):
    __tablename__= 'query_result_product_images' #type: ignore
    __table_args__ = (UniqueConstraint("cloth_id", "matched_image_id"),)
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    cloth_id: uuid.UUID = Field(foreign_key="query_result_cloths.id")
    matched_image_id: uuid.UUID =  Field(foreign_key="images.id")
    score: float
    rank: int
    
    cloth: "QueryResultCloth"= Relationship(back_populates="similar_products")
    
class QueryResultCloth(SQLModel, table=True):
    __tablename__ = "query_result_cloths" #type: ignore
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    query_result_id: uuid.UUID = Field(foreign_key='query_results.id')
    crop_img_id: uuid.UUID =  Field(foreign_key='images.id')
    
    
    query_result: "QueryResult" = Relationship(back_populates="cloths")
    similar_products: List["QueryResultProductImage"] = Relationship(back_populates="cloth")


class QueryResult(SQLModel, table=True):
    __tablename__ = "query_results" #type: ignore
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    job_id: uuid.UUID = Field(foreign_key="jobs.id", unique=True)
    model_version: str = Field(max_length=50)
    
    cloths: List["QueryResultCloth"] = Relationship(back_populates="query_result")
