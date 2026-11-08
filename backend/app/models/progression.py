import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserProgression(Base):
    __tablename__ = "user_progression"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    xp_current: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_quests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("level >= 1", name="check_progression_level"),
        CheckConstraint("xp_current >= 0 AND lifetime_xp >= 0", name="check_progression_xp"),
        CheckConstraint("completed_quests >= 0", name="check_completed_quests"),
    )


class XpTransaction(Base):
    __tablename__ = "xp_transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lifetime_before: Mapped[int] = mapped_column(Integer, nullable=False)
    lifetime_after: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_xp_amount"),
        Index("idx_xp_transactions_user_date", "user_id", "created_at"),
    )


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False)
    repeatability: Mapped[str] = mapped_column(String(20), default="daily", nullable=False)
    proof_requirement: Mapped[str] = mapped_column(String(40), default="none", nullable=False)
    reflection_prompt: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="check_quest_difficulty"),
        CheckConstraint("estimated_duration_minutes >= 1 AND xp_reward >= 0", name="check_quest_values"),
    )


class UserQuestInstance(Base):
    __tablename__ = "user_quest_instances"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quests.id"), nullable=False, index=True)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    abandoned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reflection: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    xp_claimed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    quest: Mapped[Quest] = relationship("Quest")

    __table_args__ = (CheckConstraint("status IN ('active', 'completed', 'abandoned')", name="check_quest_instance_status"),)


class DailyQuestSelection(Base):
    """Persisted discovery history, including items shown but never started."""
    __tablename__ = "daily_quest_selections"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    period_key: Mapped[str] = mapped_column(String(10), primary_key=True)
    quest_codes: Mapped[list] = mapped_column(JSON, nullable=False)
    suggestion_codes: Mapped[list] = mapped_column(JSON, nullable=False)


class QuestFavorite(Base):
    __tablename__ = "quest_favorites"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    quest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quests.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class MissionDefinition(Base):
    __tablename__ = "mission_definitions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    mission_type: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(30), nullable=False)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    category_filter: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reward_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    __table_args__ = (CheckConstraint("mission_type IN ('daily', 'weekly')", name="check_mission_type"),)


class UserMission(Base):
    __tablename__ = "user_missions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mission_definitions.id"), nullable=False)
    period_key: Mapped[str] = mapped_column(String(20), nullable=False)
    current_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    reward_claimed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    mission: Mapped[MissionDefinition] = relationship("MissionDefinition")
    __table_args__ = (UniqueConstraint("user_id", "mission_id", "period_key", name="uq_user_mission_period"),)


class AchievementDefinition(Base):
    __tablename__ = "achievement_definitions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metric: Mapped[str] = mapped_column(String(30), nullable=False)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    category_filter: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reward_xp: Mapped[int] = mapped_column(Integer, nullable=False)


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("achievement_definitions.id"), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    claimed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    achievement: Mapped[AchievementDefinition] = relationship("AchievementDefinition")
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)
