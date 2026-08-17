from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.rbac import require_role
from app.models.cart import Cart
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
)

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


@router.post(
    "",
    response_model=CartItemResponse,
    status_code=201
)
def add_to_cart(
    cart_data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer"))
):
    # Check product exists
    product = db.query(Product).filter(
        Product.id == cart_data.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check stock
    if cart_data.quantity > product.stock:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    # Check if already in cart
    existing_item = db.query(Cart).filter(
        Cart.user_id == current_user.id,
        Cart.product_id == cart_data.product_id
    ).first()

    if existing_item:
        existing_item.quantity += cart_data.quantity
        db.commit()
        db.refresh(existing_item)

        return existing_item

    # Create new cart item
    cart_item = Cart(
        user_id=current_user.id,
        product_id=cart_data.product_id,
        quantity=cart_data.quantity
    )

    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    return cart_item


@router.get(
    "",
    response_model=list[CartItemResponse]
)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer"))
):
    return db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).all()


@router.put(
    "/{product_id}",
    response_model=CartItemResponse
)
def update_cart(
    product_id: int,
    cart_data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer"))
):
    cart_item = db.query(Cart).filter(
        Cart.user_id == current_user.id,
        Cart.product_id == product_id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Product not found in cart"
        )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if cart_data.quantity > product.stock:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    cart_item.quantity = cart_data.quantity

    db.commit()
    db.refresh(cart_item)

    return cart_item


@router.delete("/{product_id}")
def remove_from_cart(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer"))
):
    cart_item = db.query(Cart).filter(
        Cart.user_id == current_user.id,
        Cart.product_id == product_id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Product not found in cart"
        )

    db.delete(cart_item)
    db.commit()

    return {
        "message": "Product removed from cart"
    }