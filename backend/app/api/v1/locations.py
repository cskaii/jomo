from uuid import UUID
from fastapi import APIRouter, Request, status
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.location import CheckInCreateRequest, CheckInResponse
from app.services.location_service import LocationService
from app.utils.response import wrap_response

router = APIRouter(prefix="/activities", tags=["Locations"])


@router.post("/{activity_id}/check-ins", response_model=ResponseEnvelope[CheckInResponse], status_code=status.HTTP_201_CREATED)
def submit_check_in(
    request: Request,
    activity_id: UUID,
    payload: CheckInCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = LocationService(db)
    result = service.record_check_in(current_user.id, activity_id, payload)
    return wrap_response(result, request)


@router.get("/{activity_id}/check-ins/me", response_model=ResponseEnvelope[CheckInResponse])
def get_my_check_in(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = LocationService(db)
    result = service.get_my_check_in(current_user.id, activity_id)
    return wrap_response(result, request)


@router.delete("/{activity_id}/check-ins/me", response_model=ResponseEnvelope[SuccessStatus])
def delete_my_check_in(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = LocationService(db)
    service.delete_my_check_in(current_user.id, activity_id)
    return wrap_response(SuccessStatus(success=True, message="Check-in record removed"), request)
