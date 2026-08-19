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
        category=product_data.category,
        price=product_data.price,
        stock=product_data.stock,
        popularity=product_data.popularity,
        images=product_data.images
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


# --------------------------------
# GET ALL PRODUCTS + FILTERS
# --------------------------------

@router.get(
    "/",
    response_model=list[ProductResponse]
)
def get_products(
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_popularity: int | None = None,
    in_stock: bool | None = None,
    db: Session = Depends(get_db)
):

    query = db.query(Product)

    # Category filter
    if category:
        query = query.filter(
            Product.category == category
        )

    # Minimum price
    if min_price is not None:
        query = query.filter(
            Product.price >= min_price
        )

    # Maximum price
    if max_price is not None:
        query = query.filter(
            Product.price <= max_price
        )

    # Popularity filter
    if min_popularity is not None:
        query = query.filter(
            Product.popularity >= min_popularity
        )

    # Stock availability
    if in_stock is True:
        query = query.filter(
            Product.stock > 0
        )

    if in_stock is False:
        query = query.filter(
            Product.stock == 0
        )

    return query.all()

# --------------------------------
# GET PRODUCTS BY CATEGORY
# --------------------------------

@router.get(
    "/category/{category}",
    response_model=list[ProductResponse]
)
def get_products_by_category(
    category: str,
    db: Session = Depends(get_db)
):
    products = db.query(Product).filter(
        Product.category == category
    ).all()

    return products

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