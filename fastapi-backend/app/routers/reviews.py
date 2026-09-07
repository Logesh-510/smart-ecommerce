from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.review import Review
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.user import User

from app.schemas.review import ReviewCreate, ReviewResponse

from app.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED
)
def create_review(
    request: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Check whether product exists
    product = (
        db.query(Product)
        .filter(Product.id == request.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # 2. Check whether user already reviewed this product
    existing_review = (
        db.query(Review)
        .filter(
            Review.user_id == current_user.id,
            Review.product_id == request.product_id
        )
        .first()
    )

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product"
        )

    # 3. Check whether user purchased and received this product
    completed_purchase = (
        db.query(Order)
        .join(
            OrderItem,
            OrderItem.order_id == Order.id
        )
        .filter(
            Order.user_id == current_user.id,
            Order.status == "delivered",
            OrderItem.product_id == request.product_id
        )
        .first()
    )

    if not completed_purchase:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can review a product only after purchasing and receiving it"
        )

    # 4. Create review
    review = Review(
        user_id=current_user.id,
        product_id=request.product_id,
        rating=request.rating,
        comment=request.comment,
        status="pending"
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review