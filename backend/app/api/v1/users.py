from fastapi import APIRouter, Request, status
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope
from app.schemas.user import (
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
    DeleteAccountRequest,
)
from app.schemas.common import SuccessStatus
from app.services.account_deletion_service import AccountDeletionService
from app.services.user_service import UserService
from app.utils.response import wrap_response
from pydantic import BaseModel
from typing import Literal


class OnboardingAcknowledgement(BaseModel):
    privacy_notice_acknowledged: Literal[True]

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/export")
async def export_account(request: Request, current_user: CurrentUser, db: DbSession):
    from app.services.data_control_service import DataControlService
    from starlette.responses import JSONResponse
    return JSONResponse(wrap_response(DataControlService(db).export(current_user.id, current_user.email), request).model_dump(mode="json"),
                        headers={"Cache-Control": "no-store", "Content-Disposition": 'attachment; filename="jomo-data.json"'})


@router.post("/me/onboarding", response_model=ResponseEnvelope[SuccessStatus])
async def complete_onboarding(request: Request, payload: OnboardingAcknowledgement, current_user: CurrentUser, db: DbSession):
    from datetime import datetime, timezone
    prefs = UserService(db).get_or_create_preferences(current_user.id)
    prefs.onboarding_completed_at = datetime.now(timezone.utc)
    from app.models.consent import ConsentRecord
    db.add(ConsentRecord(user_id=current_user.id, purpose="privacy_notice_acknowledgement", policy_version="2026-11-07", granted=True))
    db.commit()
    return wrap_response(SuccessStatus(message="Welcome to your space."), request)


@router.delete("/me/proof-images", response_model=ResponseEnvelope[SuccessStatus])
async def remove_photos(request: Request, current_user: CurrentUser, db: DbSession):
    from app.services.data_control_service import DataControlService
    DataControlService(db).remove_photos(current_user.id)
    return wrap_response(SuccessStatus(message="Photo access removed. Private storage deletion is queued."), request)


@router.delete("/me/screening-history", response_model=ResponseEnvelope[SuccessStatus])
async def clear_screening(request: Request, current_user: CurrentUser, db: DbSession):
    from app.services.data_control_service import DataControlService
    DataControlService(db).clear_screening(current_user.id)
    return wrap_response(SuccessStatus(message="Screening history cleared."), request)


@router.delete("/me", response_model=ResponseEnvelope[SuccessStatus])
async def delete_current_user_account(
    request: Request,
    payload: DeleteAccountRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    await AccountDeletionService(db).delete(current_user, payload)
    return wrap_response(SuccessStatus(message="Your account has been permanently deleted."), request)


@router.get("/me", response_model=ResponseEnvelope[UserProfileResponse])
async def get_current_user_profile(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
):
    service = UserService(db)
    profile = service.get_or_create_profile(current_user.id)
    return wrap_response(profile, request)


@router.patch("/me", response_model=ResponseEnvelope[UserProfileResponse])
async def update_current_user_profile(
    request: Request,
    payload: UserProfileUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = UserService(db)
    profile = service.update_profile(current_user.id, payload)
    return wrap_response(profile, request)


@router.get("/me/preferences", response_model=ResponseEnvelope[UserPreferencesResponse])
async def get_user_preferences(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
):
    service = UserService(db)
    prefs = service.get_or_create_preferences(current_user.id)
    return wrap_response(prefs, request)


@router.patch("/me/preferences", response_model=ResponseEnvelope[UserPreferencesResponse])
async def update_user_preferences(
    request: Request,
    payload: UserPreferencesUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = UserService(db)
    prefs = service.update_preferences(current_user.id, payload)
    return wrap_response(prefs, request)
