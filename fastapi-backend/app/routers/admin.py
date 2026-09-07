import stripe

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.dependencies.rbac import require_role

from app.models.user import User
from app.models.return_request import ReturnRequest
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.payment import Payment
from app.models.notification import Notification
from app.services.email import send_email

# =========================================================
# Stripe Configuration
# =========================================================

stripe.api_key = settings.STRIPE_SECRET_KEY

# =========================================================
# Router Configuration
# =========================================================

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

# =========================================================
# Get All Return Requests
# =========================================================

@router.get("/returns")
def get_returns(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    return_requests = (
        db.query(ReturnRequest)
        .order_by(ReturnRequest.created_at.desc())
        .all()
    )

    return return_requests

# =========================================================
# Approve Return Request
# =========================================================

@router.post("/returns/{return_id}/approve")
def approve_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):

    # -----------------------------------------------------
    # Find Return Request
    # -----------------------------------------------------

    return_request = (
        db.query(ReturnRequest)
        .filter(ReturnRequest.id == return_id)
        .first()
    )

    if not return_request:
        raise HTTPException(
            status_code=404,
            detail="Return request not found"
        )

    if return_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending return requests can be approved"
        )


    # -----------------------------------------------------
    # Find Related Order
    # -----------------------------------------------------

    order = (
        db.query(Order)
        .filter(Order.id == return_request.order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )


    # -----------------------------------------------------
    # Find Payment
    # -----------------------------------------------------

    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id)
        .first()
    )

    refund_id = None
    refund_status = "not_required"


    # -----------------------------------------------------
    # Find Customer
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(User.id == return_request.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )


    # -----------------------------------------------------
    # Process Stripe Refund
    # -----------------------------------------------------

    if payment:

        if (
            payment.payment_method == "stripe"
            and payment.status == "completed"
            and payment.transaction_id
        ):

            try:

                refund = stripe.Refund.create(
                    payment_intent=payment.transaction_id
                )

                refund_id = refund.id
                refund_status = refund.status

            except stripe.StripeError as e:

                db.rollback()

                raise HTTPException(
                    status_code=400,
                    detail=f"Stripe refund failed: {str(e)}"
                )


            # Update payment status
            payment.status = "refunded"

            # Update order payment status
            order.payment_status = "refunded"

        else:

            refund_status = "not_applicable"


    # -----------------------------------------------------
    # Find Order Items
    # -----------------------------------------------------

    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

    if not order_items:

        raise HTTPException(
            status_code=400,
            detail="No items found for this order"
        )


    # -----------------------------------------------------
    # Restore Inventory
    # -----------------------------------------------------

    for item in order_items:

        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if not product:

            db.rollback()

            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )

        product.stock += item.quantity


    # -----------------------------------------------------
    # Update Return Request
    # -----------------------------------------------------

    return_request.status = "approved"


    # -----------------------------------------------------
    # Update Order Status
    # -----------------------------------------------------

    order.status = "returned"


    # -----------------------------------------------------
    # Create Customer Notification
    # -----------------------------------------------------

    notification = Notification(
        user_id=return_request.user_id,
        type="return_approved",
        message=(
            f"Your return request for order #{order.id} "
            f"has been approved successfully."
        )
    )

    db.add(notification)


    # -----------------------------------------------------
    # Create Refund Notification
    # -----------------------------------------------------

    if (
        payment
        and payment.status == "refunded"
        and refund_status == "succeeded"
    ):

        refund_notification = Notification(
            user_id=return_request.user_id,
            type="refund_processed",
            message=(
                f"Your refund for order #{order.id} "
                f"has been processed successfully."
            )
        )

        db.add(refund_notification)


    # -----------------------------------------------------
    # Commit Database Changes
    # -----------------------------------------------------

    try:

        db.commit()

        db.refresh(return_request)
        db.refresh(order)

        if payment:
            db.refresh(payment)

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database update failed: {str(e)}"
        )


    # -----------------------------------------------------
    # Send Return Approval Email
    # -----------------------------------------------------

    try:

        send_email(
            user.email,
            f"Return Approved - Order #{order.id}",
            (
                f"Your return request for order #{order.id} "
                "has been approved successfully.\n\n"
                f"Order status: {order.status}\n"
                f"Payment status: {order.payment_status}\n"
            ),
        )

        print("RETURN APPROVAL EMAIL SENT")

    except Exception as e:

        print(
            "WARNING: Return approval email failed:",
            str(e),
        )


    # -----------------------------------------------------
    # Send Refund Email
    # -----------------------------------------------------

    if (
        payment
        and payment.status == "refunded"
        and refund_status == "succeeded"
    ):

        try:

            send_email(
                user.email,
                f"Refund Processed - Order #{order.id}",
                (
                    f"Your refund for order #{order.id} "
                    "has been processed successfully.\n\n"
                    f"Refund amount: ₹{order.total_amount}\n"
                    f"Refund ID: {refund_id}\n"
                    "Payment status: refunded"
                ),
            )

            print("REFUND EMAIL SENT")

        except Exception as e:

            print(
                "WARNING: Refund email failed:",
                str(e),
            )


    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "message": "Return request approved successfully",
        "return_request_id": return_request.id,
        "order_id": order.id,
        "return_status": return_request.status,
        "order_status": order.status,
        "refund_status": refund_status,
        "refund_id": refund_id,
        "payment_status": (
            payment.status if payment else "no_payment"
        )
    }


# =========================================================
# Reject Return Request
# =========================================================

@router.post("/returns/{return_id}/reject")
def reject_return(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):

    # -----------------------------------------------------
    # Find Return Request
    # -----------------------------------------------------

    return_request = (
        db.query(ReturnRequest)
        .filter(ReturnRequest.id == return_id)
        .first()
    )

    if not return_request:

        raise HTTPException(
            status_code=404,
            detail="Return request not found"
        )


    # -----------------------------------------------------
    # Validate Status
    # -----------------------------------------------------

    if return_request.status != "pending":

        raise HTTPException(
            status_code=400,
            detail="Only pending return requests can be rejected"
        )


    # -----------------------------------------------------
    # Find Customer
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(User.id == return_request.user_id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )


    # -----------------------------------------------------
    # Update Return Request
    # -----------------------------------------------------

    return_request.status = "rejected"


    # -----------------------------------------------------
    # Create Customer Notification
    # -----------------------------------------------------

    notification = Notification(
        user_id=return_request.user_id,
        type="return_rejected",
        message=(
            f"Your return request for order "
            f"#{return_request.order_id} has been rejected."
        )
    )

    db.add(notification)


    # -----------------------------------------------------
    # Commit Database Changes
    # -----------------------------------------------------

    try:

        db.commit()

        db.refresh(return_request)

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database update failed: {str(e)}"
        )


    # -----------------------------------------------------
    # Send Return Rejection Email
    # -----------------------------------------------------

    try:

        send_email(
            user.email,
            f"Return Rejected - Order #{return_request.order_id}",
            (
                f"Your return request for order "
                f"#{return_request.order_id} has been rejected.\n\n"
                "If you have any questions, please contact "
                "customer support."
            ),
        )

        print("RETURN REJECTION EMAIL SENT")

    except Exception as e:

        print(
            "WARNING: Return rejection email failed:",
            str(e),
        )


    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "message": "Return request rejected successfully",
        "return_request_id": return_request.id,
        "order_id": return_request.order_id,
        "status": return_request.status
    }
