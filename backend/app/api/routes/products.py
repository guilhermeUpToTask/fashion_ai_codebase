from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlmodel import select

from api.deps import SessionDep, CurrentUser
from models.product import ProductCreate, ProductUpdate
from models import Product

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    session: SessionDep,
):
    """
    Create a new product. Requires authenticated user.
    """
    product = Product(**product_in.model_dump())

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.get("/")
async def list_products(
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Retrieve a list of products with pagination.
    """
    results = session.exec(select(Product).offset(offset).limit(limit)).all()

    return list(results)


@router.get("/{product_id}")
async def get_product(
    session: SessionDep,
    product_id: UUID = Path(..., description="ID of the product to retrieve"),
):
    """
    Get a single product by its ID.
    """
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return product


@router.put("/{product_id}")
async def update_product(
    product_id: UUID,
    product_in: ProductUpdate,
    session: SessionDep,
):
    """
    Update an existing product. Requires authenticated user.
    """
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    product_data = product_in.model_dump(exclude_unset=True)
    for key, value in product_data.items():
        setattr(product, key, value)
        
    session.add(product)
    session.commit()
    session.refresh(product)

    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    session: SessionDep,
) -> None:
    """
    Delete a product. Requires authenticated user.
    """
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    session.delete(product)
    session.commit()
    return None
