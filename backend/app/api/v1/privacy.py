from typing import List, Literal, Annotated
from fastapi import APIRouter, Request, Header, HTTPException, status
from starlette.concurrency import run_in_threadpool
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.privacy import (
    ScreenTextRequest,
    ScreenTextResponse,
    WellbeingRecommendationRequest,
    WellbeingRecommendationResponse,
    MissionRecommendationRequest,
    MissionItemResponse,
    FileScreeningResponse,
)
from app.services.privacy_service import PrivacyService
from app.utils.response import wrap_response
from app.services.file_screening_service import FileScreeningService

router = APIRouter(prefix="/ai", tags=["AI & Privacy"])


def require_file_consent(consent):
    if consent != "true":
        raise HTTPException(400, detail={"code": "SCREENING_CONSENT_REQUIRED", "message": "Agree to submit this file before screening."})


@router.post("/privacy/image", response_model=ResponseEnvelope[FileScreeningResponse], response_model_exclude_none=True)
async def screen_image(request: Request, current_user: CurrentUser, db: DbSession,
                       consent: Annotated[str | None, Header(alias="X-Screening-Consent")] = None):
    require_file_consent(consent)
    content = await request.body()
    media_type = request.headers.get("content-type", "").split(";")[0].lower()
    result = await run_in_threadpool(FileScreeningService(db).screen_image, current_user.id, content, media_type)
    from app.models.consent import ConsentRecord
    db.add(ConsentRecord(user_id=current_user.id, purpose="image_screening", policy_version="2026-11-07", granted=True))
    db.commit()
    return wrap_response(result, request)


@router.post("/privacy/structured", response_model=ResponseEnvelope[FileScreeningResponse], response_model_exclude_none=True)
async def screen_structured(request: Request, current_user: CurrentUser, db: DbSession,
                            format: Literal["csv", "json"],
                            consent: Annotated[str | None, Header(alias="X-Screening-Consent")] = None):
    require_file_consent(consent)
    media_type = request.headers.get("content-type", "").split(";")[0].lower()
    if media_type not in ({"text/csv", "application/csv"} if format == "csv" else {"application/json"}):
        raise HTTPException(415, detail={"code": "UNSUPPORTED_SCREENING_FILE", "message": "Choose a CSV or JSON file with its matching content type."})
    content = await request.body()
    result = await run_in_threadpool(FileScreeningService(db).screen_structured, current_user.id, content, format)
    from app.models.consent import ConsentRecord
    db.add(ConsentRecord(user_id=current_user.id, purpose="structured_screening", policy_version="2026-11-07", granted=True))
    db.commit()
    return wrap_response(result, request)


@router.post("/privacy/text", response_model=ResponseEnvelope[ScreenTextResponse])
def screen_text(
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
