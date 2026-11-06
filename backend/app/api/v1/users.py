from fastapi import APIRouter, Request, status
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope
from app.schemas.user import (
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserPreferencesResponse,
    UserPreferencesUpdateRequest,
)
from app.services.user_service import UserService
from app.utils.response import wrap_response

router = APIRouter(prefix="/users", tags=["Users"])


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
