from typing import List
from uuid import UUID
from fastapi import APIRouter, Request, status
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.group import (
    GroupCreateRequest,
    GroupUpdateRequest,
    GroupResponse,
    GroupMemberResponse,
    GroupInviteCreateRequest,
    GroupInviteResponse,
)
from app.services.group_service import GroupService
from app.utils.response import wrap_response
from app.schemas.group import GroupMemberUpdate, TransferOwnership
from pydantic import BaseModel, Field


class InviteAcceptance(BaseModel):
    token: str = Field(min_length=16, max_length=200)

router = APIRouter(tags=["Groups"])


@router.post("/group-invites/accept", response_model=ResponseEnvelope[SuccessStatus])
async def accept_invite_body(request: Request, payload: InviteAcceptance, current_user: CurrentUser, db: DbSession):
    GroupService(db).accept_invite(current_user.id, payload.token)
    return wrap_response(SuccessStatus(message="Invitation accepted."), request)


@router.get("/group-invitations")
async def pending_targeted_invites(request: Request, current_user: CurrentUser, db: DbSession):
    from app.models.group import GroupInvite, Group, GroupMember
    from datetime import datetime, timezone
    rows = db.query(GroupInvite).filter(GroupInvite.receiver_id == current_user.id,
        GroupInvite.revoked_at.is_(None), GroupInvite.expires_at > datetime.now(timezone.utc)).all()
    output = []
    for row in rows:
        membership = db.get(GroupMember, (row.group_id, current_user.id))
        group = db.get(Group, row.group_id)
        if group and not group.archived_at and not (membership and membership.status in ("active", "removed")) and (not row.max_uses or row.uses_count < row.max_uses):
            output.append({"id": row.id, "group_name": group.name, "expires_at": row.expires_at})
    return wrap_response(output, request)


@router.patch("/groups/{group_id}/members/{user_id}")
async def change_member(request: Request, group_id: UUID, user_id: UUID, payload: GroupMemberUpdate, current_user: CurrentUser, db: DbSession):
    GroupService(db).manage_member(current_user.id, group_id, user_id, payload.role)
    return wrap_response(SuccessStatus(message="Member role updated."), request)


@router.delete("/groups/{group_id}/members/{user_id}")
async def remove_member(request: Request, group_id: UUID, user_id: UUID, current_user: CurrentUser, db: DbSession):
    GroupService(db).manage_member(current_user.id, group_id, user_id)
    return wrap_response(SuccessStatus(message="Member removed."), request)


@router.post("/groups/{group_id}/transfer-ownership")
async def transfer_owner(request: Request, group_id: UUID, payload: TransferOwnership, current_user: CurrentUser, db: DbSession):
    GroupService(db).transfer(current_user.id, group_id, payload.user_id)
    return wrap_response(SuccessStatus(message="Ownership transferred."), request)


@router.get("/groups/{group_id}/invites")
async def list_invites(request: Request, group_id: UUID, current_user: CurrentUser, db: DbSession):
    return wrap_response(GroupService(db).list_invites(current_user.id, group_id), request)


@router.delete("/groups/{group_id}/invites/{invite_id}")
async def revoke_invite(request: Request, group_id: UUID, invite_id: UUID, current_user: CurrentUser, db: DbSession):
    GroupService(db).revoke(current_user.id, group_id, invite_id)
    return wrap_response(SuccessStatus(message="Invitation revoked."), request)


@router.post("/group-invitations/{invite_id}/accept")
async def accept_targeted(request: Request, invite_id: UUID, current_user: CurrentUser, db: DbSession):
    GroupService(db).accept_targeted(current_user.id, invite_id)
    return wrap_response(SuccessStatus(message="Invitation accepted."), request)


@router.get("/groups", response_model=ResponseEnvelope[List[GroupResponse]])
async def list_user_groups(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GroupService(db)
    groups = service.list_groups(current_user.id)
    return wrap_response(groups, request)


@router.post("/groups", response_model=ResponseEnvelope[GroupResponse], status_code=status.HTTP_201_CREATED)
async def create_group(
    request: Request,
    payload: GroupCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GroupService(db)
    group = service.create_group(current_user.id, payload)
    return wrap_response(group, request)


@router.get("/groups/{group_id}", response_model=ResponseEnvelope[GroupResponse])
async def get_group_details(
    request: Request,
    group_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GroupService(db)
    group = service.get_group_details(current_user.id, group_id)
    return wrap_response(group, request)


@router.patch("/groups/{group_id}", response_model=ResponseEnvelope[GroupResponse])
async def update_group(
    request: Request,
    group_id: UUID,
    payload: GroupUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GroupService(db)
    group = service.update_group(current_user.id, group_id, payload)
    return wrap_response(group, request)


@router.post("/groups/{group_id}/invites", response_model=ResponseEnvelope[GroupInviteResponse], status_code=status.HTTP_201_CREATED)
async def create_group_invite(
    request: Request,
    group_id: UUID,
    payload: GroupInviteCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GroupService(db)
    invite = service.create_invite(current_user.id, group_id, payload)
    return wrap_response(invite, request)


@router.post("/group-invites/{token}/accept", response_model=ResponseEnvelope[SuccessStatus])
async def accept_group_invite(
    request: Request,
    token: str,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GroupService(db)
    service.accept_invite(current_user.id, token)
    return wrap_response(SuccessStatus(success=True, message="Joined group successfully"), request)


@router.post("/groups/{group_id}/leave", response_model=ResponseEnvelope[SuccessStatus])
async def leave_group(
    request: Request,
    group_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GroupService(db)
    service.leave_group(current_user.id, group_id)
    return wrap_response(SuccessStatus(success=True, message="Left group successfully"), request)


@router.get("/groups/{group_id}/members", response_model=ResponseEnvelope[List[GroupMemberResponse]])
async def list_group_members(
    request: Request,
    group_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = GroupService(db)
    members = service.list_members(current_user.id, group_id)
    return wrap_response(members, request)
