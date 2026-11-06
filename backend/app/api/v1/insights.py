from datetime import date
from typing import Optional, List, Dict
from fastapi import APIRouter, Request, Query
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.usage import UsageRecordCreate, UsageRecordResponse, UsageSummaryResponse
from app.services.usage_service import UsageService
from app.utils.response import wrap_response

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/summary", response_model=ResponseEnvelope[UsageSummaryResponse])
async def get_usage_summary(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
):
    service = UsageService(db)
    summary = service.get_summary(current_user.id, from_date, to_date)
    return wrap_response(summary, request)


@router.get("/daily", response_model=ResponseEnvelope[List[UsageRecordResponse]])
async def get_daily_usage(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
):
    service = UsageService(db)
    records = service.get_daily_records(current_user.id, from_date, to_date)
    return wrap_response(records, request)


@router.get("/categories", response_model=ResponseEnvelope[Dict[str, int]])
async def get_categories_breakdown(
    request: Request,
    current_user: CurrentUser,
    db: DbSession,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
):
    service = UsageService(db)
    breakdown = service.get_category_breakdown(current_user.id, from_date, to_date)
    return wrap_response(breakdown, request)


@router.post("/manual", response_model=ResponseEnvelope[UsageRecordResponse])
async def submit_manual_usage(
    request: Request,
    payload: UsageRecordCreate,
    current_user: CurrentUser,
    db: DbSession,
):
    service = UsageService(db)
    record = service.record_usage(current_user.id, payload)
    return wrap_response(record, request)


@router.post("/import", response_model=ResponseEnvelope[SuccessStatus])
async def import_usage_records(
    request: Request,
    payload: List[UsageRecordCreate],
    current_user: CurrentUser,
    db: DbSession,
):
    service = UsageService(db)
    service.import_records(current_user.id, payload)
    return wrap_response(SuccessStatus(success=True, message=f"Imported {len(payload)} records"), request)
