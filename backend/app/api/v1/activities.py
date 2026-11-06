from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Request, Query, status
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.activity import (
    ActivityCreateRequest,
    ActivityUpdateRequest,
    ActivityResponse,
    ActivityStartRequest,
    ActivityParticipantResponse,
)
from app.services.activity_service import ActivityService
from app.utils.response import wrap_response
from app.core.enums import ActivityStatus

router = APIRouter(prefix="/activities", tags=["Activities"])


@router.get("", response_model=ResponseEnvelope[List[ActivityResponse]])
async def browse_activities(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
    group_id: Optional[UUID] = Query(None),
    status_filter: Optional[ActivityStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    service = ActivityService(db)
    activities = service.list_activities(current_user.id, group_id, status_filter, limit, offset)
    return wrap_response(activities, request)


@router.post("", response_model=ResponseEnvelope[ActivityResponse], status_code=status.HTTP_201_CREATED)
async def create_activity(
    request: Request,
    payload: ActivityCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ActivityService(db)
    activity = service.create_activity(current_user.id, payload)
    return wrap_response(activity, request)


@router.get("/{activity_id}", response_model=ResponseEnvelope[ActivityResponse])
async def get_activity(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ActivityService(db)
    activity = service.get_activity(current_user.id, activity_id)
    return wrap_response(activity, request)


@router.patch("/{activity_id}", response_model=ResponseEnvelope[ActivityResponse])
async def update_activity(
    request: Request,
    activity_id: UUID,
    payload: ActivityUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ActivityService(db)
    activity = service.update_activity(current_user.id, activity_id, payload)
    return wrap_response(activity, request)


@router.post("/{activity_id}/publish", response_model=ResponseEnvelope[ActivityResponse])
async def publish_activity(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ActivityService(db)
    activity = service.publish_activity(current_user.id, activity_id)
    return wrap_response(activity, request)


@router.post("/{activity_id}/start", response_model=ResponseEnvelope[ActivityResponse])
async def start_activity(
    request: Request,
    activity_id: UUID,
    payload: ActivityStartRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ActivityService(db)
    activity = service.start_activity(current_user.id, activity_id, payload.client_started_at)
    return wrap_response(activity, request)


@router.post("/{activity_id}/join", response_model=ResponseEnvelope[ActivityParticipantResponse])
async def join_activity(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ActivityService(db)
    participant = service.join_activity(current_user.id, activity_id)
    return wrap_response(participant, request)


@router.post("/{activity_id}/leave", response_model=ResponseEnvelope[SuccessStatus])
async def leave_activity(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ActivityService(db)
    service.leave_activity(current_user.id, activity_id)
    return wrap_response(SuccessStatus(success=True, message="Left activity"), request)


@router.post("/{activity_id}/end", response_model=ResponseEnvelope[ActivityResponse])
async def end_activity(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ActivityService(db)
    activity = service.end_activity(current_user.id, activity_id)
    return wrap_response(activity, request)


@router.get("/{activity_id}/participants", response_model=ResponseEnvelope[List[ActivityParticipantResponse]])
async def list_participants(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ActivityService(db)
    participants = service.list_participants(current_user.id, activity_id)
    return wrap_response(participants, request)


@router.post("/{activity_id}/complete", response_model=ResponseEnvelope[SuccessStatus])
async def complete_activity(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ActivityService(db)
    service.request_completion(current_user.id, activity_id)
    return wrap_response(SuccessStatus(success=True, message="Completion requested"), request)

