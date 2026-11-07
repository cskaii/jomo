"""Prototype privacy controls, targeted invitations and durable photo cleanup.

Revision ID: d91e7c20b403
Revises: c8e31a04d912
"""
from alembic import op
import sqlalchemy as sa

revision = "d91e7c20b403"
down_revision = "c8e31a04d912"
branch_labels = None
depends_on = None


PHOTO_CLEANUP_SQL = """
CREATE OR REPLACE FUNCTION public.jomo_queue_proof_deletion()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  IF OLD.storage_key IS NOT NULL THEN
    IF TG_OP = 'DELETE' THEN
      INSERT INTO public.storage_deletions(storage_key, created_at, attempts)
        VALUES (OLD.storage_key, now(), 0) ON CONFLICT (storage_key) DO NOTHING;
    ELSIF OLD.storage_key IS DISTINCT FROM NEW.storage_key THEN
      INSERT INTO public.storage_deletions(storage_key, created_at, attempts)
        VALUES (OLD.storage_key, now(), 0) ON CONFLICT (storage_key) DO NOTHING;
    END IF;
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END $$;
REVOKE ALL ON FUNCTION public.jomo_queue_proof_deletion() FROM PUBLIC;
CREATE TRIGGER jomo_queue_proof_deletion BEFORE DELETE OR UPDATE OF storage_key
ON public.proof_submissions FOR EACH ROW EXECUTE FUNCTION public.jomo_queue_proof_deletion();
ALTER TABLE public.storage_deletions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_access_events ENABLE ROW LEVEL SECURITY;
"""


def upgrade():
    op.add_column("user_preferences", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("group_invites", sa.Column("receiver_id", sa.Uuid(), nullable=True))
    if op.get_context().dialect.name == "postgresql":
        op.create_foreign_key("fk_group_invite_receiver", "group_invites", "users", ["receiver_id"], ["id"], ondelete="CASCADE")
    op.create_table("storage_deletions",
        sa.Column("storage_key", sa.String(200), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False))
    op.create_table("data_access_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("subject_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("purpose", sa.String(40), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_data_access_events_subject_user_id", "data_access_events", ["subject_user_id"])
    if op.get_context().dialect.name == "postgresql":
        if op.get_context().as_sql:
            op.get_context().impl.static_output(PHOTO_CLEANUP_SQL)
        else:
            op.get_bind().exec_driver_sql(PHOTO_CLEANUP_SQL, execution_options={"no_parameters": True})


def downgrade():
    raise RuntimeError("Review backup/retention requirements before reversing this privacy migration.")
