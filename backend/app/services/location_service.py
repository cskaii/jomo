import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.location import ActivityCheckIn
from app.models.activity import ActivityParticipant
from app.schemas.location import CheckInCreateRequest, CheckInResponse
from app.core.enums import LocationPrecision


class LocationService:
    def __init__(self, db: Session):
        self.db = db

    def record_check_in(self, user_id: uuid.UUID, activity_id: uuid.UUID, data: CheckInCreateRequest) -> CheckInResponse:
        if not data.consent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CONSENT_REQUIRED", "message": "Location check-in requires explicit user consent."},
            )

        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PARTICIPANT_NOT_FOUND", "message": "Must be participant in activity to check in."},
            )

        # Coarsen to 3 decimal places for privacy preservation (approx ~100m)
        lat = round(data.latitude, 3) if data.latitude is not None else None
        lon = round(data.longitude, 3) if data.longitude is not None else None

        check_in = ActivityCheckIn(
            activity_id=activity_id,
            participant_id=participant.id,
            latitude=lat,
            longitude=lon,
            accuracy_meters=data.accuracy_meters,
            precision_level=LocationPrecision.APPROXIMATE.value,
            consent_at=datetime.now(timezone.utc),
            captured_at=data.captured_at,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),  # 24h retention
        )
        self.db.add(check_in)
        self.db.commit()
        self.db.refresh(check_in)

        return CheckInResponse(
            check_in_id=check_in.id,
            accepted=True,
            precision=LocationPrecision.APPROXIMATE,
        )

    def get_my_check_in(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> CheckInResponse:
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PARTICIPANT_NOT_FOUND", "message": "Participant not found."},
            )

        check_in = (
            self.db.query(ActivityCheckIn)
            .filter(ActivityCheckIn.participant_id == participant.id)
            .order_by(ActivityCheckIn.created_at.desc())
            .first()
        )
        if not check_in:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CHECK_IN_NOT_FOUND", "message": "No check-in recorded for this activity."},
            )

        return CheckInResponse(
            check_in_id=check_in.id,
            accepted=True,
            precision=LocationPrecision(check_in.precision_level),
        )

    def delete_my_check_in(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> None:
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if participant:
            self.db.query(ActivityCheckIn).filter(ActivityCheckIn.participant_id == participant.id).delete()
            self.db.commit()

