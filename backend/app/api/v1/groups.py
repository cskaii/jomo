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

router = APIRouter(tags=["Groups"])


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
