import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.notification import Notification


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def list_notifications(self, user_id: uuid.UUID) -> List[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
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
