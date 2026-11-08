from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query, Request

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.progression import (
    AchievementResponse, ActivitiesOverviewResponse, DailyDiscoveryResponse, MissionResponse, ProgressionResponse, QuestCompleteRequest,
    QuestCompletionResponse, QuestInstanceResponse, QuestResponse, XpTransactionResponse,
)
from app.services.progression_service import ProgressionService
from app.utils.response import wrap_response

router = APIRouter(tags=["Progression & Quests"])


@router.get("/progression/activities", response_model=ResponseEnvelope[ActivitiesOverviewResponse])
def activities_overview(request: Request, current_user: CurrentUser, db: DbSession):
    # Synchronous SQLAlchemy work belongs in FastAPI's thread pool, not its event loop.
    return wrap_response(ProgressionService(db).activities_overview(current_user.id), request)


@router.get("/progression", response_model=ResponseEnvelope[ProgressionResponse])
async def progression(request: Request, current_user: CurrentUser, db: DbSession):
    return wrap_response(ProgressionService(db).progression_payload(current_user.id), request)


@router.get("/progression/xp-history", response_model=ResponseEnvelope[List[XpTransactionResponse]])
async def xp_history(request: Request, current_user: CurrentUser, db: DbSession):
    return wrap_response(ProgressionService(db).xp_history(current_user.id), request)


@router.get("/quests", response_model=ResponseEnvelope[List[QuestResponse]])
async def quests(
    request: Request, current_user: CurrentUser, db: DbSession,
    category: Optional[str] = None, difficulty: Optional[str] = None,
    search: Optional[str] = Query(default=None, max_length=80), favorites: bool = False,
):
    return wrap_response(ProgressionService(db).list_quests(current_user.id, category, difficulty, search, favorites), request)


@router.get("/quests/history", response_model=ResponseEnvelope[List[QuestInstanceResponse]])
async def quest_history(request: Request, current_user: CurrentUser, db: DbSession):
    service = ProgressionService(db)
    rows = service.history(current_user.id)
    return wrap_response([{
        "id": row.id, "quest": service._quest_payload(row.quest, current_user.id),
        "activity_id": row.activity_id, "status": row.status, "started_at": row.started_at,
        "completed_at": row.completed_at, "abandoned_at": row.abandoned_at,
        "reflection": row.reflection, "xp_claimed": row.xp_claimed,
    } for row in rows], request)


@router.get("/quests/discovery", response_model=ResponseEnvelope[DailyDiscoveryResponse])
async def discovery(request: Request, current_user: CurrentUser, db: DbSession):
    return wrap_response(ProgressionService(db).daily_discovery(current_user.id), request)


@router.get("/quests/{code}", response_model=ResponseEnvelope[QuestResponse])
async def quest(request: Request, code: str, current_user: CurrentUser, db: DbSession):
    return wrap_response(ProgressionService(db).get_quest(current_user.id, code), request)


@router.post("/quests/{code}/favorite", response_model=ResponseEnvelope[SuccessStatus])
async def favorite(request: Request, code: str, current_user: CurrentUser, db: DbSession):
    state = ProgressionService(db).toggle_favorite(current_user.id, code)
    return wrap_response(SuccessStatus(success=True, message="Quest saved" if state else "Quest removed from saved"), request)


@router.post("/quests/{code}/start", response_model=ResponseEnvelope[QuestInstanceResponse])
async def start(request: Request, code: str, current_user: CurrentUser, db: DbSession):
    service = ProgressionService(db)
    row = service.start_quest(current_user.id, code)
    return wrap_response({
        "id": row.id, "quest": service._quest_payload(row.quest, current_user.id),
        "activity_id": row.activity_id, "status": row.status, "started_at": row.started_at,
        "completed_at": row.completed_at, "abandoned_at": row.abandoned_at,
        "reflection": row.reflection, "xp_claimed": row.xp_claimed,
    }, request)


@router.post("/quest-instances/{instance_id}/abandon", response_model=ResponseEnvelope[SuccessStatus])
async def abandon(request: Request, instance_id: UUID, current_user: CurrentUser, db: DbSession):
    ProgressionService(db).abandon_quest(current_user.id, instance_id)
    return wrap_response(SuccessStatus(success=True, message="Quest abandoned without penalty"), request)


@router.post("/quest-instances/{instance_id}/complete", response_model=ResponseEnvelope[QuestCompletionResponse])
async def complete(request: Request, instance_id: UUID, payload: QuestCompleteRequest, current_user: CurrentUser, db: DbSession):
    return wrap_response(ProgressionService(db).complete_quest(current_user.id, instance_id, payload.reflection), request)


@router.get("/missions/{mission_type}", response_model=ResponseEnvelope[List[MissionResponse]])
async def missions(request: Request, mission_type: str, current_user: CurrentUser, db: DbSession):
    if mission_type not in ("daily", "weekly"):
        from fastapi import HTTPException
        raise HTTPException(422, detail={"code": "INVALID_MISSION_TYPE", "message": "Use daily or weekly."})
    rows = ProgressionService(db).get_missions(current_user.id, mission_type)
    return wrap_response([{
        "id": row.id, "code": row.mission.code, "title": row.mission.title,
        "description": row.mission.description, "mission_type": row.mission.mission_type,
        "current_progress": row.current_progress, "target_value": row.mission.target_value,
        "reward_xp": row.mission.reward_xp, "status": row.status,
        "reward_claimed": row.reward_claimed, "start_at": row.start_at, "end_at": row.end_at,
        "categories": (row.mission.category_filter or {}).get("categories", []),
    } for row in rows], request)


@router.post("/missions/{assignment_id}/claim", response_model=ResponseEnvelope[MissionResponse])
async def claim_mission(request: Request, assignment_id: UUID, current_user: CurrentUser, db: DbSession):
    row = ProgressionService(db).claim_mission(current_user.id, assignment_id)
    return wrap_response({
        "id": row.id, "code": row.mission.code, "title": row.mission.title,
        "description": row.mission.description, "mission_type": row.mission.mission_type,
        "current_progress": row.current_progress, "target_value": row.mission.target_value,
        "reward_xp": row.mission.reward_xp, "status": row.status,
        "reward_claimed": row.reward_claimed, "start_at": row.start_at, "end_at": row.end_at,
        "categories": (row.mission.category_filter or {}).get("categories", []),
    }, request)


@router.get("/achievements", response_model=ResponseEnvelope[List[AchievementResponse]])
async def achievements(request: Request, current_user: CurrentUser, db: DbSession):
    return wrap_response(ProgressionService(db).list_achievements(current_user.id), request)
