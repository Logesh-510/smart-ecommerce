from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class ProductView(Base):
    __tablename__ = "product_views"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    viewed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )