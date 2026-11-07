# Deploy JOMO on Vercel and Supabase

JOMO uses separate Vercel projects for the Next.js frontend and containerised backend,
with the existing Supabase project for authentication, PostgreSQL and private photos.

Follow [Vercel backend setup](vercel-backend.md) for the complete migration procedure.
Use Root Directory **backend** and framework **Container**, not native FastAPI, so
Tesseract and the English model are installed. Container runtime currently is beta.

Set private credentials only in the backend project. Once its health endpoint works,
set BACKEND_API_URL in the frontend to the assigned backend origin and redeploy.
Do not keep the former Render URL in a public API override.

The daily protected cleanup schedule replaces the persistent worker. Read the guide's
retention, rate-limit and hosted-test limitations before opening public registration.
No live Vercel deployment or hosted settings were changed by preparing these files.
