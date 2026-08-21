from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        unique=True
    )

    amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    payment_method = Column(
        String,
        nullable=False
    )

    status = Column(
        String,
        default="pending",
        nullable=False
    )

    transaction_id = Column(
        String,
        unique=True,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    order = relationship(
        "Order",
        back_populates="payment"
    )