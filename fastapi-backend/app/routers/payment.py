import stripe

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

from app.models.payment import Payment
from app.models.order import Order
from app.models.user import User
from app.models.webhook_event import WebhookEvent

from app.routers.notifications import create_notification
from app.routers.websocket import manager

from app.services.email import send_email

from app.dependencies.auth import get_current_user

from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentStatusUpdate,
)


# =========================================================
# Stripe Configuration
# =========================================================

stripe.api_key = settings.STRIPE_SECRET_KEY


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


# =========================================================
# Helper Functions - Stripe Objects
# =========================================================

def stripe_object_to_dict(obj):
    """
    Convert a StripeObject into a normal Python dictionary.
    """

    if obj is None:
        return {}

    try:
        return obj.to_dict()
    except AttributeError:
        try:
            return dict(obj)
        except Exception:
            return {}


def get_stripe_metadata(obj):
    """
    Safely extract Stripe metadata as a normal dictionary.
    """

    metadata = getattr(obj, "metadata", None)

    if metadata is None:
        return {}

    return stripe_object_to_dict(metadata)


# =========================================================
# Create Payment
# =========================================================

@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(
            Order.id == payment_data.order_id,
            Order.user_id == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create payment for a cancelled order",
        )

    if order.payment_status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid",
        )

    existing_payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .first()
    )

    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment already exists for this order",
        )

    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        payment_method=payment_data.payment_method,
        status="pending",
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
    response_model=list[PaymentResponse],
)
def get_my_payments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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
    response_model=PaymentResponse,
)
def update_payment_status(
    payment_id: int,
    status_data: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    allowed_statuses = {
        "pending",
        "completed",
        "failed",
    }

    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid payment status. "
                f"Allowed values: {', '.join(sorted(allowed_statuses))}"
            ),
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
    current_user=Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot pay for a cancelled order",
        )

    if order.payment_status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid",
        )

    # -----------------------------------------------------
    # Stripe Checkout Line Item
    # -----------------------------------------------------

    line_items = [
        {
            "price_data": {
                "currency": "inr",
                "product_data": {
                    "name": f"Order #{order.id}",
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

            # Metadata attached to PaymentIntent
            payment_intent_data={
                "metadata": {
                    "order_id": str(order.id),
                    "user_id": str(current_user.id),
                }
            },

            # Success URL
            success_url=(
                "http://127.0.0.1:8000/payments/success"
                "?session_id={CHECKOUT_SESSION_ID}"
            ),

            # Cancel URL
            cancel_url=(
                "http://127.0.0.1:8000/payments/cancel"
            ),

            # Metadata attached to Checkout Session
            metadata={
                "order_id": str(order.id),
                "user_id": str(current_user.id),
            },
        )

        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
            "order_id": order.id,
        }

    except stripe.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =========================================================
# Payment Success
# =========================================================

@router.get("/success")
def payment_success(
    session_id: str | None = None,
):
    return {
        "message": "Payment completed successfully",
        "session_id": session_id,
    }


# =========================================================
# Payment Cancel
# =========================================================

@router.get("/cancel")
def payment_cancel():
    return {
        "message": "Payment was cancelled",
    }


# =========================================================
# Process Successful Payment
# =========================================================

async def process_successful_payment(
    order_id: int,
    payment_intent_id: str | None,
    db: Session,
):
    print("========================================")
    print("PROCESSING SUCCESSFUL PAYMENT")
    print("ORDER ID:", order_id)
    print("PAYMENT INTENT:", payment_intent_id)
    print("========================================")

    # -----------------------------------------------------
    # Find Order
    # -----------------------------------------------------

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        print("ERROR: Order not found:", order_id)
        return

    print("ORDER FOUND:", order.id)

    # -----------------------------------------------------
    # Find Payment
    # -----------------------------------------------------

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .first()
    )

    # -----------------------------------------------------
    # Already Paid
    # -----------------------------------------------------

    if (
        order.payment_status == "paid"
        and payment is not None
        and payment.status == "completed"
    ):
        print("ORDER ALREADY PROCESSED")
        print("ORDER ID:", order.id)
        return

    # -----------------------------------------------------
    # Create / Update Payment
    # -----------------------------------------------------

    if payment:
        print("EXISTING PAYMENT FOUND:", payment.id)

        payment.status = "completed"
        payment.payment_method = "stripe"

        if payment_intent_id:
            payment.transaction_id = payment_intent_id

    else:
        print("CREATING NEW PAYMENT")

        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            payment_method="stripe",
            status="completed",
            transaction_id=payment_intent_id,
        )

        db.add(payment)

    # -----------------------------------------------------
    # Update Order
    # -----------------------------------------------------

    order.status = "confirmed"
    order.payment_status = "paid"

    # -----------------------------------------------------
    # Find User
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(User.id == order.user_id)
        .first()
    )

    # -----------------------------------------------------
    # Commit Database Changes
    # -----------------------------------------------------

    try:
        db.commit()

        db.refresh(order)
        db.refresh(payment)

    except Exception as e:
        db.rollback()

        print("DATABASE ERROR:", str(e))

        raise

    print("----------------------------------------")
    print("DATABASE UPDATED")
    print("ORDER ID:", order.id)
    print("ORDER STATUS:", order.status)
    print("PAYMENT STATUS:", order.payment_status)
    print("PAYMENT ID:", payment.id)
    print("TRANSACTION ID:", payment.transaction_id)
    print("----------------------------------------")

    # -----------------------------------------------------
    # Notification
    # -----------------------------------------------------

    try:
        create_notification(
            db,
            order.user_id,
            "payment_success",
            f"Payment successful for order #{order.id}.",
        )

        print("NOTIFICATION CREATED")

    except Exception as e:
        print(
            "WARNING: Notification failed:",
            str(e),
        )

    # -----------------------------------------------------
    # Email
    # -----------------------------------------------------

    if user:
        try:
            send_email(
                user.email,
                f"Payment Successful - Order #{order.id}",
                (
                    f"Payment for your order #{order.id} "
                    "was successful.\n\n"
                    f"Amount: ₹{order.total_amount}\n"
                    "Order status: confirmed"
                ),
            )

            print("EMAIL SENT")

        except Exception as e:
            print(
                "WARNING: Email sending failed:",
                str(e),
            )

    # -----------------------------------------------------
    # WebSocket
    # -----------------------------------------------------

    try:
        await manager.send_personal_message(
            order.user_id,
            {
                "event": "payment_success",
                "order_id": order.id,
                "status": "paid",
                "message": (
                    f"Payment successful for order #{order.id}."
                ),
            },
        )

        print("WEBSOCKET MESSAGE SENT")

    except Exception as e:
        print(
            "WARNING: WebSocket notification failed:",
            str(e),
        )

    print("========================================")
    print("PAYMENT SUCCESSFULLY PROCESSED")
    print("========================================")


# =========================================================
# Process Failed Payment
# =========================================================

async def process_failed_payment(
    order_id: int,
    payment_intent_id: str | None,
    db: Session,
):
    print("========================================")
    print("PROCESSING FAILED PAYMENT")
    print("ORDER ID:", order_id)
    print("PAYMENT INTENT:", payment_intent_id)
    print("========================================")

    # -----------------------------------------------------
    # Find Order
    # -----------------------------------------------------

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        print("ERROR: Order not found:", order_id)
        return

    # -----------------------------------------------------
    # Find Payment
    # -----------------------------------------------------

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .first()
    )

    # -----------------------------------------------------
    # Create / Update Payment
    # -----------------------------------------------------

    if payment:
        payment.status = "failed"
        payment.payment_method = "stripe"

        if payment_intent_id:
            payment.transaction_id = payment_intent_id

    else:
        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            payment_method="stripe",
            status="failed",
            transaction_id=payment_intent_id,
        )

        db.add(payment)

    # -----------------------------------------------------
    # Update Order
    # -----------------------------------------------------

    order.payment_status = "failed"

    # -----------------------------------------------------
    # Commit
    # -----------------------------------------------------

    try:
        db.commit()

        db.refresh(order)
        db.refresh(payment)

    except Exception as e:
        db.rollback()

        print("DATABASE ERROR:", str(e))

        raise

    print("----------------------------------------")
    print("FAILED PAYMENT SAVED")
    print("ORDER ID:", order.id)
    print(
        "ORDER PAYMENT STATUS:",
        order.payment_status,
    )
    print(
        "PAYMENT STATUS:",
        payment.status,
    )
    print("----------------------------------------")

    # -----------------------------------------------------
    # Find User
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(User.id == order.user_id)
        .first()
    )

    # -----------------------------------------------------
    # Notification
    # -----------------------------------------------------

    try:
        create_notification(
            db,
            order.user_id,
            "payment_failed",
            f"Payment failed for order #{order.id}.",
        )

        print("FAILURE NOTIFICATION CREATED")

    except Exception as e:
        print(
            "WARNING: Notification failed:",
            str(e),
        )

    # -----------------------------------------------------
    # Email
    # -----------------------------------------------------

    if user:
        try:
            send_email(
                user.email,
                f"Payment Failed - Order #{order.id}",
                (
                    f"Payment for your order #{order.id} "
                    "failed.\n\n"
                    f"Amount: ₹{order.total_amount}\n"
                    "Please try the payment again."
                ),
            )

            print("FAILURE EMAIL SENT")

        except Exception as e:
            print(
                "WARNING: Email sending failed:",
                str(e),
            )

    # -----------------------------------------------------
    # WebSocket
    # -----------------------------------------------------

    try:
        await manager.send_personal_message(
            order.user_id,
            {
                "event": "payment_failed",
                "order_id": order.id,
                "status": "failed",
                "message": (
                    f"Payment failed for order #{order.id}."
                ),
            },
        )

        print("FAILURE WEBSOCKET MESSAGE SENT")

    except Exception as e:
        print(
            "WARNING: WebSocket notification failed:",
            str(e),
        )

    print("========================================")
    print("PAYMENT FAILURE PROCESSED")
    print("========================================")


# =========================================================
# Webhook Event Helper
# =========================================================

def is_webhook_event_processed(
    event_id: str,
    db: Session,
) -> bool:
    """
    Check whether a Stripe webhook event was already processed.
    """

    existing_event = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.id == event_id)
        .first()
    )

    return existing_event is not None


def save_webhook_event(
    event_id: str,
    event_type: str,
    db: Session,
):
    """
    Save a successfully processed Stripe webhook event.
    """

    webhook_event = WebhookEvent(
        id=event_id,
        event_type=event_type,
        processed_at=datetime.now(timezone.utc),
    )

    db.add(webhook_event)

    try:
        db.commit()

        print("----------------------------------------")
        print("WEBHOOK EVENT SAVED")
        print("EVENT ID:", event_id)
        print("EVENT TYPE:", event_type)
        print("----------------------------------------")

    except Exception as e:
        db.rollback()

        print(
            "WARNING: Could not save webhook event:",
            str(e),
        )


# =========================================================
# Stripe Webhook
# =========================================================

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    print("")
    print("========================================")
    print("STRIPE WEBHOOK RECEIVED")
    print("========================================")

    # =====================================================
    # RAW REQUEST BODY
    # =====================================================

    payload = await request.body()

    print("PAYLOAD LENGTH:", len(payload))

    # =====================================================
    # STRIPE SIGNATURE
    # =====================================================

    signature = request.headers.get("stripe-signature")

    if not signature:
        print("ERROR: Missing Stripe signature")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature",
        )

    # =====================================================
    # WEBHOOK SECRET
    # =====================================================

    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    if not webhook_secret:
        print("ERROR: STRIPE_WEBHOOK_SECRET is empty")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe webhook secret is not configured",
        )

    # =====================================================
    # VERIFY STRIPE SIGNATURE
    # =====================================================

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            webhook_secret,
        )

    except ValueError as e:
        print("WEBHOOK PAYLOAD ERROR:", str(e))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        )

    except stripe.error.SignatureVerificationError as e:
        print("WEBHOOK SIGNATURE ERROR:", str(e))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe signature",
        )

    # =====================================================
    # EVENT INFORMATION
    # =====================================================

    event_type = event["type"]
    event_id = event["id"]

    print("----------------------------------------")
    print("WEBHOOK SIGNATURE VERIFIED")
    print("EVENT ID:", event_id)
    print("EVENT TYPE:", event_type)
    print("----------------------------------------")

    # =====================================================
    # IDEMPOTENCY CHECK
    # =====================================================

    if is_webhook_event_processed(
        event_id,
        db,
    ):
        print("----------------------------------------")
        print("DUPLICATE WEBHOOK EVENT")
        print("EVENT ID:", event_id)
        print("EVENT TYPE:", event_type)
        print("EVENT ALREADY PROCESSED")
        print("----------------------------------------")

        return {
            "message": "Webhook event already processed",
            "event_type": event_type,
            "event_id": event_id,
        }

    # =====================================================
    # CHECKOUT SESSION COMPLETED
    # =====================================================

    if event_type == "checkout.session.completed":

        session = event["data"]["object"]

        session_dict = stripe_object_to_dict(session)

        metadata = get_stripe_metadata(session)

        order_id = metadata.get("order_id")

        payment_intent_id = session_dict.get(
            "payment_intent"
        )

        payment_status = session_dict.get(
            "payment_status"
        )

        session_id = session_dict.get("id")

        print("----------------------------------------")
        print("CHECKOUT SESSION COMPLETED")
        print("----------------------------------------")

        print("SESSION ID:", session_id)
        print("METADATA:", metadata)
        print("ORDER ID:", order_id)
        print("PAYMENT INTENT:", payment_intent_id)
        print("PAYMENT STATUS:", payment_status)

        # -------------------------------------------------
        # Missing Order ID
        # -------------------------------------------------

        if not order_id:
            print(
                "ERROR: Order ID missing from checkout metadata"
            )

            return {
                "message": "Missing order_id metadata",
                "event_type": event_type,
                "event_id": event_id,
            }

        # -------------------------------------------------
        # Convert Order ID
        # -------------------------------------------------

        try:
            order_id = int(order_id)

        except (TypeError, ValueError):
            print("ERROR: Invalid order ID:", order_id)

            return {
                "message": "Invalid order_id",
                "event_type": event_type,
                "event_id": event_id,
            }

        # -------------------------------------------------
        # Process only if paid
        # -------------------------------------------------

        if payment_status == "paid":

            await process_successful_payment(
                order_id,
                payment_intent_id,
                db,
            )

        else:

            print(
                "CHECKOUT SESSION COMPLETED "
                "BUT PAYMENT IS NOT PAID"
            )

    # =====================================================
    # PAYMENT INTENT SUCCEEDED
    # =====================================================

    elif event_type == "payment_intent.succeeded":

        payment_intent = event["data"]["object"]

        payment_intent_dict = stripe_object_to_dict(
            payment_intent
        )

        metadata = get_stripe_metadata(
            payment_intent
        )

        order_id = metadata.get("order_id")

        payment_intent_id = payment_intent_dict.get(
            "id"
        )

        print("----------------------------------------")
        print("PAYMENT INTENT SUCCEEDED")
        print("----------------------------------------")

        print(
            "PAYMENT INTENT:",
            payment_intent_id,
        )

        print(
            "METADATA:",
            metadata,
        )

        print(
            "ORDER ID:",
            order_id,
        )

        # -------------------------------------------------
        # Missing Order ID
        # -------------------------------------------------

        if not order_id:

            print(
                "ERROR: Order ID missing from "
                "PaymentIntent metadata"
            )

            return {
                "message": "Missing order_id metadata",
                "event_type": event_type,
                "event_id": event_id,
            }

        # -------------------------------------------------
        # Convert Order ID
        # -------------------------------------------------

        try:

            order_id = int(order_id)

        except (TypeError, ValueError):

            print(
                "ERROR: Invalid order ID:",
                order_id,
            )

            return {
                "message": "Invalid order_id",
                "event_type": event_type,
                "event_id": event_id,
            }

        # -------------------------------------------------
        # Process Successful Payment
        # -------------------------------------------------

        await process_successful_payment(
            order_id,
            payment_intent_id,
            db,
        )

    # =====================================================
    # PAYMENT INTENT FAILED
    # =====================================================

    elif event_type == "payment_intent.payment_failed":

        payment_intent = event["data"]["object"]

        payment_intent_dict = stripe_object_to_dict(
            payment_intent
        )

        metadata = get_stripe_metadata(
            payment_intent
        )

        order_id = metadata.get("order_id")

        payment_intent_id = payment_intent_dict.get(
            "id"
        )

        print("----------------------------------------")
        print("PAYMENT INTENT FAILED")
        print("----------------------------------------")

        print(
            "PAYMENT INTENT:",
            payment_intent_id,
        )

        print(
            "METADATA:",
            metadata,
        )

        print(
            "ORDER ID:",
            order_id,
        )

        # -------------------------------------------------
        # Process Failure
        # -------------------------------------------------

        if order_id:

            try:

                order_id = int(order_id)

            except (TypeError, ValueError):

                print(
                    "ERROR: Invalid order ID:",
                    order_id,
                )

                order_id = None

            if order_id:

                await process_failed_payment(
                    order_id,
                    payment_intent_id,
                    db,
                )

        else:

            print(
                "WARNING: Missing order_id metadata "
                "for failed PaymentIntent"
            )

    # =====================================================
    # CHARGE SUCCEEDED
    # =====================================================

    elif event_type == "charge.succeeded":

        print(
            "Charge succeeded - payment will be "
            "processed through payment_intent.succeeded"
        )

    # =====================================================
    # CHARGE UPDATED
    # =====================================================

    elif event_type == "charge.updated":

        print(
            "Charge updated - no database action required"
        )

    # =====================================================
    # PAYMENT INTENT CREATED
    # =====================================================

    elif event_type == "payment_intent.created":

        print(
            "PaymentIntent created - "
            "waiting for success/failure"
        )

    # =====================================================
    # OTHER EVENTS
    # =====================================================

    else:

        print(
            "Stripe event received - no handler:",
            event_type,
        )

    # =====================================================
    # SAVE WEBHOOK EVENT
    # =====================================================

    save_webhook_event(
        event_id,
        event_type,
        db,
    )

    # =====================================================
    # RETURN 200
    # =====================================================

    print("----------------------------------------")
    print("WEBHOOK RESPONSE 200")
    print("EVENT:", event_type)
    print("EVENT ID:", event_id)
    print("----------------------------------------")

    return {
        "message": "Webhook processed successfully",
        "event_type": event_type,
        "event_id": event_id,
    }
