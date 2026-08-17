from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password = Column(String(255), nullable=True)

    role = Column(
        String(20),
        default="customer",
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    orders = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan"
    )