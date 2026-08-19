from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.rbac import require_role
from app.models.cart import Cart, CartItem
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

    # Get existing cart or create one
    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        db.flush()

    # Check whether product is already in cart
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == cart_data.product_id
    ).first()

    if existing_item:
        new_quantity = existing_item.quantity + cart_data.quantity

        if new_quantity > product.stock:
            raise HTTPException(
                status_code=400,
                detail="Insufficient stock"
            )

        existing_item.quantity = new_quantity
        db.commit()
        db.refresh(existing_item)

        return {
            "id": existing_item.id,
            "user_id": current_user.id,
            "product_id": existing_item.product_id,
            "quantity": existing_item.quantity
        }

    # Create new cart item
    cart_item = CartItem(
        cart_id=cart.id,
        product_id=cart_data.product_id,
        quantity=cart_data.quantity
    )

    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)

    return {
        "id": cart_item.id,
        "user_id": current_user.id,
        "product_id": cart_item.product_id,
        "quantity": cart_item.quantity
    }


@router.get(
    "",
    response_model=list[CartItemResponse]
)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer"))
):
    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        return []

    items = db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).all()

    return [
        {
            "id": item.id,
            "user_id": current_user.id,
            "product_id": item.product_id,
            "quantity": item.quantity
        }
        for item in items
    ]


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
    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    cart_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Product not found in cart"
        )

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if cart_data.quantity > product.stock:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    cart_item.quantity = cart_data.quantity

    db.commit()
    db.refresh(cart_item)

    return {
        "id": cart_item.id,
        "user_id": current_user.id,
        "product_id": cart_item.product_id,
        "quantity": cart_item.quantity
    }


@router.delete("/{product_id}")
def remove_from_cart(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer"))
):
    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    cart_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id
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