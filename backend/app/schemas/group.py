from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.core.enums import GroupVisibility, GroupRole, GroupMemberStatus


class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = None
    visibility: GroupVisibility = GroupVisibility.INVITE_ONLY


class GroupUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = None
    visibility: Optional[GroupVisibility] = None


class GroupResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    created_by: UUID
    visibility: GroupVisibility
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GroupMemberResponse(BaseModel):
    group_id: UUID
    user_id: UUID
    username: Optional[str] = None
    display_name: Optional[str] = None
    role: GroupRole
    status: GroupMemberStatus
    joined_at: datetime

    model_config = {"from_attributes": True}


class GroupInviteCreateRequest(BaseModel):
    receiver_id: Optional[UUID] = None
    max_uses: Optional[int] = Field(None, ge=1, le=100)
    expires_in_hours: int = Field(default=72, ge=1, le=720)


class GroupInviteResponse(BaseModel):
    id: UUID
    group_id: UUID
    created_by: UUID
    invite_token: Optional[str] = None  # Returned once upon creation
    expires_at: datetime
    max_uses: Optional[int] = None
    uses_count: int
    created_at: datetime


class GroupMemberUpdate(BaseModel):
    role: str = Field(pattern="^(admin|member)$")


class TransferOwnership(BaseModel):
    user_id: UUID


class FriendRequestCreate(BaseModel):
    receiver_id: UUID


class FriendResponse(BaseModel):
    id: UUID
    username: str
    display_name: str
    avatar_url: Optional[str] = None

