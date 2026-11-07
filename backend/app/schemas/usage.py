from datetime import date, datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
from app.core.enums import UsageSource


class UsageRecordCreate(BaseModel):
    usage_date: date
    total_minutes: int = Field(..., ge=0, le=1440)
    social_minutes: Optional[int] = Field(None, ge=0, le=1440)
    category_breakdown: Optional[Dict[str, int]] = None
    source: UsageSource = UsageSource.MANUAL

    @model_validator(mode="after")
    def validate_totals(self):
        if self.social_minutes is not None and self.social_minutes > self.total_minutes:
            raise ValueError("Social minutes cannot exceed total screen time")
        if self.category_breakdown is not None:
            if len(self.category_breakdown) > 30 or any(not key or len(key) > 50 or not isinstance(value, int) or value < 0 for key, value in self.category_breakdown.items()):
                raise ValueError("Invalid category breakdown")
            if sum(self.category_breakdown.values()) > self.total_minutes:
                raise ValueError("Category minutes cannot exceed total screen time")
        return self


    @field_validator("source")
    @classmethod
    def reject_demo_source(cls, value):
        if value == UsageSource.DEMO:
            raise ValueError("Demo usage imports are disabled. Record actual usage instead.")
        return value


class UsageRecordResponse(BaseModel):
    id: UUID
    user_id: UUID
    usage_date: date
    total_minutes: int
    social_minutes: Optional[int] = None
    category_breakdown: Optional[Dict[str, Any]] = None
    source: UsageSource
    created_at: datetime

    model_config = {"from_attributes": True}


class UsageSummaryResponse(BaseModel):
    total_screen_time_minutes: int
    daily_average_minutes: int
    social_time_minutes: int
    start_date: date
    end_date: date
    days_recorded: int
    daily_breakdown: List[UsageRecordResponse] = Field(default_factory=list)

