from uuid import UUID, uuid4
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

from backend.app.models.image import ImageFile



class Product(SQLModel, table=True):
    __tablename__ = "products" #type: ignore
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    #A SKU is a unique alphanumeric code assigned to a specific product to identify and track it for inventory purposes.
    #example: A "Levi's 501 Jeans, Blue, Size 32x32" might have a SKU of LEV501-BL-3232.
    sku: str | None = Field(default=None, unique=True, index=True)
    name: str = Field(index=True)
    description: str | None
    
    #adapted relationshipt
    product_images: List["ProductImage"] = Relationship(back_populates="product")
    
class ProductImage(SQLModel, table=True):
    __tablename__ = "product_images" #type: ignore
    # Foreign keys to the two entities it connects.
    product_id: UUID = Field(foreign_key="products.id", primary_key=True)
    image_id: UUID = Field(foreign_key="image_files.id", primary_key=True)
    # --- METADATA SPECIFIC TO THIS CONTEXT ---
    is_primary_crop: bool = Field(default=False)
    # --- Relationships ---
    product: "Product" = Relationship(back_populates="product_images")
    image: "ImageFile" = Relationship() # One-way is fine here.

    
    