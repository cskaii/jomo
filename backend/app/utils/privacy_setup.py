from fastapi import HTTPException
from app.core.config import get_settings


def require_optional_data_setup():
    settings = get_settings()
    if settings.APP_ENV not in ("development", "test") and not settings.PRIVACY_CONTACT_EMAIL:
        raise HTTPException(503, detail={"code": "PRIVACY_SETUP_REQUIRED",
            "message": "Optional personal-data collection requires a configured privacy contact."})
