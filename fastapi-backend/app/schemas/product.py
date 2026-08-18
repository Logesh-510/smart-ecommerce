from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "general"
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0)
    popularity: int = Field(
        default=0,
        ge=0
    )

    images: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

    price: Optional[Decimal] = Field(
        default=None,
        gt=0
    )

    stock: Optional[int] = Field(
        default=None,
        ge=0
    )

    popularity: Optional[int] = Field(
        default=None,
        ge=0
    )

    images: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: str
    price: Decimal
    stock: int
    popularity: int
    images: Optional[str]
    class Config:
        from_attributes = True