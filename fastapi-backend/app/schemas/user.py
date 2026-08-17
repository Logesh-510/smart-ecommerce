from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):

    id: int
    name: str
    email: str
    role: str
    created_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True
    )