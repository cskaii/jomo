from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.core.enums import LocationPrecision


class CheckInCreateRequest(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0, allow_inf_nan=False)
    longitude: float = Field(ge=-180.0, le=180.0, allow_inf_nan=False)
    accuracy_meters: float = Field(ge=0, le=1000, allow_inf_nan=False)
    captured_at: datetime
    consent: bool = Field(..., description="User explicit consent for activity check-in")


class CheckInResponse(BaseModel):
    check_in_id: UUID
    accepted: bool
    precision: LocationPrecision = LocationPrecision.APPROXIMATE
    captured_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

