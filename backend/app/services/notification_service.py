import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.notification import Notification
from app.models.user import UserPreference


def notify(db, user_id, kind, title, body, href, **payload):
    prefs = db.get(UserPreference, user_id)
    if prefs and not prefs.notifications_enabled:
        return
    db.add(Notification(user_id=user_id, type=kind, title=title, body=body,
                        payload={"href": href, **{key: str(value) for key, value in payload.items()}}))


def resolve_notices(db, user_id, field, value):
    for notice in db.query(Notification).filter_by(user_id=user_id).limit(1000).all():
        if notice.payload and notice.payload.get(field) == str(value):
            notice.payload = {**notice.payload, "handled": True}
            notice.read_at = datetime.now(timezone.utc)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def list_notifications(self, user_id: uuid.UUID) -> List[Notification]:
        from datetime import timedelta
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.created_at >= datetime.now(timezone.utc) - timedelta(days=30))
            .order_by(Notification.created_at.desc())
            .limit(50)
            .all()
        )

    def mark_read(self, user_id: uuid.UUID, notification_id: uuid.UUID) -> None:
        notif = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if notif:
            notif.read_at = datetime.now(timezone.utc)
            self.db.commit()
        else:
            raise HTTPException(404, detail={"code": "NOTIFICATION_NOT_FOUND", "message": "Notification not found."})

    def mark_all_read(self, user_id):
        self.db.query(Notification).filter(Notification.user_id == user_id, Notification.read_at.is_(None)).update(
            {"read_at": datetime.now(timezone.utc)}, synchronize_session=False)
        self.db.commit()
