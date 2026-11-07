-- JOMO existing database update: account deletion.
-- Paste this COMPLETE file into Supabase SQL Editor and Run.
-- This installs rules only; it does not delete existing accounts.
BEGIN;
DO $$
BEGIN
  IF (SELECT count(*) FROM public.alembic_version) <> 1 OR NOT EXISTS (
    SELECT 1 FROM public.alembic_version WHERE version_num IN ('b7d210c42f01', 'c8e31a04d912')
  ) THEN
    RAISE EXCEPTION 'Unexpected JOMO schema version. Apply the preceding migrations first.';
  END IF;
  IF to_regclass('auth.users') IS NULL THEN
    RAISE EXCEPTION 'Run this script in your Supabase project database.';
  END IF;
END $$;

-- Shared by the Alembic migration and the Supabase SQL Editor script.
-- No accounts are deleted when this setup script is run.
ALTER TABLE public.point_transactions ALTER COLUMN user_id DROP NOT NULL;

-- Resolve actual constraint names, including databases created before Alembic.
DO $$
DECLARE link record;
BEGIN
  FOR link IN
    SELECT c.conname, c.conrelid::regclass AS table_name
    FROM pg_constraint c
    WHERE c.contype = 'f' AND (
      (c.conrelid = 'public.point_transactions'::regclass
       AND c.confrelid IN ('public.users'::regclass, 'public.activity_participants'::regclass))
      OR (c.conrelid = 'public.activity_participants'::regclass AND c.confrelid = 'public.users'::regclass)
      OR (c.conrelid = 'public.proof_submissions'::regclass AND c.confrelid = 'public.users'::regclass)
      OR (c.conrelid = 'public.proof_confirmations'::regclass AND c.confrelid = 'public.users'::regclass)
      OR (c.conrelid = 'public.group_invites'::regclass AND c.confrelid = 'public.users'::regclass)
      OR (c.conrelid = 'public.activities'::regclass AND c.confrelid = 'public.groups'::regclass)
    )
  LOOP
    EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', link.table_name, link.conname);
  END LOOP;
END $$;

ALTER TABLE public.point_transactions ADD CONSTRAINT fk_points_user_deletion
  FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;
ALTER TABLE public.point_transactions ADD CONSTRAINT fk_points_participant_deletion
  FOREIGN KEY (activity_participant_id) REFERENCES public.activity_participants(id) ON DELETE SET NULL;
ALTER TABLE public.activity_participants ADD CONSTRAINT fk_participant_user_deletion
  FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE public.proof_submissions ADD CONSTRAINT fk_proof_reviewer_deletion
  FOREIGN KEY (reviewed_by) REFERENCES public.users(id) ON DELETE SET NULL;
ALTER TABLE public.proof_confirmations ADD CONSTRAINT fk_confirmation_user_deletion
  FOREIGN KEY (confirmed_by) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE public.group_invites ADD CONSTRAINT fk_invite_creator_deletion
  FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE CASCADE;
ALTER TABLE public.activities ADD CONSTRAINT fk_activity_group_deletion
  FOREIGN KEY (group_id) REFERENCES public.groups(id) ON DELETE CASCADE;

CREATE OR REPLACE FUNCTION public.jomo_prepare_account_deletion()
RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
  owned_group record;
  successor uuid;
BEGIN
  -- Lock affected groups in a stable order. Prefer an existing owner/admin,
  -- then the longest-standing active member. Departed/removed users never inherit.
  FOR owned_group IN
    SELECT g.id, g.created_by FROM public.groups g
    WHERE g.created_by = OLD.id OR EXISTS (
      SELECT 1 FROM public.group_members m
      WHERE m.group_id = g.id AND m.user_id = OLD.id
        AND m.role = 'owner' AND m.status = 'active'
    ) ORDER BY g.id FOR UPDATE
  LOOP
    successor := NULL;
    SELECT m.user_id INTO successor FROM public.group_members m
    WHERE m.group_id = owned_group.id AND m.user_id <> OLD.id AND m.status = 'active'
    ORDER BY CASE m.role WHEN 'owner' THEN 0 WHEN 'admin' THEN 1 ELSE 2 END,
      m.joined_at, m.user_id LIMIT 1 FOR UPDATE;
    IF successor IS NULL THEN
      -- A group with no remaining active members has no one to retain its garden.
      DELETE FROM public.groups WHERE id = owned_group.id;
    ELSE
      UPDATE public.groups SET created_by = successor
        WHERE id = owned_group.id AND created_by = OLD.id;
      IF NOT EXISTS (
        SELECT 1 FROM public.group_members
        WHERE group_id = owned_group.id AND user_id <> OLD.id
          AND role = 'owner' AND status = 'active'
      ) THEN
        UPDATE public.group_members SET role = 'owner'
          WHERE group_id = owned_group.id AND user_id = successor;
      END IF;
    END IF;
  END LOOP;

  -- Shared activities remain usable; personal activities and their evidence go.
  UPDATE public.activities a SET created_by = g.created_by
    FROM public.groups g
    WHERE a.group_id = g.id AND a.created_by = OLD.id;
  DELETE FROM public.activities WHERE created_by = OLD.id;

  -- Retain group balances and accounting amounts without the deleted identity.
  -- Replace free text and idempotency keys that might identify the former user.
  UPDATE public.point_transactions
    SET user_id = NULL, activity_participant_id = NULL,
        reason = 'Former member transaction', idempotency_key = 'deleted-account:' || id::text
    WHERE user_id = OLD.id;
  -- Other users' notifications can contain this user's name/ID in free text.
  DELETE FROM public.notifications
    WHERE payload::text LIKE '%' || OLD.id::text || '%';
  RETURN OLD;
END $$;

REVOKE ALL ON FUNCTION public.jomo_prepare_account_deletion() FROM PUBLIC;
DROP TRIGGER IF EXISTS jomo_prepare_account_deletion ON public.users;
CREATE TRIGGER jomo_prepare_account_deletion BEFORE DELETE ON public.users
  FOR EACH ROW EXECUTE FUNCTION public.jomo_prepare_account_deletion();

CREATE OR REPLACE FUNCTION public.jomo_delete_app_account()
RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = ''
AS $$
BEGIN
  DELETE FROM public.users WHERE id = OLD.id;
  RETURN OLD;
END $$;
REVOKE ALL ON FUNCTION public.jomo_delete_app_account() FROM PUBLIC;

-- An ordinary PostgreSQL installation has no auth schema. Supabase does.
DO $$
BEGIN
  IF to_regclass('auth.users') IS NOT NULL THEN
    -- Enforce the identity link for new writes, including requests that began
    -- before deletion. NOT VALID tolerates old local/demo rows without deleting them.
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
      WHERE conrelid = 'public.users'::regclass AND conname = 'fk_jomo_user_auth') THEN
      EXECUTE 'ALTER TABLE public.users ADD CONSTRAINT fk_jomo_user_auth
        FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE NOT VALID';
    END IF;
    EXECUTE 'DROP TRIGGER IF EXISTS jomo_delete_app_account ON auth.users';
    EXECUTE 'CREATE TRIGGER jomo_delete_app_account BEFORE DELETE ON auth.users
      FOR EACH ROW EXECUTE FUNCTION public.jomo_delete_app_account()';
  END IF;
END $$;

UPDATE public.alembic_version SET version_num = 'c8e31a04d912' WHERE version_num = 'b7d210c42f01';
COMMIT;
