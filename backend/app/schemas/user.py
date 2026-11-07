from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, SecretStr


class DeleteAccountRequest(BaseModel):
    confirmation: Literal["DELETE"]
    password: SecretStr = Field(min_length=1, max_length=1024)
    model_config = {"extra": "forbid"}


class UserProfileResponse(BaseModel):
    id: UUID
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=80)
    avatar_url: Optional[str] = None


class UserPreferencesResponse(BaseModel):
    user_id: UUID
    timezone: str
    language: str
    daily_screen_goal_minutes: Optional[int] = None
    location_enabled: bool
    screening_enabled: bool
    notifications_enabled: bool
    created_at: datetime
    updated_at: datetime
    onboarding_completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserPreferencesUpdateRequest(BaseModel):
    timezone: Optional[str] = Field(None, max_length=64)
    language: Optional[str] = Field(None, max_length=10)
    daily_screen_goal_minutes: Optional[int] = Field(None, ge=1, le=1440)
    location_enabled: Optional[bool] = None
    screening_enabled: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
