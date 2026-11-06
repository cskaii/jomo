"""Require application tables to be accessed through the authorized backend.

Revision ID: b7d210c42f01
Revises: a1f4c2d9e710
"""
from alembic import op

revision = "b7d210c42f01"
down_revision = "a1f4c2d9e710"
branch_labels = None
depends_on = None

TABLES = (
    "achievement_definitions", "activities", "activity_check_ins", "activity_participants",
    "consent_records", "focus_sessions", "friend_requests", "friendships",
    "garden_catalog_items", "garden_items", "gardens", "group_invites", "group_members",
    "groups", "mission_definitions", "notifications", "point_transactions",
    "proof_confirmations", "proof_submissions", "quest_favorites", "quests",
    "screening_events", "usage_summaries", "user_achievements", "user_missions",
    "user_preferences", "user_progression", "user_quest_instances", "users", "xp_transactions",
)

def upgrade():
    if op.get_context().dialect.name == "postgresql":
        # No browser Data API policies: Supabase Auth identifies users, while
        # FastAPI enforces ownership and uses the server-side Postgres connection.
        for table in (*TABLES, "alembic_version"):
            op.execute(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY')

def downgrade():
    if op.get_context().dialect.name == "postgresql":
        for table in (*TABLES, "alembic_version"):
            op.execute(f'ALTER TABLE public."{table}" DISABLE ROW LEVEL SECURITY')
