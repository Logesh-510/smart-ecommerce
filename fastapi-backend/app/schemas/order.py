from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    payment_status: str
    delivered_at: Optional[datetime] = None
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True