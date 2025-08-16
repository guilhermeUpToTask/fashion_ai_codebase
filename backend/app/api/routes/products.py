from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Query, status
from sqlmodel import col, delete, select

from api.deps import SessionDep, CurrentUser
from models.job import Job
from core import storage
from models.image import BUCKET_NAME_TO_S3, BucketName, ImageFile
from models.product import ProductCreate, ProductImage, ProductUpdate
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


@router.get("/", response_model=List[Product])
async def list_products(
    session: SessionDep,
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max number of items to return"),
):
    """
    Retrieve a list of products with pagination.
    """
    results = session.exec(select(Product).offset(offset).limit(limit)).all()

    return results


@router.get(
    "/{product_id}",
    response_model=Product,
    responses={404: {"description": "Product not found"}},
)
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


@router.put(
    "/{product_id}",
    response_model=Product,
    responses={404: {"description": "Product not found"}},
)
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

#TODO: its needs to delete from the vector db aswell
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Product not found"}},
)
async def delete_product(
    product_id: UUID,
    session: SessionDep,
) -> None:
    """
    Delete a product along with its images. Atomic: if S3 deletion fails, DB changes are rolled back. Requires authenticated user.
    """
    real_bucket = BUCKET_NAME_TO_S3[BucketName.PRODUCT]

    with session.begin():

        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        img_ids: List[UUID] = [prod_img.image_id for prod_img in product.product_images]
        if not img_ids:
            session.delete(product)
            return

        imgs = session.exec(
            select(ImageFile).where(col(ImageFile.id).in_(img_ids))
        ).all()
        imgs_filenames = [img.filename for img in imgs]

        session.execute(delete(Job).where(col(Job.input_product_id).in_([product_id])))
        session.delete(product)

        storage.delete_files_from_s3_batch(bucket_name=real_bucket, keys=imgs_filenames)
        # i use execute here, because current version of sqlmodel does not yet aplied this patch:https://github.com/fastapi/sqlmodel/pull/1342
        session.execute(delete(ImageFile).where(col(ImageFile.id).in_(img_ids)))

    return


@router.get(
    "/images/",
    response_model=List[ProductImage],
)
async def list_products_images(
    session: SessionDep,
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max number of items to return"),
):
    """
    Retrieve a list of product images with pagination.
    """
    results = session.exec(select(ProductImage).offset(offset).limit(limit)).all()

    return results
