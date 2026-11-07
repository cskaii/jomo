-- Private photo evidence storage. Run in the JOMO Supabase SQL Editor.
-- This creates/configures a private bucket; it does not grant browser uploads.
BEGIN;
INSERT INTO storage.buckets(id, name, public, file_size_limit, allowed_mime_types)
VALUES ('activity-proofs', 'activity-proofs', false, 2097152, ARRAY['image/jpeg'])
ON CONFLICT (id) DO UPDATE SET public = false, file_size_limit = 2097152,
  allowed_mime_types = ARRAY['image/jpeg'];

-- The backend validates, sanitises and authorises every photo operation.
-- A restrictive policy also blocks this bucket if older broad user policies exist.
DROP POLICY IF EXISTS jomo_private_proofs_server_only ON storage.objects;
CREATE POLICY jomo_private_proofs_server_only ON storage.objects AS RESTRICTIVE
FOR ALL TO anon, authenticated
USING (bucket_id <> 'activity-proofs')
WITH CHECK (bucket_id <> 'activity-proofs');
COMMIT;
