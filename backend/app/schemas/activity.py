from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.core.enums import ActivityStatus, ParticipantStatus, ActivityVisibility, ProofType


class ActivityCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    category: str = Field(..., min_length=1, max_length=40)
    duration_minutes: int = Field(..., ge=1, le=480)
    visibility: ActivityVisibility = ActivityVisibility.PERSONAL
    group_id: Optional[UUID] = None
    max_participants: int = Field(default=10, ge=1, le=100)
    location_required: bool = False
    proof_requirement: ProofType = ProofType.PHOTO_OR_GROUP_CONFIRMATION


class ActivityUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, min_length=1, max_length=40)
    duration_minutes: Optional[int] = Field(None, ge=1, le=480)
    max_participants: Optional[int] = Field(None, ge=1, le=100)


class ActivityResponse(BaseModel):
    id: UUID
    title: str
    description: str
    category: str
    visibility: ActivityVisibility
    status: ActivityStatus
    created_by: UUID
    group_id: Optional[UUID] = None
    duration_minutes: int
    max_participants: int
    location_required: bool
    proof_requirement: ProofType
    max_reward_points: int
    published_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActivityStartRequest(BaseModel):
    client_started_at: Optional[datetime] = None


class ActivityParticipantResponse(BaseModel):
    id: UUID
    activity_id: UUID
    user_id: UUID
    status: ParticipantStatus
    joined_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    eligible_minutes: int
    points_awarded: int
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

