from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    body: str
    payload: Optional[Dict[str, Any]] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
