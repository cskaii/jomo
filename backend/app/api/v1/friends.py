from typing import List
from uuid import UUID
from fastapi import APIRouter, Request, status
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.group import FriendResponse, FriendRequestCreate
from app.services.friendship_service import FriendshipService
from app.utils.response import wrap_response

router = APIRouter(tags=["Friends"])


@router.get("/friends", response_model=ResponseEnvelope[List[FriendResponse]])
async def list_friends(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
):
    service = FriendshipService(db)
    friends = service.list_friends(current_user.id)
    return wrap_response(friends, request)


@router.post("/friend-requests", response_model=ResponseEnvelope[SuccessStatus], status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    request: Request,
    payload: FriendRequestCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    service = FriendshipService(db)
    service.send_request(current_user.id, payload.receiver_id)
    return wrap_response(SuccessStatus(success=True, message="Friend request sent"), request)


@router.post("/friend-requests/{request_id}/accept", response_model=ResponseEnvelope[SuccessStatus])
async def accept_friend_request(
    request: Request,
    request_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = FriendshipService(db)
    service.accept_request(request_id, current_user.id)
    return wrap_response(SuccessStatus(success=True, message="Friend request accepted"), request)


@router.post("/friend-requests/{request_id}/decline", response_model=ResponseEnvelope[SuccessStatus])
async def decline_friend_request(
    request: Request,
    request_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = FriendshipService(db)
    service.decline_request(request_id, current_user.id)
    return wrap_response(SuccessStatus(success=True, message="Friend request declined"), request)
