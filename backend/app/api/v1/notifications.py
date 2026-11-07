from typing import List
from uuid import UUID
from fastapi import APIRouter, Request
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService
from app.utils.response import wrap_response

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/read-all", response_model=ResponseEnvelope[SuccessStatus])
async def mark_all_notifications(request: Request, current_user: CurrentUser, db: DbSession):
    NotificationService(db).mark_all_read(current_user.id)
    return wrap_response(SuccessStatus(message="Notifications marked as read."), request)


@router.get("", response_model=ResponseEnvelope[List[NotificationResponse]])
async def list_notifications(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
):
    service = NotificationService(db)
    notifications = service.list_notifications(current_user.id)
    return wrap_response(notifications, request)


@router.post("/{notification_id}/read", response_model=ResponseEnvelope[SuccessStatus])
async def mark_notification_read(
    request: Request,
    notification_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = NotificationService(db)
    service.mark_read(current_user.id, notification_id)
    return wrap_response(SuccessStatus(success=True, message="Marked as read"), request)
