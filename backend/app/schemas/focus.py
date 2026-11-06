from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.core.enums import FocusStatus


class FocusSessionResponse(BaseModel):
    id: UUID
    activity_id: UUID
    participant_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: FocusStatus
    created_at: datetime

    model_config = {"from_attributes": True}

