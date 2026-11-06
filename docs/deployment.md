# Deploy JOMO: Supabase, Render and Vercel

The source is prepared for these services. A successful local build or mocked authentication test does not mean a hosted deployment is live.

## 1. Supabase

Project URL: `https://dkxbuudvsnsrymitystf.supabase.co`

The supplied session-pooler URI and publishable key are configured in the untracked `backend/.env`. The password is deliberately not repeated in this guide. SQLAlchemy uses the `postgresql+psycopg://` scheme. SSL is required.

For this project, the session-pooler hostname is `aws-0-ap-southeast-2.pooler.supabase.com`, port `5432`, database `postgres`, username `postgres.dkxbuudvsnsrymitystf`.

Create tables with either method:

1. In a **fresh database**, open Supabase SQL Editor and run the entire `supabase/schema.sql` file. It creates 30 application tables, constraints, indexes and row-level security. The only inserted row is Alembic's migration-version bookkeeping; every application table stays empty.
2. Alternatively, from `backend`, run `.venv/Scripts/python.exe -m app.db.setup` using the supplied environment settings. The command migrates and verifies the database without inserting catalogue or demo data.

Do not run the full initial SQL over existing tables. The setup command refuses unversioned application tables rather than guessing their schema or deleting records. No live records were deleted by the rebuild; populated source SQLite files were excluded from the repository.

Browser database access is denied by RLS with no policies. FastAPI uses the private server-side Postgres connection and enforces ownership. The frontend must use FastAPI, rather than writing to the Supabase Data API directly.

Under Supabase Authentication, enable the Email provider. Set the Site URL to the final Vercel production URL. Add redirect URLs:

- `http://localhost:3000/login`
- `http://localhost:3000/reset-password`
- `<VERCEL_PRODUCTION_URL>/login`
- `<VERCEL_PRODUCTION_URL>/reset-password`

Keep email confirmation enabled if you want confirmation before sign-in. No user account is pre-created.

## 2. Render backend

Connect this Git repository and use its `render.yaml` Blueprint, or create a Python Web Service with:

| Setting | Value |
|---|---|
| Root directory | `backend` |
| Build command | `pip install -r requirements.txt && python -m spacy download en_core_web_sm` |
| Start command | `python -m app.db.setup && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health-check path | `/api/health` |

Enter the following environment variables:

| Variable | Exact value or source |
|---|---|
| `PYTHON_VERSION` | `3.12.14` |
| `APP_ENV` | `production` |
| `DATABASE_URL` | Copy the complete `DATABASE_URL` value from your private `backend/.env`; it already has the correct driver, supplied password, pooler and SSL parameters. |
| `AUTH_PROVIDER` | `supabase` |
| `AUTH_ISSUER_URL` | `https://dkxbuudvsnsrymitystf.supabase.co/auth/v1` |
| `AUTH_PUBLIC_KEY` | `sb_publishable_MP3g-8385ESy5JPE_J0V1w_pFsJMH19` |
| `AUTH_AUDIENCE` | `authenticated` |
| `DEV_AUTH_ENABLED` | `false` |
| `AUTO_SEED_CATALOG` | `false` |
| `AI_PRESIDIO_ENABLED` | `true` |
| `AI_SPACY_MODEL` | `en_core_web_sm` |
| `FRONTEND_URL` | Your final Vercel production origin, including `https://`, with no trailing slash. |
| `CORS_ORIGINS` | The same exact Vercel production origin. For several origins, use a comma-separated list. |

Render supplies `PORT`; do not hard-code it. No service-role key or JWT signing secret is required: the backend verifies sessions with Supabase Auth's `/user` endpoint. The session pooler is also used for migrations; do not change its port to `6543`.

Render service URL: `https://jomo.onrender.com`. Deployment branch: `main`. Confirm `https://jomo.onrender.com/api/health` returns `healthy` and `database: connected`. The service URL has been supplied by the owner; this session has not verified its live health.

## 3. Vercel frontend

Import the same repository and use production branch `main`. Choose Next.js, set the Root Directory to `frontend`, and use its `vercel.json`. Install: `npm ci`; Build: `npm run build`.

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `/api/v1` |
| `BACKEND_API_URL` | `https://jomo.onrender.com` |
| `NEXT_PUBLIC_DEV_AUTH_ENABLED` | `false` |

There is no database password in Vercel. `BACKEND_API_URL` is server-only; Next.js proxies `/api/v1/*` to Render. Set it before building and redeploy after changing it, because the rewrite is produced during the build.

Once the Vercel URL is known, update `FRONTEND_URL`, `CORS_ORIGINS` and Supabase redirect URLs above. Render can be deployed after the Vercel project URL is assigned; any first-deploy backend error will resolve after all services and variables are configured.

## 4. Hosted verification

1. Open `/register`, create your own account and confirm the email.
2. Sign in, open Settings and save your display name.
3. Open Activities and create a personal activity. Start it, end it and request completion. Eligible minutes come from server timestamps; a short test should not fabricate rewards.
4. Open Garden. Its balance and activity history should reflect server results. Shop and quest catalogues are intentionally empty until real entries are added.
5. Test sign-out and sign-in again, and use the forgot-password link.
6. A second account must not be able to access the first account's personal garden or private activity.

## Scope

This prototype does not include real photo upload storage, native device/app blocking or background surveillance. Personal activities do not require photos; group activities support peer confirmation. Privacy screening uses Microsoft Presidio Analyzer and Anonymizer only. The Render build installs its small English spaCy model. If the model is absent, Presidio reports pattern-only operation; if Presidio itself fails or is disabled, screening returns HTTP 503 with no substitute detector. Text is processed within the backend and is not retained. Existing Render services must update their Build Command and AI environment variables explicitly; committing render.yaml only updates Blueprint-managed services after a sync.

All database credentials stay in ignored environment files or hosting environment settings. The earlier example Supabase project and its keys were removed from active configuration.

References: https://render.com/docs/deploy-fastapi, https://vercel.com/docs/monorepos, https://supabase.com/docs/guides/database/connecting-to-postgres

## Render outbound IP ranges

If Supabase network restrictions are already enabled, its database allowlist must include Render ranges `74.220.48.0/24` and `74.220.56.0/24` alongside any existing required ranges. These are shared egress ranges, not environment variables. They do not need to be added when no IP restrictions are enabled. No network restrictions were changed by this update.

