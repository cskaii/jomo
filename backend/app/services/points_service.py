import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.points import PointTransaction
from app.models.garden import Garden
from app.models.activity import Activity, ActivityParticipant
from app.services.notification_service import notify
from app.core.constants import (
    MIN_POINTS_ELIGIBILITY_MINUTES,
    DEFAULT_POINTS_PER_MINUTE,
    MAX_POINTS_PER_ACTIVITY_PARTICIPANT,
)


class PointsService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_points(
        self,
        eligible_minutes: int,
        points_per_minute: float = DEFAULT_POINTS_PER_MINUTE,
        max_reward_points: int = MAX_POINTS_PER_ACTIVITY_PARTICIPANT,
    ) -> int:
        if eligible_minutes < MIN_POINTS_ELIGIBILITY_MINUTES:
            return 0
        raw_points = int(eligible_minutes * points_per_minute)
        return min(raw_points, max_reward_points)

    def award_activity_completion_reward(
        self,
        participant_id: uuid.UUID,
        commit: bool = True,
    ) -> Optional[PointTransaction]:
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.id == participant_id)
            .populate_existing().with_for_update().first()
        )
        if not participant:
            return None

        activity = self.db.query(Activity).filter(Activity.id == participant.activity_id).first()
        if not activity:
            return None

        if participant.status != "completed":
            raise HTTPException(409, detail={"code": "COMPLETION_REQUIRED", "message": "Rewards require completed participation."})
        # Check idempotency key: Section 8.7: "activity-completion:{activity_participant_id}"
        idempotency_key = f"activity-completion:{participant.id}"
        existing_tx = (
            self.db.query(PointTransaction)
            .filter(PointTransaction.idempotency_key == idempotency_key)
            .first()
        )
        if existing_tx:
            # Reward already processed idempotently
            return existing_tx

        # Determine target garden: Section 8.8: Group garden if group activity, otherwise personal garden
        if activity.group_id:
            garden = (
                self.db.query(Garden)
                .filter(Garden.garden_type == "group", Garden.owner_group_id == activity.group_id)
                .populate_existing().with_for_update()
                .first()
            )
        else:
            garden = (
                self.db.query(Garden)
                .filter(Garden.garden_type == "personal", Garden.owner_user_id == participant.user_id)
                .populate_existing().with_for_update()
                .first()
            )

        if not garden:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "GARDEN_NOT_FOUND", "message": "Target reward garden not found."},
            )

        rate = float(activity.points_per_minute or DEFAULT_POINTS_PER_MINUTE)
        cap = activity.max_reward_points or MAX_POINTS_PER_ACTIVITY_PARTICIPANT
        points = self.calculate_points(participant.eligible_minutes, rate, cap)

        if points <= 0:
            return None

        # Transactional update
        tx = PointTransaction(
            garden_id=garden.id,
            user_id=participant.user_id,
            activity_participant_id=participant.id,
            transaction_type="earn",
            amount=points,
            reason=f"Completed activity: {activity.title}",
            idempotency_key=idempotency_key,
        )
        self.db.add(tx)

        garden.points_balance += points
        garden.updated_at = datetime.now(timezone.utc)
        participant.points_awarded = points
        notify(self.db, participant.user_id, "reward", "Activity reward confirmed", f"{points} coins were added to the activity's garden.", f"/garden?garden={garden.id}", garden_id=garden.id, activity_id=activity.id)

        if commit:
            self.db.commit()
            self.db.refresh(tx)
        else:
            self.db.flush()
        return tx
