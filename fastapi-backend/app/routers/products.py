from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.dependencies.rbac import require_role

from app.models.product import Product
from app.models.user import User
from app.models.review import Review
from app.models.product_view import ProductView

from app.schemas.review import ProductReviewsResponse

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
    products = (
        db.query(Product)
        .filter(Product.category == category)
        .all()
    )

    return products


# --------------------------------
# GET PRODUCT REVIEWS
# --------------------------------

@router.get(
    "/{product_id}/reviews",
    response_model=ProductReviewsResponse
)
def get_product_reviews(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    approved_reviews_query = (
        db.query(Review)
        .filter(
            Review.product_id == product_id,
            Review.status == "approved"
        )
    )

    total_reviews = approved_reviews_query.count()

    average_rating = (
        approved_reviews_query
        .with_entities(
            func.avg(Review.rating)
        )
        .scalar()
    )

    reviews = (
        approved_reviews_query
        .order_by(
            Review.created_at.desc()
        )
        .all()
    )

    top_reviews = (
        approved_reviews_query
        .order_by(
            Review.rating.desc(),
            Review.created_at.desc()
        )
        .limit(3)
        .all()
    )

    return {
        "product_id": product_id,
        "average_rating": (
            round(float(average_rating), 2)
            if average_rating is not None
            else 0.0
        ),
        "total_reviews": total_reviews,
        "reviews": reviews,
        "top_reviews": top_reviews
    }


# --------------------------------
# GET SIMILAR PRODUCTS
# --------------------------------

@router.get(
    "/{product_id}/similar",
    response_model=list[ProductResponse]
)
def get_similar_products(
    product_id: int,
    db: Session = Depends(get_db)
):
    # Get the original product
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Find products in the same category
    # Exclude the current product
    similar_products = (
        db.query(Product)
        .filter(
            Product.category == product.category,
            Product.id != product.id,
            Product.stock > 0
        )
        .order_by(
            Product.popularity.desc()
        )
        .limit(10)
        .all()
    )

    return similar_products

# --------------------------------
# GET TRENDING PRODUCTS
# --------------------------------

@router.get(
    "/trending",
    response_model=list[ProductResponse]
)
def get_trending_products(
    db: Session = Depends(get_db)
):
    trending_products = (
        db.query(Product)
        .filter(
            Product.stock > 0
        )
        .order_by(
            Product.popularity.desc()
        )
        .limit(10)
        .all()
    )

    return trending_products

# --------------------------------
# GET SINGLE PRODUCT + TRACK VIEW
# --------------------------------

@router.get(
    "/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer"))
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Save user browsing history
    product_view = ProductView(
        user_id=current_user.id,
        product_id=product.id
    )

    db.add(product_view)

    # Increase product popularity
    product.popularity += 1

    db.commit()
    db.refresh(product)

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
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

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
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

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