"""quests and progression

Revision ID: a1f4c2d9e710
Revises: db98869da4be
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1f4c2d9e710"
down_revision: Union[str, Sequence[str], None] = "db98869da4be"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("user_progression",
        sa.Column("user_id", sa.Uuid(), nullable=False), sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("xp_current", sa.Integer(), nullable=False), sa.Column("lifetime_xp", sa.Integer(), nullable=False),
        sa.Column("completed_quests", sa.Integer(), nullable=False), sa.Column("current_streak", sa.Integer(), nullable=False),
        sa.Column("longest_streak", sa.Integer(), nullable=False), sa.Column("last_completion_date", sa.Date(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("level >= 1", name="check_progression_level"),
        sa.CheckConstraint("xp_current >= 0 AND lifetime_xp >= 0", name="check_progression_xp"),
        sa.CheckConstraint("completed_quests >= 0", name="check_completed_quests"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("user_id"))
    op.create_table("quests",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("code", sa.String(12), nullable=False),
        sa.Column("title", sa.String(120), nullable=False), sa.Column("description", sa.Text(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False), sa.Column("category", sa.String(50), nullable=False),
        sa.Column("difficulty", sa.String(10), nullable=False), sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("xp_reward", sa.Integer(), nullable=False), sa.Column("repeatability", sa.String(20), nullable=False),
        sa.Column("proof_requirement", sa.String(40), nullable=False), sa.Column("reflection_prompt", sa.String(240), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="check_quest_difficulty"),
        sa.CheckConstraint("estimated_duration_minutes >= 1 AND xp_reward >= 0", name="check_quest_values"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("code"))
    op.create_index("ix_quests_code", "quests", ["code"], unique=True)
    op.create_index("ix_quests_category", "quests", ["category"], unique=False)
    op.create_index("ix_quests_difficulty", "quests", ["difficulty"], unique=False)
    op.create_table("mission_definitions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("code", sa.String(12), nullable=False),
        sa.Column("title", sa.String(120), nullable=False), sa.Column("description", sa.Text(), nullable=False),
        sa.Column("mission_type", sa.String(10), nullable=False), sa.Column("metric", sa.String(30), nullable=False),
        sa.Column("target_value", sa.Integer(), nullable=False), sa.Column("category_filter", sa.JSON(), nullable=True),
        sa.Column("reward_xp", sa.Integer(), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.CheckConstraint("mission_type IN ('daily', 'weekly')", name="check_mission_type"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("code"))
    op.create_index("ix_mission_definitions_code", "mission_definitions", ["code"], unique=True)
    op.create_index("ix_mission_definitions_mission_type", "mission_definitions", ["mission_type"], unique=False)
    op.create_table("achievement_definitions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("code", sa.String(12), nullable=False),
        sa.Column("name", sa.String(100), nullable=False), sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metric", sa.String(30), nullable=False), sa.Column("target_value", sa.Integer(), nullable=False),
        sa.Column("category_filter", sa.String(50), nullable=True), sa.Column("reward_xp", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("code"))
    op.create_index("ix_achievement_definitions_code", "achievement_definitions", ["code"], unique=True)
    op.create_table("xp_transactions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False), sa.Column("transaction_type", sa.String(40), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False), sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("lifetime_before", sa.Integer(), nullable=False), sa.Column("lifetime_after", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(180), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="check_xp_amount"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_xp_transactions_user_id", "xp_transactions", ["user_id"], unique=False)
    op.create_index("ix_xp_transactions_idempotency_key", "xp_transactions", ["idempotency_key"], unique=True)
    op.create_index("idx_xp_transactions_user_date", "xp_transactions", ["user_id", "created_at"], unique=False)
    op.create_table("user_quest_instances",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("quest_id", sa.Uuid(), nullable=False), sa.Column("activity_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("abandoned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reflection", sa.String(1000), nullable=True), sa.Column("xp_claimed", sa.Boolean(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'completed', 'abandoned')", name="check_quest_instance_status"),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quest_id"], ["quests.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("activity_id"))
    for column in ("user_id", "quest_id", "status"):
        op.create_index(f"ix_user_quest_instances_{column}", "user_quest_instances", [column], unique=False)
    op.create_table("quest_favorites",
        sa.Column("user_id", sa.Uuid(), nullable=False), sa.Column("quest_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["quest_id"], ["quests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "quest_id"))
    op.create_table("user_missions",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("mission_id", sa.Uuid(), nullable=False), sa.Column("period_key", sa.String(20), nullable=False),
        sa.Column("current_progress", sa.Integer(), nullable=False), sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reward_claimed", sa.Boolean(), nullable=False), sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False), sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["mission_id"], ["mission_definitions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("user_id", "mission_id", "period_key", name="uq_user_mission_period"))
    op.create_index("ix_user_missions_user_id", "user_missions", ["user_id"], unique=False)
    op.create_table("user_achievements",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("achievement_id", sa.Uuid(), nullable=False), sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["achievement_id"], ["achievement_definitions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"))
    op.create_index("ix_user_achievements_user_id", "user_achievements", ["user_id"], unique=False)


def downgrade() -> None:
    for table in ("user_achievements", "user_missions", "quest_favorites", "user_quest_instances", "xp_transactions", "achievement_definitions", "mission_definitions", "quests", "user_progression"):
        op.drop_table(table)
