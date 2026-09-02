from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String

from app.core.database import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(
        String(255),
        primary_key=True,
    )

    event_type = Column(
        String(100),
        nullable=False,
    )

    processed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )