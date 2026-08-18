from sqlalchemy import Column, Integer, String, Text, Numeric
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False)

    description = Column(Text)

    category = Column(
        String(100),
        nullable=False,
        default="general"
    )

    price = Column(
        Numeric(10, 2),
        nullable=False
    )

    stock = Column(
        Integer,
        default=0,
        nullable=False
    )

    popularity = Column(
        Integer,
        default=0,
        nullable=False
    )

    images = Column(
        Text,
        nullable=True
    )