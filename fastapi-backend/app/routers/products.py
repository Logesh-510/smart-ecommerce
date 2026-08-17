from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.rbac import require_role
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# --------------------------------
# CREATE PRODUCT - ADMIN ONLY
# --------------------------------

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=201
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):

    product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock=product_data.stock,
        images=product_data.images
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


# --------------------------------
# GET ALL PRODUCTS
# --------------------------------

@router.get(
    "/",
    response_model=list[ProductResponse]
)
def get_products(
    db: Session = Depends(get_db)
):

    return db.query(Product).all()


# --------------------------------
# GET SINGLE PRODUCT
# --------------------------------

@router.get(
    "/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# --------------------------------
# UPDATE PRODUCT - ADMIN ONLY
# --------------------------------

@router.put(
    "/{product_id}",
    response_model=ProductResponse
)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    update_data = product_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return product


# --------------------------------
# DELETE PRODUCT - ADMIN ONLY
# --------------------------------

@router.delete(
    "/{product_id}"
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }