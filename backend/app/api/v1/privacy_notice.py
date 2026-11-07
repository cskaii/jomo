from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter(tags=["Privacy notice"])


@router.get("/privacy-notice")
async def privacy_notice():
    settings = get_settings()
    return {"version": "2026-11-07", "organisation": settings.PRIVACY_ORGANISATION,
            "contact_email": settings.PRIVACY_CONTACT_EMAIL,
            "location_retention_hours": 24, "photo_retention_days": settings.PROOF_RETENTION_DAYS,
            "notification_retention_days": 30, "screening_metadata_retention_days": 30}
