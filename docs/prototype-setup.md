# Complete prototype: deployment and verification

The implementation is local until the code is deployed. No live Supabase,
Render or Vercel settings were changed. Read [PDPA readiness](pdpa-readiness.md)
before opening the prototype to public users.

## Supabase

Back up the database and check its revision:

```sql
select version_num from public.alembic_version;
```

| Current state | Action |
| --- | --- |
| Fresh database without JOMO tables | Run `supabase/schema.sql` once, or migrate using `python -m app.db.setup`. |
| `b7d210c42f01` | Apply `supabase/account_deletion.sql`, then `supabase/prototype_upgrade.sql`. |
| `c8e31a04d912` | Apply `supabase/prototype_upgrade.sql`. |
| `d91e7c20b403` | The prototype upgrade is installed. |
| Another revision/unversioned tables | Inspect migration history first. Never drop tables or rerun the fresh schema to bypass an error. |

Render's Docker startup already runs `app.db.setup`; successful deployment can
apply the Alembic migration instead of the SQL Editor alternative. Both record
the same head. The upgrade preserves existing data, adds onboarding/targeted
invitations, creates private-file deletion retries and photo-access metadata, and
queues photos when proofs/accounts are deleted. There are 32 application tables
plus Alembic bookkeeping, with RLS enabled for all.

Separately run **`supabase/storage_setup.sql`** in SQL Editor. It creates/updates
the private **activity-proofs** bucket with a 2 MB JPEG limit and restricts direct
anon/authenticated access even when older broad Storage policies exist. The backend
accepts JPEG/PNG/WebP, removes metadata and converts them to JPEG before storage.
Do not make this bucket public. No keys belong in SQL.

If starting with an empty shop, run the existing `supabase/shop_catalog.sql` to
register the supplied art assets. It preserves existing catalogue prices/items and
does not grant users coins or create demo activity records.

## Render variables

| Variable | Value |
| --- | --- |
| `SUPABASE_SECRET_KEY` | Backend-only Supabase **Secret key** beginning `sb_secret_`, from Project Settings → API Keys. Reused for account deletion/private Storage. |
| `STORAGE_BUCKET` | `activity-proofs` |
| `PRIVACY_CONTACT_EMAIL` | A real, monitored privacy/DPO email that can be published. |
| `PRIVACY_ORGANISATION` | The actual person or organisation operating JOMO. |
| `PROOF_RETENTION_DAYS` | Optional; default `7`, allowed 1–30. Choose and document the period. |
| `STORAGE_TIMEOUT_SECONDS` | Optional; default `15`, maximum 30. |
| `APP_ENV` | `production` |

Keep existing database, authentication, explicit CORS and frontend URL settings.
`AUTH_ISSUER_URL` is `https://<project-ref>.supabase.co/auth/v1`, not the JWKS URL.
Never put an admin secret in `NEXT_PUBLIC_*`, frontend code, Vercel public variables,
screenshots or Git. Supabase needs no additional environment variable or Realtime
switch. Production optional photo/location collection fails closed until a privacy
contact is configured; this check alone does not establish legal compliance.

Deploy Render, then Vercel with the existing backend rewrite. No new frontend
environment variable is needed. Docker includes Presidio, the English model and
Tesseract. Visit `/api/health` and `/privacy` to verify readiness/contact details.

## Hosted acceptance check (two test accounts)

1. Save/edit/delete screen time in Insights. Confirm it changes screen time and
   does not award coins or increase offline minutes.
2. Complete a personal activity and retry/refresh: one reward only. Join a group
   activity with a second account, request evidence review and approve as the other
   participant. Check the group's balance, purchases, planting/movement and ledger.
3. Enable optional location, consent to a check-in, remove it, then disable the
   setting. Deny browser permission and confirm other activity functions remain usable.
4. Upload a harmless synthetic photo after ending an activity. Test uploader/reviewer
   preview and unrelated-account denial. Remove it and check the deletion backlog.
5. Test friend requests, targeted invitations, owner/admin/member restrictions,
   revoked invitations, ownership transfer and website notification actions.
6. Export and delete a disposable account. Verify Auth/personal records are removed,
   shared assets survive, and private objects are removed by cleanup. Do not delete
   your only production owner account for testing.

Activities/gardens use visible polling (about 15 seconds); in-app notices use about
20 seconds. They are not device push notifications or continuous tracking.

## Retention operation

A worker runs on backend startup and approximately every 60 seconds while it is
running: location 24 hours, photos the configured period, notification/screening
metadata 30 days, minimal photo-access events 366 days. These are product choices,
not statutory PDPA periods. Expired photos cannot be previewed through JOMO while
physical deletion is waiting. Files are deleted through a durable retry queue.

From a trusted backend environment with its private configuration:

```powershell
python -m app.db.retention --check-only
python -m app.db.retention
```

Output contains counts, not keys/personal data. Investigate failed retries and
persistent backlog. Sleeping free services and provider outages delay physical
removal; use an appropriate trusted scheduler/worker where retention depends on it.
Do not expose a public cleanup endpoint. Document backup expiry, reapply deletions
after restore and reconcile orphan files after exceptional provider/database failures.

## Repeat local verification

```powershell
# backend; install requirements and English spaCy model first
python -m pytest tests -q
# frontend
npm run lint
npx tsc --noEmit
node --test tests/*.test.cjs
npm run build -- --webpack
# repository root: disposable PostgreSQL WASM; no hosted database
npm install --prefix frontend/.next-prototype-qa --ignore-scripts --no-audit --no-fund @electric-sql/pglite
node scripts/verify-postgres-schema.cjs
```

`scripts/verify-prototype-browser.cjs` runs Chrome against the production frontend
with synthetic API responses. Set `JOMO_QA_PHOTO` to a generated harmless JPEG;
optionally set `JOMO_QA_FRONTEND` to a disposable build copy and `CHROME_PATH`.
Backend tests use disposable SQLite and a private Storage HTTP fake. PostgreSQL
trigger/RLS tests use PGlite. These checks do not prove hosted service configuration,
quotas/network behaviour or simultaneous multi-session PostgreSQL concurrency;
perform the hosted acceptance check after deployment.
