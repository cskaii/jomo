-- Existing JOMO database upgrade from c8e31a04d912. Safe to rerun at d91e7c20b403.
-- Run storage_setup.sql separately for the private evidence bucket.
BEGIN;
DO $upgrade$
BEGIN
  IF EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = 'c8e31a04d912') THEN
    ALTER TABLE public.user_preferences ADD COLUMN onboarding_completed_at timestamptz;
    ALTER TABLE public.group_invites ADD COLUMN receiver_id uuid REFERENCES public.users(id) ON DELETE CASCADE;
    CREATE TABLE public.storage_deletions (
      storage_key varchar(200) PRIMARY KEY, created_at timestamptz NOT NULL, attempts integer NOT NULL
    );
    CREATE TABLE public.data_access_events (
      id uuid PRIMARY KEY,
      subject_user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
      actor_user_id uuid REFERENCES public.users(id) ON DELETE SET NULL,
      purpose varchar(40) NOT NULL, resource_id uuid NOT NULL, occurred_at timestamptz NOT NULL
    );
    CREATE INDEX ix_data_access_events_subject_user_id ON public.data_access_events(subject_user_id);

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

    UPDATE public.alembic_version SET version_num = 'd91e7c20b403' WHERE version_num = 'c8e31a04d912';
  ELSIF EXISTS (SELECT 1 FROM public.alembic_version WHERE version_num = 'd91e7c20b403') THEN
    RAISE NOTICE 'JOMO prototype upgrade is already installed.';
  ELSE
    RAISE EXCEPTION 'Apply the preceding JOMO migrations, including account_deletion.sql, first. Do not rerun the initial schema on existing data.';
  END IF;
END $upgrade$;
COMMIT;
