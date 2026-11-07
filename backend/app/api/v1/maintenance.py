"""Scheduled retention; never authorised by a browser session or query-string key."""
import secrets
from fastapi import APIRouter, Request, HTTPException
from starlette.concurrency import run_in_threadpool
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.retention import StorageDeletion
from app.services.retention_service import cleanup

router = APIRouter(tags=["Maintenance"])


@router.get("/internal/retention", include_in_schema=False)
async def scheduled_retention(request: Request):
    secret = get_settings().CRON_SECRET.get_secret_value()
    expected = f"Bearer {secret}"
    if len(secret) < 32 or not secrets.compare_digest(request.headers.get("authorization", "").encode(), expected.encode()):
        raise HTTPException(401, detail={"code": "MAINTENANCE_UNAUTHORIZED", "message": "Scheduled job authentication required."})
    def execute():
        with SessionLocal() as db:
            cleanup(db, time_budget_seconds=150)
            return {"success": True, "pending_deletions": db.query(StorageDeletion).count()}
    return await run_in_threadpool(execute)
