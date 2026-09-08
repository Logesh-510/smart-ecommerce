from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.product import Product
from app.services.recommendation_service import get_recommendations


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/{user_id}")
def get_user_recommendations(
    user_id: int,
    db: Session = Depends(get_db)
):
    # Check whether user exists
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    products = get_recommendations(
        db=db,
        user_id=user_id,
        limit=10
    )

    return {
        "user_id": user_id,
        "recommendations": products
    }