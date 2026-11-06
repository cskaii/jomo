from typing import List
from fastapi import APIRouter, Request, status
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.privacy import (
    ScreenTextRequest,
    ScreenTextResponse,
    WellbeingRecommendationRequest,
    WellbeingRecommendationResponse,
    MissionRecommendationRequest,
    MissionItemResponse,
)
from app.services.privacy_service import PrivacyService
from app.utils.response import wrap_response

router = APIRouter(prefix="/ai", tags=["AI & Privacy"])


@router.post("/privacy/text", response_model=ResponseEnvelope[ScreenTextResponse])
async def screen_text(
    request: Request,
    payload: ScreenTextRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = PrivacyService(db)
    result = service.screen_text(current_user.id, payload)
    return wrap_response(result, request)


@router.post("/wellbeing/recommendation", response_model=ResponseEnvelope[WellbeingRecommendationResponse])
async def get_wellbeing_recommendation(
    request: Request,
    payload: WellbeingRecommendationRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = PrivacyService(db)
    result = service.get_wellbeing_recommendation(current_user.id, payload)
    return wrap_response(result, request)


@router.post("/missions/recommend", response_model=ResponseEnvelope[List[MissionItemResponse]])
async def recommend_missions(
    request: Request,
    payload: MissionRecommendationRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = PrivacyService(db)
    result = service.recommend_missions(current_user.id, payload)
    return wrap_response(result, request)
