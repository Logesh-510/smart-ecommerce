from pydantic import BaseModel
from datetime import datetime


class NotificationBase(BaseModel):
    type: str
    message: str


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    read_status: bool
    timestamp: datetime

    class Config:
        from_attributes = True