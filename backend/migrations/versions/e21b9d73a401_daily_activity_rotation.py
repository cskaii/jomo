"""Persist daily discovery selections behind the backend API."""
from alembic import op
import sqlalchemy as sa

revision = "e21b9d73a401"
down_revision = "d91e7c20b403"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "daily_quest_selections",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("period_key", sa.String(10), nullable=False),
        sa.Column("quest_codes", sa.JSON(), nullable=False),
        sa.Column("suggestion_codes", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "period_key"),
    )
    if op.get_context().dialect.name == "postgresql":
        op.execute("ALTER TABLE daily_quest_selections ENABLE ROW LEVEL SECURITY")
        op.execute("REVOKE ALL ON TABLE daily_quest_selections FROM anon, authenticated")


def downgrade():
    op.drop_table("daily_quest_selections")
