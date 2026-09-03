from pydantic import BaseModel
from typing import Optional


class ReturnRequestCreate(BaseModel):
    reason: str
    comment: Optional[str] = None