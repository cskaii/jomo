import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.focus import FocusSession
from app.models.activity import ActivityParticipant
from app.services.activity_service import ActivityService


class FocusService:
    def __init__(self, db: Session):
        self.db = db

    def start_session(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> FocusSession:
        ActivityService(self.db).get_activity(user_id, activity_id, for_update=True)
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if not participant or participant.status != "active":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PARTICIPANT_NOT_FOUND", "message": "Must join activity before starting focus session."},
            )

        existing = self.db.query(FocusSession).filter_by(participant_id=participant.id, status="active").first()
        if existing:
            return existing
        session = FocusSession(
            activity_id=activity_id,
            participant_id=participant.id,
            started_at=datetime.now(timezone.utc),
            status="active",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def end_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> FocusSession:
        session = self.get_session(user_id, session_id, for_update=True)
        if session.status == "completed":
            return session
        session.status = "completed"
        session.ended_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, user_id: uuid.UUID, session_id: uuid.UUID, *, for_update: bool = False) -> FocusSession:
        query = self.db.query(FocusSession).filter(FocusSession.id == session_id).populate_existing()
        if for_update:
            query = query.with_for_update()
        session = query.first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "SESSION_NOT_FOUND", "message": "Focus session not found."},
            )
        participant = self.db.query(ActivityParticipant).filter(
            ActivityParticipant.id == session.participant_id,
            ActivityParticipant.user_id == user_id,
        ).first()
        if not participant:
            raise HTTPException(403, detail={"code": "SESSION_ACCESS_DENIED", "message": "You cannot access this focus session."})
        return session
