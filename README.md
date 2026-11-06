# JOMO

A Next.js frontend, FastAPI backend and PostgreSQL database for intentional offline time.

## Current prototype

The rebuilt application includes Supabase email/password authentication, profiles and preferences, personal and shared gardens, custom activities and voluntary focus timers, friends/groups, usage insights and text privacy screening. Authorization and rewards are enforced by the backend.

Fresh setup creates **30 empty application tables**. No sample accounts, shop items, quests, missions or transactions are inserted. Catalogue auto-seeding is disabled. Users and their personal gardens are created only when someone signs in and opens their account. Activities can be created from the Activities page even when the quest catalogue is empty.

Photo storage is not implemented in this prototype. Personal activities use the existing no-photo completion flow; group activities can use peer confirmation. Text screening uses Microsoft Presidio Analyzer and Anonymizer exclusively. If Presidio is unavailable, the API reports an error instead of switching engines.

## Run locally

Prerequisites: Python 3.12+, Node.js 20.9+ and npm.

```powershell
.\scripts\setup-dev.ps1
```

To use Supabase, fill `backend/.env` using `docs/deployment.md`, then start these in separate terminals:

```powershell
.\scripts\start-prototype-backend.ps1
```

```powershell
.\scripts\start-prototype-frontend.ps1
```

For a local preview without cloud access, add `-LocalPreview` to **both** start commands. Open http://localhost:3000/login and choose **Open local preview**. This uses a separate local SQLite database and creates a new identity only when clicked. Local identities are disabled for hosted databases and production. Use Supabase sign-up/sign-in for a lasting account.

## Deployment

See [deployment configuration and exact environment variables](docs/deployment.md).

- Vercel project root: `frontend`.
- Render blueprint: `render.yaml`; backend root: `backend`.
- Supabase: create empty tables using `supabase/schema.sql` in a fresh project's SQL Editor, or run `python -m app.db.setup` from `backend` with your connection configured. Use one method, not both on an unversioned existing schema. The SQL script also records the migration version, so later migration checks are repeatable.

Never commit `.env`, database passwords or local database files. Example files have no project credentials.

## Verification

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm test
npm run typecheck
npm run lint
npm run build
```

The backend tests use disposable databases, mocked Supabase responses and the real Presidio Analyzer/Anonymizer. Install the English model with `python -m spacy download en_core_web_sm` to test named-entity recognition as well. Without a model Presidio can still run its pattern recognisers and reports that limitation. Tests do not prove that a remote project or deployment is reachable.

To regenerate the schema without contacting a database, run `python scripts/export-schema.py` from the repository root with backend dependencies installed.
