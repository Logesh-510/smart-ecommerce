import stripe

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

from app.models.payment import Payment
from app.models.order import Order
from app.models.user import User

from app.routers.notifications import create_notification
from app.routers.websocket import manager

from app.services.email import send_email

from app.dependencies.auth import get_current_user

from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentStatusUpdate
)


stripe.api_key = settings.STRIPE_SECRET_KEY


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


# =========================================================
# Create Payment
# =========================================================
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
    order = (
        db.query(Order)
        .filter(
            Order.id == payment_data.order_id,
            Order.user_id == current_user.id
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    existing_payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .first()
    )

    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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


# =========================================================
# Get My Payments
# =========================================================
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


# =========================================================
# Update Payment Status - Admin
# =========================================================
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    allowed_statuses = {
        "pending",
        "completed",
        "failed"
    }

    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid payment status. "
                f"Allowed values: {', '.join(sorted(allowed_statuses))}"
            )
        )

    payment.status = status_data.status

    db.commit()
    db.refresh(payment)

    return payment


# =========================================================
# Stripe Checkout
# =========================================================
@router.post("/checkout")
def create_checkout_session(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
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

    if order.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pay for a cancelled order"
        )

    # -----------------------------------------------------
    # Stripe Checkout line item
    # -----------------------------------------------------
    line_items = [
        {
            "price_data": {
                "currency": "inr",
                "product_data": {
                    "name": f"Order #{order.id}"
                },
                "unit_amount": int(
                    float(order.total_amount) * 100
                ),
            },
            "quantity": 1,
        }
    ]

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",

            # Metadata is also attached to the PaymentIntent.
            payment_intent_data={
                "metadata": {
                    "order_id": str(order.id),
                    "user_id": str(current_user.id),
                }
            },

            success_url=(
                "http://127.0.0.1:8000/payments/success"
                "?session_id={CHECKOUT_SESSION_ID}"
            ),

            cancel_url=(
                "http://127.0.0.1:8000/payments/cancel"
            ),

            # Metadata attached to Checkout Session.
            metadata={
                "order_id": str(order.id),
                "user_id": str(current_user.id),
            }
        )

        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
            "order_id": order.id,
        }

    except stripe.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =========================================================
# Payment Success
# =========================================================
@router.get("/success")
def payment_success():
    return {
        "message": "Payment completed successfully"
    }


# =========================================================
# Payment Cancel
# =========================================================
@router.get("/cancel")
def payment_cancel():
    return {
        "message": "Payment was cancelled"
    }


# =========================================================
# Stripe Webhook
# =========================================================
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.body()

    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )

    # -----------------------------------------------------
    # Verify Stripe webhook signature
    # -----------------------------------------------------
    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET
        )

        print(
            "WEBHOOK EVENT TYPE:",
            event["type"]
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload"
        )

    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe signature"
        )

    # =====================================================
    # Handle successful Checkout
    # =====================================================
    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        if hasattr(session, "to_dict"):
            session_data = session.to_dict()
        else:
            session_data = dict(session)

        metadata = session_data.get("metadata") or {}

        order_id = metadata.get("order_id")
        user_id = metadata.get("user_id")

        print("Stripe webhook received")
        print("Session ID:", session_data.get("id"))
        print("Metadata:", metadata)
        print("Order ID:", order_id)

        if not order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order ID missing from Stripe metadata"
            )

        order = (
            db.query(Order)
            .filter(Order.id == int(order_id))
            .first()
        )

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        # -------------------------------------------------
        # Find existing payment
        # -------------------------------------------------
        payment = (
            db.query(Payment)
            .filter(Payment.order_id == order.id)
            .first()
        )

        payment_intent_id = session_data.get(
            "payment_intent"
        )

        # -------------------------------------------------
        # Update existing payment
        # -------------------------------------------------
        if payment:

            payment.status = "completed"
            payment.payment_method = "stripe"

            if payment_intent_id:
                payment.transaction_id = payment_intent_id

        # -------------------------------------------------
        # Create payment if it does not exist
        # -------------------------------------------------
        else:

            payment = Payment(
                order_id=order.id,
                amount=order.total_amount,
                payment_method="stripe",
                status="completed",
                transaction_id=payment_intent_id
            )

            db.add(payment)

        # -------------------------------------------------
        # Update order
        # -------------------------------------------------
        order.status = "confirmed"
        order.payment_status = "paid"

        # -------------------------------------------------
        # Find customer
        # -------------------------------------------------
        user = (
            db.query(User)
            .filter(User.id == order.user_id)
            .first()
        )

        # -------------------------------------------------
        # Create notification
        # -------------------------------------------------
        create_notification(
            db,
            order.user_id,
            "payment_success",
            f"Payment successful for order #{order.id}."
        )

        # -------------------------------------------------
        # Send email
        # -------------------------------------------------
        if user:
            send_email(
                user.email,
                f"Payment Successful - Order #{order.id}",
                (
                    f"Payment for your order #{order.id} "
                    "was successful.\n\n"
                    f"Amount: ₹{order.total_amount}\n"
                    "Order status: confirmed"
                )
            )

        # -------------------------------------------------
        # WebSocket notification
        # -------------------------------------------------
        await manager.send_personal_message(
            order.user_id,
            {
                "event": "payment_success",
                "order_id": order.id,
                "status": "paid",
                "message": (
                    f"Payment successful for order #{order.id}."
                )
            }
        )

        db.commit()
        db.refresh(order)

        print("ORDER UPDATED SUCCESSFULLY")
        print("Order ID:", order.id)
        print("Order Status:", order.status)
        print("Payment Status:", order.payment_status)

    # =====================================================
    # Handle failed PaymentIntent
    # =====================================================
    elif event["type"] == "payment_intent.payment_failed":

        payment_intent = event["data"]["object"]

        if hasattr(payment_intent, "to_dict"):
            payment_data = payment_intent.to_dict()
        else:
            payment_data = dict(payment_intent)

        metadata = payment_data.get("metadata") or {}

        order_id = metadata.get("order_id")
        user_id = metadata.get("user_id")

        payment_intent_id = payment_data.get("id")

        print("Stripe payment failed")
        print("Payment Intent:", payment_intent_id)
        print("Metadata:", metadata)
        print("Order ID:", order_id)

        # -------------------------------------------------
        # Metadata is required to identify the order.
        # -------------------------------------------------
        if order_id:

            order = (
                db.query(Order)
                .filter(Order.id == int(order_id))
                .first()
            )

            if order:

                # -----------------------------------------
                # Find existing payment
                # -----------------------------------------
                payment = (
                    db.query(Payment)
                    .filter(Payment.order_id == order.id)
                    .first()
                )

                # -----------------------------------------
                # Create payment if it doesn't exist
                # -----------------------------------------
                if not payment:

                    payment = Payment(
                        order_id=order.id,
                        amount=order.total_amount,
                        payment_method="stripe",
                        status="failed",
                        transaction_id=payment_intent_id
                    )

                    db.add(payment)

                else:

                    payment.status = "failed"
                    payment.payment_method = "stripe"

                    if payment_intent_id:
                        payment.transaction_id = (
                            payment_intent_id
                        )

                # -----------------------------------------
                # Update order payment status
                # -----------------------------------------
                order.payment_status = "failed"

                # -----------------------------------------
                # Find customer
                # -----------------------------------------
                user = (
                    db.query(User)
                    .filter(User.id == order.user_id)
                    .first()
                )

                # -----------------------------------------
                # Create notification
                # -----------------------------------------
                create_notification(
                    db,
                    order.user_id,
                    "payment_failed",
                    f"Payment failed for order #{order.id}."
                )

                # -----------------------------------------
                # Send email
                # -----------------------------------------
                if user:
                    send_email(
                        user.email,
                        f"Payment Failed - Order #{order.id}",
                        (
                            f"Payment for your order #{order.id} "
                            "failed.\n\n"
                            f"Amount: ₹{order.total_amount}\n"
                            "Please try the payment again."
                        )
                    )

                # -----------------------------------------
                # WebSocket notification
                # -----------------------------------------
                await manager.send_personal_message(
                    order.user_id,
                    {
                        "event": "payment_failed",
                        "order_id": order.id,
                        "status": "failed",
                        "message": (
                            f"Payment failed for order #{order.id}."
                        )
                    }
                )

                db.commit()
                db.refresh(order)

                print(
                    "PAYMENT FAILURE PROCESSED SUCCESSFULLY"
                )
                print(
                    "Order ID:",
                    order.id
                )
                print(
                    "Order Payment Status:",
                    order.payment_status
                )
                print(
                    "Payment Status:",
                    payment.status
                )

    # =====================================================
    # Return successful webhook response
    # =====================================================
    return {
        "message": "Webhook processed successfully",
        "event_type": event["type"]
    }
