import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.activity import Activity, ActivityParticipant
from app.models.group import GroupMember
from app.schemas.activity import ActivityCreateRequest, ActivityUpdateRequest
from app.core.enums import ActivityStatus, ParticipantStatus, ActivityVisibility


class ActivityService:
    def __init__(self, db: Session):
        self.db = db

    def list_activities(
        self,
        user_id: uuid.UUID,
        group_id: Optional[uuid.UUID] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Activity]:
        query = self.db.query(Activity)
        if group_id:
            # Check user is member of group
            member = (
                self.db.query(GroupMember)
                .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id, GroupMember.status == "active")
                .first()
            )
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "NOT_GROUP_MEMBER", "message": "Cannot view activities for a group you are not in."},
                )
            query = query.filter(Activity.group_id == group_id)
        else:
            # Return personal activities created by user OR group activities for user's active groups
            user_group_ids = [
                m.group_id
                for m in self.db.query(GroupMember)
                .filter(GroupMember.user_id == user_id, GroupMember.status == "active")
                .all()
            ]
            query = query.filter(
                ((Activity.created_by == user_id) & Activity.group_id.is_(None))
                | Activity.group_id.in_(user_group_ids)
            )

        if status_filter:
            query = query.filter(Activity.status == status_filter)

        return query.order_by(Activity.created_at.desc(), Activity.id).offset(offset).limit(limit).all()

    def create_activity(self, user_id: uuid.UUID, data: ActivityCreateRequest) -> Activity:
        if data.visibility == ActivityVisibility.GROUP:
            if not data.group_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "GROUP_ID_REQUIRED", "message": "Group activities require a valid group_id."},
                )
            member = (
                self.db.query(GroupMember)
                .filter(GroupMember.group_id == data.group_id, GroupMember.user_id == user_id, GroupMember.status == "active")
                .first()
            )
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "GROUP_MEMBERSHIP_REQUIRED", "message": "You must be an active group member to create an activity for this group."},
                )
        else:
            data.group_id = None

        activity = Activity(
            created_by=user_id,
            group_id=data.group_id,
            title=data.title,
            description=data.description,
            category=data.category,
            visibility=data.visibility.value,
            status=ActivityStatus.PUBLISHED.value,
            duration_minutes=data.duration_minutes,
            max_participants=data.max_participants,
            location_required=data.location_required,
            proof_requirement=data.proof_requirement.value,
            max_reward_points=min(data.duration_minutes, 100),
            published_at=datetime.now(timezone.utc),
        )
        self.db.add(activity)
        self.db.flush()

        # Automatically join creator as participant
        creator_participant = ActivityParticipant(
            activity_id=activity.id,
            user_id=user_id,
            status=ParticipantStatus.JOINED.value,
        )
        self.db.add(creator_participant)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def get_activity(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> Activity:
        activity = self.db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ACTIVITY_NOT_FOUND", "message": "Activity not found."},
            )
        if activity.group_id:
            member = self.db.query(GroupMember).filter(
                GroupMember.group_id == activity.group_id,
                GroupMember.user_id == user_id,
                GroupMember.status == "active",
            ).first()
            allowed = member is not None
        else:
            allowed = activity.created_by == user_id
        if not allowed:
            raise HTTPException(403, detail={"code": "ACTIVITY_ACCESS_DENIED", "message": "You cannot access this activity."})
        return activity

    def update_activity(self, user_id: uuid.UUID, activity_id: uuid.UUID, data: ActivityUpdateRequest) -> Activity:
        activity = self.get_activity(user_id, activity_id)
        if activity.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PERMISSION_DENIED", "message": "Only the activity creator can update activity details."},
            )
        if activity.status not in (ActivityStatus.DRAFT.value, ActivityStatus.PUBLISHED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_STATE", "message": "Cannot edit an active or completed activity."},
            )
        if data.title is not None:
            activity.title = data.title
        if data.description is not None:
            activity.description = data.description
        if data.category is not None:
            activity.category = data.category
        if data.duration_minutes is not None:
            activity.duration_minutes = data.duration_minutes
        if data.max_participants is not None:
            activity.max_participants = data.max_participants

        activity.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def publish_activity(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> Activity:
        activity = self.get_activity(user_id, activity_id)
        if activity.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PERMISSION_DENIED", "message": "Only creator can publish."},
            )
        if activity.status == ActivityStatus.PUBLISHED.value:
            return activity
        if activity.status != ActivityStatus.DRAFT.value:
            raise HTTPException(409, detail={"code": "INVALID_STATE", "message": "Only a draft activity can be published."})
        activity.status = ActivityStatus.PUBLISHED.value
        activity.published_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def start_activity(self, user_id: uuid.UUID, activity_id: uuid.UUID, client_started_at: Optional[datetime]) -> Activity:
        activity = self.get_activity(user_id, activity_id)
        if activity.status != ActivityStatus.PUBLISHED.value:
            raise HTTPException(409, detail={"code": "INVALID_STATE", "message": "Only a published activity can be started."})
        # Check permissions: Section 8.2: "For a group activity, any active group member can start it... Do not restrict start permission to the creator alone."
        if activity.group_id:
            member = (
                self.db.query(GroupMember)
                .filter(GroupMember.group_id == activity.group_id, GroupMember.user_id == user_id, GroupMember.status == "active")
                .first()
            )
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "NOT_GROUP_MEMBER", "message": "Must be group member to start group activity."},
                )
        elif activity.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PERMISSION_DENIED", "message": "Cannot start someone else's personal activity."},
            )

        now = datetime.now(timezone.utc)
        activity.status = ActivityStatus.ACTIVE.value
        activity.started_at = now

        # Update or create participant record for caller
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if not participant:
            participant = ActivityParticipant(
                activity_id=activity_id,
                user_id=user_id,
                status=ParticipantStatus.ACTIVE.value,
                started_at=now,
            )
            self.db.add(participant)
        else:
            participant.status = ParticipantStatus.ACTIVE.value
            participant.started_at = now

        self.db.commit()
        self.db.refresh(activity)
        return activity

    def join_activity(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> ActivityParticipant:
        activity = self.get_activity(user_id, activity_id)
        if activity.status not in (ActivityStatus.PUBLISHED.value, ActivityStatus.ACTIVE.value):
            raise HTTPException(409, detail={"code": "INVALID_STATE", "message": "This activity cannot be joined."})
        if activity.group_id:
            member = (
                self.db.query(GroupMember)
                .filter(GroupMember.group_id == activity.group_id, GroupMember.user_id == user_id, GroupMember.status == "active")
                .first()
            )
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "NOT_GROUP_MEMBER", "message": "Must be group member to join."},
                )

        # Capacity check
        active_count = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.status.in_(["joined", "active"]))
            .count()
        )
        if active_count >= activity.max_participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ACTIVITY_FULL", "message": "Activity has reached maximum participant capacity."},
            )

        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        now = datetime.now(timezone.utc)
        if not participant:
            participant = ActivityParticipant(
                activity_id=activity_id,
                user_id=user_id,
                status=ParticipantStatus.ACTIVE.value if activity.status == ActivityStatus.ACTIVE.value else ParticipantStatus.JOINED.value,
                started_at=now if activity.status == ActivityStatus.ACTIVE.value else None,
            )
            self.db.add(participant)
        else:
            participant.status = ParticipantStatus.ACTIVE.value if activity.status == ActivityStatus.ACTIVE.value else ParticipantStatus.JOINED.value
            if not participant.started_at and activity.status == ActivityStatus.ACTIVE.value:
                participant.started_at = now

        self.db.commit()
        self.db.refresh(participant)
        return participant

    def leave_activity(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> None:
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if participant:
            participant.status = ParticipantStatus.LEFT.value
            participant.ended_at = datetime.now(timezone.utc)
            self.db.commit()

    def end_activity(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> Activity:
        activity = self.get_activity(user_id, activity_id)
        actor = self.db.query(ActivityParticipant).filter(
            ActivityParticipant.activity_id == activity_id,
            ActivityParticipant.user_id == user_id,
            ActivityParticipant.status == ParticipantStatus.ACTIVE.value,
        ).first()
        if not actor:
            raise HTTPException(403, detail={"code": "PARTICIPATION_REQUIRED", "message": "Only an active participant can end the activity."})
        if activity.status != ActivityStatus.ACTIVE.value:
            raise HTTPException(409, detail={"code": "INVALID_STATE", "message": "Only an active activity can be ended."})
        now = datetime.now(timezone.utc)
        activity.ended_at = now
        activity.status = ActivityStatus.AWAITING_PROOF.value if activity.proof_requirement != "none" else ActivityStatus.COMPLETED.value

        # Update all active participants end time
        active_participants = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.status == ParticipantStatus.ACTIVE.value)
            .all()
        )
        for p in active_participants:
            p.ended_at = now
            p.status = ParticipantStatus.AWAITING_PROOF.value if activity.proof_requirement != "none" else ParticipantStatus.COMPLETED.value
            if p.started_at:
                # Normalise both sides to naive UTC before subtraction to handle
                # SQLite returning naive datetimes alongside our timezone-aware now.
                ended = now.replace(tzinfo=None)
                started = p.started_at.replace(tzinfo=None) if p.started_at.tzinfo else p.started_at
                elapsed_min = max(0, int((ended - started).total_seconds() / 60))
                p.eligible_minutes = min(elapsed_min, activity.duration_minutes)

        self.db.commit()
        self.db.refresh(activity)
        return activity

    def list_participants(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> List[ActivityParticipant]:
        self.get_activity(user_id, activity_id)
        return (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id)
            .all()
        )

    def request_completion(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> None:
        activity = self.get_activity(user_id, activity_id)
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PARTICIPANT_NOT_FOUND", "message": "You are not a participant in this activity."},
            )
        if not participant.ended_at or participant.status not in (
            ParticipantStatus.AWAITING_PROOF.value, ParticipantStatus.COMPLETED.value,
        ):
            raise HTTPException(409, detail={"code": "INVALID_STATE", "message": "End participation before requesting completion."})
        # Completion requests cannot bypass the configured proof requirement.
        if activity.proof_requirement == "none":
            participant.status = ParticipantStatus.COMPLETED.value
            participant.completed_at = participant.completed_at or datetime.now(timezone.utc)
            # No-proof activities still use the same trusted completion path and
            # immutable ledger as proof-backed activities.
            self.db.flush()
            from app.services.points_service import PointsService
            PointsService(self.db).award_activity_completion_reward(participant.id)
        self.db.commit()

