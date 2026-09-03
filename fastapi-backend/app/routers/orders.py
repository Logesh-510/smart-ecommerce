from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cart import Cart
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.user import User
from app.models.return_request import ReturnRequest

from app.routers.notifications import create_notification
from app.routers.websocket import manager

from app.services.email import send_email

from app.schemas.order import OrderResponse
from app.schemas.return_request import ReturnRequestCreate
from app.dependencies.auth import get_current_user
from app.dependencies.rbac import require_role


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


class OrderStatusUpdate(BaseModel):
    status: str


# ---------------------------------------------------------
# Create Order
# ---------------------------------------------------------
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

    # 8. Reload order
    db.refresh(order)

    # 9. Create in-app notification
    create_notification(
        db,
        current_user.id,
        "order_confirmation",
        f"Your order #{order.id} has been placed successfully."
    )

    # 10. Send order confirmation email
    send_email(
        current_user.email,
        f"Order #{order.id} Confirmation",
        (
            f"Hello {current_user.name},\n\n"
            f"Your order #{order.id} has been placed successfully.\n"
            f"Order total: ₹{order.total_amount}\n"
            f"Order status: {order.status}\n\n"
            "Thank you for shopping with Smart E-Commerce!"
        )
    )

    return order


# ---------------------------------------------------------
# Get My Orders
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Get All Orders - Admin
# ---------------------------------------------------------
# IMPORTANT:
# This route must be declared before /{order_id}/return
# and /{order_id}/status
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


# ---------------------------------------------------------
# Get Order By ID
# ---------------------------------------------------------
@router.get(
    "/{order_id}",
    response_model=OrderResponse
)
def get_order_by_id(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return order


# ---------------------------------------------------------
# Request Return
# ---------------------------------------------------------
@router.post(
    "/{order_id}/return"
)
def request_return(
    order_id: int,
    request: ReturnRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Find the customer's order
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # 2. Return is allowed only for delivered orders
    if order.status != "delivered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Return can only be requested for delivered orders"
        )

    # 3. Make sure delivery date exists
    if not order.delivered_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery date is not available for this order"
        )

    # 4. Check the 7-day return window
    now = datetime.now(timezone.utc)

    delivered_at = order.delivered_at

    # Handle old database timestamps without timezone information
    if delivered_at.tzinfo is None:
        delivered_at = delivered_at.replace(tzinfo=timezone.utc)

    return_deadline = delivered_at + timedelta(days=7)

    if now > return_deadline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Return window has expired. "
                "Returns are allowed within 7 days of delivery."
            )
        )

    # 5. Prevent duplicate pending return requests
    existing_request = (
        db.query(ReturnRequest)
        .filter(
            ReturnRequest.order_id == order.id,
            ReturnRequest.status == "pending"
        )
        .first()
    )

    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A return request is already pending for this order"
        )

    # 6. Create return request
    return_request = ReturnRequest(
        order_id=order.id,
        user_id=current_user.id,
        reason=request.reason,
        comment=request.comment,
        status="pending"
    )

    db.add(return_request)

    # 7. Update order status
    order.status = "return_requested"

    # 8. Save changes
    db.commit()
    db.refresh(return_request)

    return {
        "message": "Return request submitted successfully",
        "return_request_id": return_request.id,
        "order_id": return_request.order_id,
        "reason": return_request.reason,
        "comment": return_request.comment,
        "status": return_request.status,
        "created_at": return_request.created_at
    }


# ---------------------------------------------------------
# Update Order Status - Admin
# ---------------------------------------------------------
@router.put(
    "/{order_id}/status",
    response_model=OrderResponse
)
async def update_order_status(
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
        "cancelled",
        "return_requested"
    }

    # 1. Validate status
    if request.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid order status. "
                f"Allowed values: {', '.join(sorted(allowed_statuses))}"
            )
        )

    # 2. Find order
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

    # 3. Update order status
    previous_status = order.status
    order.status = request.status

    if request.status == "delivered" and previous_status != "delivered":
        order.delivered_at = datetime.now(timezone.utc)

    message = (
        f"Your order #{order.id} status has been updated "
        f"to {order.status}."
    )

    # 4. Create in-app notification
    create_notification(
        db,
        order.user_id,
        "order_status",
        message
    )

    # 5. Find customer
    customer = (
        db.query(User)
        .filter(User.id == order.user_id)
        .first()
    )

    # 6. Send email notification
    if customer:
        send_email(
            customer.email,
            f"Order #{order.id} Status Update",
            message
        )

    # 7. WebSocket real-time notification
    await manager.send_personal_message(
        order.user_id,
        {
            "event": "order_status_updated",
            "order_id": order.id,
            "status": order.status,
            "message": message
        }
    )

    # 8. Commit database changes
    db.commit()
    db.refresh(order)

    return order