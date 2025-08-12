from decimal import Decimal
from uuid import UUID, uuid4
from typing import List, Optional
from pydantic import ConfigDict
from sqlmodel import Column, Numeric, SQLModel, Field, Relationship


class ProductBase(SQLModel):
    # A SKU is a unique alphanumeric code assigned to a specific product to identify and track it for inventory purposes.
    # example: A "Levi's 501 Jeans, Blue, Size 32x32" might have a SKU of LEV501-BL-3232.
    sku: Optional[str] = Field(
        default=None,
        description="Unique SKU code, e.g., LEV501-BL-3232",
        index=True,
        unique=True
    )
    name: str = Field(
        ...,
        description="Product name, e.g., Levi's 501 Jeans",
        index=True
    )
    description: Optional[str] = Field(
        default=None,
        description="Product description, e.g., Blue denim jeans, size 32x32"
    )
    price: Decimal = Field(
        sa_column=Column(Numeric(10, 2))
    )


class ProductCreate(ProductBase):
    pass




class ProductUpdate(SQLModel):
    sku: str | None = Field(
        default=None, description="Unique SKU code, e.g., LEV501-BL-3232"
    )
    name: str | None = Field(
        default=None, description="Product name, e.g., Levi's 501 Jeans"
    )
    description: str | None = Field(
        default=None,
        description="Product description, e.g., Blue denim jeans, size 32x32",
    )
    price: Decimal | None = Field(
        default=None,
        description="Product price, e.g., 99.99",
    )


class Product(ProductBase, table=True):
    __tablename__ = "products"  # type: ignore
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # adapted relationshipt
    product_images: List["ProductImage"] = Relationship(back_populates="product")



#this here needs to be deleted in cascade, within the image img itself and the image object on the db
class ProductImage(SQLModel, table=True):
    __tablename__ = "product_images"  # type: ignore
    # Foreign keys to the two entities it connects.
    product_id: UUID = Field(foreign_key="products.id", primary_key=True)
    image_id: UUID = Field(foreign_key="images.id", primary_key=True)
    # --- METADATA SPECIFIC TO THIS CONTEXT ---
    is_primary_crop: bool = Field(default=False)
    # --- Relationships ---
    product: "Product" = Relationship(back_populates="product_images")
