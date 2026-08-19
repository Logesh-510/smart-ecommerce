from pydantic import BaseModel
from typing import Optional


class PaymentCreate(BaseModel):
    order_id: int
    payment_method: str


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    payment_method: str
    status: str
    transaction_id: Optional[str] = None

    class Config:
        from_attributes = True

class PaymentStatusUpdate(BaseModel):
    status: str