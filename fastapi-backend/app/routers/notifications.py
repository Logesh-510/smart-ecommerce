from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.dependencies.rbac import require_role


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get(
    "",
    response_model=list[NotificationResponse]
)
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer"))
):
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(
        Notification.timestamp.desc()
    ).all()

    return notifications

@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer"))
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    notification.read_status = True

    db.commit()
    db.refresh(notification)

    return notification

def create_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    message: str
):
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        message=message
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification