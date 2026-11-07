"""Atomic Supabase account deletion and shared-group ownership transfer.

Revision ID: c8e31a04d912
Revises: b7d210c42f01
"""
from pathlib import Path

from alembic import op

revision = "c8e31a04d912"
down_revision = "b7d210c42f01"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == "postgresql":
        script = Path(__file__).resolve().parents[2] / "app/db/account_deletion.sql"
        sql = script.read_text(encoding="utf-8")
        if op.get_context().as_sql:
            op.get_context().impl.static_output(sql)
        else:
            # exec_driver_sql avoids interpreting PostgreSQL :: casts as parameters.
            op.get_bind().exec_driver_sql(sql, execution_options={"no_parameters": True})


def downgrade():
    raise RuntimeError(
        "Account deletion cannot be reversed automatically. Restore a reviewed database backup instead."
    )
