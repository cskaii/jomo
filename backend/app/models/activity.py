import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, Numeric, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("groups.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    location_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    proof_requirement: Mapped[str] = mapped_column(String(40), default="photo_or_group_confirmation", nullable=False)
    points_per_minute: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), default=1.0, nullable=True)
    max_reward_points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("duration_minutes BETWEEN 1 AND 480", name="check_activity_duration"),
        CheckConstraint("max_participants BETWEEN 1 AND 100", name="check_activity_max_participants"),
        CheckConstraint("max_reward_points BETWEEN 0 AND 10000", name="check_activity_max_reward_points"),
        CheckConstraint("visibility IN ('personal', 'group')", name="check_activity_visibility"),
        CheckConstraint(
            "(visibility = 'personal' AND group_id IS NULL) OR (visibility = 'group' AND group_id IS NOT NULL)",
            name="check_activity_visibility_group_match",
        ),
        Index("idx_activities_group_status", "group_id", "status", "created_at"),
        Index("idx_activities_creator", "created_by", "created_at"),
    )

    participants: Mapped[list["ActivityParticipant"]] = relationship("ActivityParticipant", back_populates="activity", cascade="all, delete-orphan")


class ActivityParticipant(Base):
    __tablename__ = "activity_participants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="joined", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    eligible_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uq_activity_participants_user"),
        CheckConstraint("eligible_minutes >= 0", name="check_participant_eligible_minutes"),
        CheckConstraint("points_awarded >= 0", name="check_participant_points_awarded"),
        Index("idx_activity_participants_user", "user_id", "status"),
        Index("idx_activity_participants_activity", "activity_id", "status"),
    )

    activity: Mapped["Activity"] = relationship("Activity", back_populates="participants")
