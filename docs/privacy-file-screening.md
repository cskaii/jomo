# Deploy image redaction and CSV/JSON screening

Privacy Guardian now supports Microsoft Presidio Image Redactor and Presidio Structured alongside its existing Analyzer and Anonymizer. The same English spaCy model and Singapore recognisers are reused across all features. No additional AI API key is required.

## Render

Commit and push the changes to `main` first. In the existing JOMO service, open Settings, find Source under Build, and choose Edit. Select the current repository and change the runtime to Docker. Configure:

| Setting | Value |
|---|---|
| Branch | `main` |
| Root Directory | `backend` |
| Dockerfile Path | `Dockerfile` |
| Docker Build Context Directory | `.` |
| Docker Command | Leave empty |
| Health Check Path | `/api/health` |

These paths are relative to Root Directory. If the dashboard displays `backend/` before an input, do not type `backend/` a second time. The resulting Dockerfile path is `backend/Dockerfile`, and the build context is the `backend` directory.

Docker now handles package installation, Tesseract OCR, the English model, migration checks and the Uvicorn start command. The old Python Build/Start commands are not used by this Docker setup.

Set these environment variables:

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `AI_PRESIDIO_ENABLED` | `true` |
| `AI_SPACY_MODEL` | `en_core_web_sm` |
| `REQUEST_MAX_BODY_BYTES` | `3145728` |
| `DEV_AUTH_ENABLED` | `false` |
| `AUTO_SEED_CATALOG` | `false` |

Keep the existing `DATABASE_URL`, Supabase Auth settings, `FRONTEND_URL=https://jomo-xi.vercel.app` and `CORS_ORIGINS=https://jomo-xi.vercel.app`. The Dockerfile uses Python 3.12; `PYTHON_VERSION` does not select a Docker image's Python version.

Deploy the latest commit. The Docker build installs `presidio-image-redactor==0.0.62` and `presidio-structured==0.0.10` together with the pinned existing Analyzer/Anonymizer packages. Docker caches unchanged installation layers, so subsequent code-only builds can reuse them.

## Supabase

No additional SQL, tables, RLS policies, buckets, extensions or model settings are needed. Supabase continues to supply authentication, PostgreSQL and the existing `screening_events` metadata table. The spaCy model belongs in Render's Docker image, not Supabase.

File contents, original filenames, OCR text and redacted files are not stored in the database or object storage. Successful checks record category names and a screening type (`image` or `structured`). Tesseract's Python wrapper can use temporary processing files inside the container; uploads are not intentionally retained.

## Vercel

Redeploy the frontend from the same commit. Keep `BACKEND_API_URL=https://jomo.onrender.com`, `NEXT_PUBLIC_API_BASE_URL=/api/v1`, and `NEXT_PUBLIC_DEV_AUTH_ENABLED=false`.

Privacy Guardian now has separate PNG/JPEG and CSV/JSON file inputs, explicit consent, a redacted preview, and a download button. Results remain in page memory until cleared or the page is closed. Nothing is written to browser storage.

## Supported files

| Format | Limits | Result |
|---|---|---|
| PNG/JPEG | 2 MiB, at most 4 million pixels | Text regions identified by Presidio are covered; a fresh PNG strips source metadata. |
| CSV | UTF-8, 256 KiB, 1–200 data rows, 50 columns; 100,000 characters total | A flagged column is replaced entirely; the output remains CSV. |
| JSON | UTF-8 object/array, 256 KiB; 2,000 scalar values, depth 12; 100,000 value characters total | Flagged scalar values are replaced; nesting, lists and unflagged primitive types are preserved. |

Individual text values are limited to 10,000 characters. JSON object keys and CSV headers are preserved and are not screened. CSV formula-like cells are escaped before download. Images with oversized output must be resized and retried. This feature detects text PII, not faces; it does not guarantee anonymity or classify harmful content. Only one file scan runs at a time per backend process to bound resource use.

## Verify after deployment

1. Open `/privacy-guardian` and confirm the image and data-file forms are visible.
2. Submit UTF-8 CSV with an email column and a harmless note column. Download the result and verify the email column is replaced.
3. Submit nested JSON containing an email value, a number and a boolean. Verify the email is redacted and the other types and nesting are preserved.
4. Submit a small, clear screenshot containing an email address. Review the covered text and download the PNG.
5. Try each form without consent and test an unsupported file type. Neither should be processed.

`/api/health` checks database readiness; an actual image upload verifies the OCR installation. A 503 `OCR_UNAVAILABLE` indicates missing OCR dependencies or a failed OCR scan. Raw exception messages are never returned to the browser or logged by the application.

## Local development and tests

Install `backend/requirements.txt`, the `en_core_web_sm` model, and the Tesseract executable with English language data. `tesseract --version` must work in the backend's environment. Alternatively build and run the Docker image from the backend directory.

The test suite uses the real Presidio Structured and Image Redactor SDKs. Deterministic OCR word boxes test image masking and metadata removal; an additional native Tesseract integration test runs when the executable is available. It skips when Tesseract is absent. Docker image execution requires a running Docker daemon.
