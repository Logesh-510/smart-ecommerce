from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.user import User
from app.routers.notifications import create_notification
from app.schemas.order import OrderResponse
from app.dependencies.auth import get_current_user
from app.dependencies.rbac import require_role


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


class OrderStatusUpdate(BaseModel):
    status: str


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED
)
def create_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Get user's cart
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == current_user.id)
        .first()
    )

    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    cart_items = cart.items
    
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # 2. Create order
    order = Order(
        user_id=current_user.id,
        total_amount=0,
        status="pending"
    )

    db.add(order)
    db.flush()

    total_amount = 0
    order_items = []

    # 3. Convert cart items into order items
    for cart_item in cart_items:

        product = (
            db.query(Product)
            .filter(Product.id == cart_item.product_id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {cart_item.product_id} not found"
            )

        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {product.name}"
            )

        item_price = float(product.price)
        item_total = item_price * cart_item.quantity

        total_amount += item_total

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=cart_item.quantity,
            price=product.price
        )

        order_items.append(order_item)

        # Reduce stock
        product.stock -= cart_item.quantity

    # 4. Set total
    order.total_amount = total_amount

    # 5. Add order items
    db.add_all(order_items)

    # 6. Clear cart
    for cart_item in cart_items:
        db.delete(cart_item)

    # 7. Save everything
    db.commit()

    # 8. Reload order with items
    db.refresh(order)

    return order


@router.get(
    "",
    response_model=list[OrderResponse]
)
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders


# IMPORTANT:
# This route must be declared before /{order_id}/status
@router.get(
    "/admin",
    response_model=list[OrderResponse]
)
def get_all_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders


@router.put(
    "/{order_id}/status",
    response_model=OrderResponse
)
def update_order_status(
    order_id: int,
    request: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    allowed_statuses = {
        "pending",
        "confirmed",
        "shipped",
        "delivered",
        "cancelled"
    }

    if request.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid order status. "
                f"Allowed values: {', '.join(sorted(allowed_statuses))}"
            )
        )

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    order.status = request.status

    create_notification(
        db,
        order.user_id,
        "order_status",
        f"Your order #{order.id} status has been updated to {order.status}."
    )

    db.commit()
    db.refresh(order)

    return order