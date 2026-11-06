from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.core.enums import LocationPrecision


class CheckInCreateRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    accuracy_meters: Optional[float] = Field(None, ge=0)
    captured_at: datetime
    consent: bool = Field(..., description="User explicit consent for activity check-in")


class CheckInResponse(BaseModel):
    check_in_id: UUID
    accepted: bool
    precision: LocationPrecision = LocationPrecision.APPROXIMATE

