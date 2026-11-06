from uuid import UUID
from fastapi import APIRouter, Request, status
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope
from app.schemas.focus import FocusSessionResponse
from app.services.focus_service import FocusService
from app.utils.response import wrap_response

router = APIRouter(tags=["Focus Sessions"])


@router.post("/activities/{activity_id}/focus-sessions", response_model=ResponseEnvelope[FocusSessionResponse], status_code=status.HTTP_201_CREATED)
async def start_focus_session(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = FocusService(db)
    session = service.start_session(current_user.id, activity_id)
    return wrap_response(session, request)


@router.post("/focus-sessions/{session_id}/end", response_model=ResponseEnvelope[FocusSessionResponse])
async def end_focus_session(
    request: Request,
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = FocusService(db)
    session = service.end_session(current_user.id, session_id)
    return wrap_response(session, request)


@router.get("/focus-sessions/{session_id}", response_model=ResponseEnvelope[FocusSessionResponse])
async def get_focus_session(
    request: Request,
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = FocusService(db)
    session = service.get_session(current_user.id, session_id)
    return wrap_response(session, request)
