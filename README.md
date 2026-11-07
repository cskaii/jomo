# JOMO — Joy of Missing Out

**Less scrolling. More living.**

JOMO helps people make time for offline activities, grow personal and shared gardens, and review information before sharing it. The prototype combines a Next.js frontend, a FastAPI backend, and Supabase authentication and PostgreSQL.

| Application | Address |
|---|---|
| Frontend | [jomo-xi.vercel.app](https://jomo-xi.vercel.app) |
| Backend | [jomo.onrender.com](https://jomo.onrender.com) |
| Backend readiness | [/api/health](https://jomo.onrender.com/api/health) |
| API documentation | [/docs](https://jomo.onrender.com/docs) |

These are the configured deployment addresses. New features become available there after their commits are deployed.

## Features

- **Accounts:** Supabase email/password registration, sign-in, password recovery, profiles and preferences.
- **Offline activities:** Create personal or group activities, use voluntary focus timers, and record completion. The backend calculates eligible minutes and rewards.
- **Gardens:** Personal and shared gardens, a shop, inventory, item placement and a points ledger.
- **Social features:** Friends, groups, invitations and shared gardens.
- **Insights:** Views of recorded usage and completed offline activity.
- **Privacy Guardian:** Explicitly submitted text, images and data files are processed by Microsoft Presidio.

### Loading transitions

Every app entry, including a restored sign-in, shows the personalized seedling welcome for at least 1.8 seconds. Tab and query-based navigation show a 0.9-second page transition even when content is already cached, including Privacy Guardian and preferences. Page requests continue underneath; these visual transitions do not speed up the backend or replace real loading and error states.

### Shared gardens and arranging

Personal and shared gardens use the same immersive garden, store, and collection. Active group members can spend their group's points and plant or move items in its shared collection; personal points and inventory stay separate. Shared gardens refresh every 15 seconds while visible, on return to the tab, or with the refresh button.

Choose **Arrange** to drag a planted item to a new position. Keyboard users can select an item with Tab, use arrow keys to adjust it, Enter to save, and Escape to cancel. Moving never spends coins. Each purchased unit can be planted separately. Backend garden row locks serialize purchases and rewards on PostgreSQL.

### Privacy Guardian

| Component | Purpose | Supported input |
|---|---|---|
| Presidio Analyzer | Detect possible personal information | English text |
| Presidio Anonymizer | Replace detected text spans with `[REDACTED]` | Text-screening results |
| Presidio Image Redactor | Find text with OCR and cover detected regions | PNG and JPEG |
| Presidio Structured | Replace detected values or sensitive columns | UTF-8 JSON and CSV |

All four components reuse the configured English spaCy model and Singapore-specific recognisers. Presidio is the only screening engine; if it is unavailable, the API reports an error rather than substituting another detector. No additional AI API key is required.

The page provides explicit consent, redacted previews, downloads, and controls to clear submitted content and results. Screening records category names, not original text, files or detected values. Originals are not retained in Supabase. The OCR wrapper may use temporary processing files inside the backend container.

### File limits

| Input | Limits and behaviour |
|---|---|
| Text | Up to 10,000 characters; English only |
| PNG/JPEG | Up to 2 MiB and 4 million pixels; output is a PNG with source metadata removed |
| CSV | Up to 256 KiB, 1–200 data rows and 50 columns; flagged columns are replaced entirely |
| JSON | Up to 256 KiB, 2,000 scalar values and nesting depth 12; flagged values are replaced while preserving the surrounding structure |

CSV/JSON values are also limited to 100,000 characters in total and 10,000 characters per individual value. CSV headers and JSON keys are preserved and are not screened. Formula-like CSV cells are escaped before download. One file scan runs at a time per backend process.

Automated screening can miss personal information. OCR does not redact faces, and a result without detections does not establish that a file is safe to share. Harmful-content classification, background monitoring, native app blocking, and activity-photo upload storage are not implemented. Personal activities use the no-photo completion flow; group activities can use peer confirmation.

## Repository layout

| Path | Contents |
|---|---|
| [frontend/](frontend/) | Next.js, React, TypeScript and Tailwind frontend |
| [backend/](backend/) | FastAPI routes, middleware, services, models and tests |
| [backend/Dockerfile](backend/Dockerfile) | Python runtime, Presidio packages, Tesseract OCR and English model |
| [backend/migrations/](backend/migrations/) | Alembic database migrations |
| [supabase/](supabase/) | Schema and optional garden-shop catalogue SQL |
| [shared/](shared/) | Shared frontend enums, contracts and reference fixtures |
| [scripts/](scripts/) | Development setup, startup and schema export helpers |
| [docs/](docs/) | Deployment, database and AI documentation |
| [blueprint.md](blueprint.md) | Product and architecture blueprint |

## Local setup

Prerequisites:

- Python 3.12 or newer, available as `python`.
- Node.js 20.9 or newer with npm.
- Tesseract OCR with English language data, available on `PATH`, for image screening.
- A Supabase project for real-account authentication, or the local preview mode below.

From the repository root on Windows:

```powershell
.\scripts\setup-dev.ps1
.\backend\.venv\Scripts\python.exe -m spacy download en_core_web_sm
tesseract --version
```

The setup script installs Python and frontend dependencies and creates environment files from the examples if they do not already exist. Tesseract is a separate system dependency; the Python packages alone do not install its executable. For container deployment, the Dockerfile installs it automatically.

Configure `backend/.env` using [backend/.env.example](backend/.env.example) and the [deployment guide](docs/deployment.md). Configure `frontend/.env.local` using [frontend/.env.example](frontend/.env.example).

Start these in **separate terminals**, each from the repository root:

```powershell
.\scripts\start-prototype-backend.ps1
```

```powershell
.\scripts\start-prototype-frontend.ps1
```

Open [http://localhost:3000](http://localhost:3000). Local API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Preview without Supabase

Add `-LocalPreview` to both startup commands:

```powershell
.\scripts\start-prototype-backend.ps1 -LocalPreview
```

```powershell
.\scripts\start-prototype-frontend.ps1 -LocalPreview
```

Open `/login` and select **Open local preview**. This uses a separate SQLite database and creates a new local identity when clicked. Local preview identities are disabled for hosted databases and production. Presidio still needs its installed dependencies; image screening also needs Tesseract.

## Database and garden shop

Fresh schema setup creates **30 empty application tables** plus Alembic migration bookkeeping. It does not create sample accounts, activities, transactions, missions or quests. Account onboarding creates the signed-in user's profile, preferences and personal garden.

For a fresh Supabase project, either:

1. Run [supabase/schema.sql](supabase/schema.sql) in Supabase SQL Editor; or
2. Configure the backend connection and run `python -m app.db.setup` from `backend` with its virtual environment active.

The backend also runs migration checks when the Docker container starts. Do not rerun the full initial schema script over existing tables. Setup refuses unversioned application tables instead of dropping them or assuming their structure matches.

To populate the garden store, run [supabase/shop_catalog.sql](supabase/shop_catalog.sql) in SQL Editor. It adds **30 products linked to existing flower, tree, animal and decoration assets**. It preserves existing products and prices, and does not give accounts coins or create inventory. Purchases use points earned through eligible completed activities.

`AUTO_SEED_CATALOG=false` keeps automatic catalogue and demo insertion disabled. See [database setup](docs/db-setup.md) for migration details.

## Deployment

Both hosted services use the `main` branch.

### Render backend

Use [render.yaml](render.yaml), or configure the existing service as follows:

| Setting | Value |
|---|---|
| Runtime | Docker |
| Root Directory | `backend` |
| Dockerfile Path | `Dockerfile` |
| Docker Build Context Directory | `.` |
| Docker Command | Leave empty |
| Health Check Path | `/api/health` |

Docker paths are relative to Root Directory. The resulting Dockerfile is `backend/Dockerfile`. The Dockerfile installs all four Presidio packages, Tesseract and `en_core_web_sm`, then checks migrations and starts Uvicorn using Render's `PORT`.

Set these production environment variables:

| Variable | Value or source |
|---|---|
| `APP_ENV` | `production` |
| `DATABASE_URL` | Supabase session-pooler URI on port `5432`, using `postgresql+psycopg://` and SSL |
| `AUTH_PROVIDER` | `supabase` |
| `AUTH_ISSUER_URL` | `https://<project-ref>.supabase.co/auth/v1` |
| `AUTH_PUBLIC_KEY` | Your project's publishable key |
| `AUTH_AUDIENCE` | `authenticated` |
| `FRONTEND_URL` | `https://jomo-xi.vercel.app` |
| `CORS_ORIGINS` | `https://jomo-xi.vercel.app` |
| `AI_PRESIDIO_ENABLED` | `true` |
| `AI_SPACY_MODEL` | `en_core_web_sm` |
| `REQUEST_MAX_BODY_BYTES` | `3145728` |
| `DEV_AUTH_ENABLED` | `false` |
| `AUTO_SEED_CATALOG` | `false` |

Existing dashboard-managed services must switch to Docker explicitly. Committing `render.yaml` does not automatically reconfigure a service unless it is managed through a synced Blueprint.

### Vercel frontend

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Framework | Next.js |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | Framework default; override off |

| Environment variable | Value |
|---|---|
| `BACKEND_API_URL` | `https://jomo.onrender.com` |
| `NEXT_PUBLIC_API_BASE_URL` | `/api/v1` |
| `NEXT_PUBLIC_DEV_AUTH_ENABLED` | `false` |

Redeploy Vercel after changing `BACKEND_API_URL`: the API rewrite is produced during the build.

### Supabase

Configure the database, Email authentication provider, Site URL and permitted authentication redirects as described in the [deployment guide](docs/deployment.md).

Privacy Guardian's image and structured-file features need **no additional tables, storage buckets or Supabase model settings**. The spaCy model and OCR engine run on Render. Existing row-level security protects direct browser access to application tables; requests go through the backend's authorization checks.

Full instructions: [deployment guide](docs/deployment.md) and [file-screening setup](docs/privacy-file-screening.md).

## Testing and verification

From the repository root:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm test
npm run typecheck
npm run lint
npm run build
```

Backend tests use disposable databases, mocked Supabase authentication responses and the real Presidio SDKs. Image-mask tests use controlled OCR word boxes. The native Tesseract integration test runs when its executable is available; named-entity tests require the English model.

After deployment, test registration and sign-in, activity completion, garden purchases and placement, and Privacy Guardian's text/image/CSV/JSON flows. `/api/health` checks database readiness; an actual image upload verifies the OCR path. Local tests do not establish that a hosted deployment is healthy.

To export the schema without contacting a database, run this from the repository root with backend dependencies installed:

```powershell
.\backend\.venv\Scripts\python.exe scripts\export-schema.py
```

## Credentials and privacy

Keep database passwords and private environment values in ignored local files or hosting environment settings. Do not commit `.env`, `.env.local`, database files, generated output, or dependency directories. The Docker build context excludes local environment files and databases.

Screening is initiated by the user. It does not silently inspect other applications or use submitted content for model training. Review redacted output before sharing it.
