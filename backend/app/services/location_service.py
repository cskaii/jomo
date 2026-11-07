import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.location import ActivityCheckIn
from app.models.activity import ActivityParticipant
from app.models.user import UserPreference
from app.models.consent import ConsentRecord
from app.services.activity_service import ActivityService
from app.utils.user_time import utc
from app.schemas.location import CheckInCreateRequest, CheckInResponse
from app.core.enums import LocationPrecision


class LocationService:
    def __init__(self, db: Session):
        self.db = db

    def record_check_in(self, user_id: uuid.UUID, activity_id: uuid.UUID, data: CheckInCreateRequest) -> CheckInResponse:
        from app.utils.privacy_setup import require_optional_data_setup
        require_optional_data_setup()
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

        activity = ActivityService(self.db).get_activity(user_id, activity_id)
        prefs = self.db.get(UserPreference, user_id)
        now = datetime.now(timezone.utc)
        if not prefs or not prefs.location_enabled:
            raise HTTPException(403, detail={"code": "LOCATION_DISABLED", "message": "Enable optional location check-ins in Settings first."})
        if activity.status != "active" or participant.status != "active":
            raise HTTPException(409, detail={"code": "INVALID_STATE", "message": "Location check-ins are only available during an active activity."})
        if data.captured_at.tzinfo is None or abs((now - utc(data.captured_at)).total_seconds()) > 120:
            raise HTTPException(400, detail={"code": "STALE_LOCATION", "message": "Capture a fresh location reading and try again."})
        self.db.query(ActivityCheckIn).filter_by(participant_id=participant.id).delete()
        self.db.add(ConsentRecord(user_id=user_id, purpose="activity_location", policy_version="2026-11-07", granted=True))
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
            captured_at=check_in.captured_at, expires_at=check_in.expires_at,
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
            .filter(ActivityCheckIn.participant_id == participant.id, ActivityCheckIn.expires_at > datetime.now(timezone.utc))
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
            captured_at=check_in.captured_at, expires_at=check_in.expires_at,
        )

    def delete_my_check_in(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> None:
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if participant:
            self.db.query(ActivityCheckIn).filter(ActivityCheckIn.participant_id == participant.id).delete()
            self.db.add(ConsentRecord(user_id=user_id, purpose="activity_location", policy_version="2026-11-07", granted=False))
            self.db.commit()

