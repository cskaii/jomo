import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserPreference
from app.models.garden import Garden
from app.schemas.user import UserProfileUpdateRequest, UserPreferencesUpdateRequest
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_profile(self, user_id: uuid.UUID) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            # Create user and default personal garden (as specified in Section 6.4:
            # "Create the user's personal garden during onboarding.")
            short_id = str(user_id)[:8]
            user = User(
                id=user_id,
                username=f"user_{short_id}",
                display_name=f"JOMO User {short_id}",
            )
            self.db.add(user)
            self.db.flush()

            # Default preferences
            prefs = UserPreference(
                user_id=user_id,
                timezone="Asia/Singapore",
                language="en",
                location_enabled=False,
                screening_enabled=True,
                notifications_enabled=True,
            )
            self.db.add(prefs)

            # Personal garden
            personal_garden = Garden(
                garden_type="personal",
                owner_user_id=user_id,
                owner_group_id=None,
                name="My Sanctuary",
                points_balance=0,
                growth_level=1,
            )
            self.db.add(personal_garden)

            self.db.commit()
            self.db.refresh(user)
        return user

    def update_profile(self, user_id: uuid.UUID, data: UserProfileUpdateRequest) -> User:
        user = self.get_or_create_profile(user_id)
        if data.display_name is not None:
            user.display_name = data.display_name
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url
        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_or_create_preferences(self, user_id: uuid.UUID) -> UserPreference:
        self.get_or_create_profile(user_id)
        prefs = self.db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        return prefs

    def update_preferences(self, user_id: uuid.UUID, data: UserPreferencesUpdateRequest) -> UserPreference:
        prefs = self.get_or_create_preferences(user_id)
        if data.timezone is not None:
            try:
                ZoneInfo(data.timezone)
            except (ZoneInfoNotFoundError, ValueError):
                raise HTTPException(400, detail={"code": "INVALID_TIMEZONE", "message": "Choose a valid time zone."}) from None
            prefs.timezone = data.timezone
        if data.language is not None:
            prefs.language = data.language
        if data.daily_screen_goal_minutes is not None:
            prefs.daily_screen_goal_minutes = data.daily_screen_goal_minutes
        if data.location_enabled is not None:
            prefs.location_enabled = data.location_enabled
            if not data.location_enabled:
                from app.models.location import ActivityCheckIn
                from app.models.activity import ActivityParticipant
                from app.models.consent import ConsentRecord
                participant_ids = self.db.query(ActivityParticipant.id).filter_by(user_id=user_id)
                self.db.query(ActivityCheckIn).filter(ActivityCheckIn.participant_id.in_(participant_ids)).delete(synchronize_session=False)
                self.db.add(ConsentRecord(user_id=user_id, purpose="activity_location", policy_version="2026-11-07", granted=False))
        if data.screening_enabled is not None:
            prefs.screening_enabled = data.screening_enabled
        if data.notifications_enabled is not None:
            prefs.notifications_enabled = data.notifications_enabled
        prefs.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(prefs)
        return prefs
