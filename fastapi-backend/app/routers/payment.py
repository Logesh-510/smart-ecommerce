from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.payment import Payment
from app.models.order import Order
from app.dependencies.auth import get_current_user
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentStatusUpdate
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    order = db.query(Order).filter(
        Order.id == payment_data.order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    existing_payment = db.query(Payment).filter(
        Payment.order_id == order.id
    ).first()

    if existing_payment:
        raise HTTPException(
            status_code=400,
            detail="Payment already exists for this order"
        )

    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        payment_method=payment_data.payment_method,
        status="pending"
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment
@router.get(
    "/",
    response_model=list[PaymentResponse]
)
def get_my_payments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    payments = (
        db.query(Payment)
        .join(Order, Payment.order_id == Order.id)
        .filter(Order.user_id == current_user.id)
        .all()
    )

    return payments
@router.put(
    "/{payment_id}/status",
    response_model=PaymentResponse
)
def update_payment_status(
    payment_id: int,
    status_data: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    payment = db.query(Payment).filter(
        Payment.id == payment_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    allowed_statuses = ["pending", "completed", "failed"]

    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment status"
        )

    payment.status = status_data.status

    db.commit()
    db.refresh(payment)

    return payment