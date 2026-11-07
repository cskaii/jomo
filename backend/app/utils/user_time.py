from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from app.models.user import UserPreference


def user_today(db, user_id):
    prefs = db.get(UserPreference, user_id)
    try:
        zone = ZoneInfo(prefs.timezone if prefs else "Asia/Singapore")
    except ZoneInfoNotFoundError:
        zone = ZoneInfo("Asia/Singapore")
    return datetime.now(timezone.utc).astimezone(zone).date()


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
