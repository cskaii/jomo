# JOMO — Change Log

## 2026-11-08 — Remove the backend connection overlay

Removed the global “Connecting to JOMO…” screen and its component from the root
layout at the user's request. Connection retries and session-preservation behaviour
remain active; normal page loading and error feedback remain available.

## 2026-11-07 — Prepare backend migration from Render to Vercel

Added a Vercel Container deployment with Dockerfile.vercel and Container preset,
preserving native Tesseract, Presidio and the English model. This uses Vercel's
Container beta rather than pretending the native Python preset installs OS packages.
Production uses persistent Supabase; serverless SQLite is rejected. Supabase data
and private photos do not need to move. No deployed URL or secrets were invented.

Added SERVERLESS_MODE: AI initialisation is lazy, the endless retention worker is
disabled, database connections use NullPool/timeouts and prepared statements are
disabled for transaction-pooler compatibility. Vercel startup does not migrate the
database; reviewed SQL/operator migration is a separate explicit step.

Added a Bearer-secret-protected daily retention job with a bounded storage-deletion
budget and backlog count. CRON_SECRET must contain at least 32 characters; browser
sessions/query parameters cannot authorise it. Daily cron fits Hobby limits but
means physical deletion can occur a day after access expiry or later on failure;
the privacy notice and deployment guide explain this. Updated the notice's provider
description to Vercel and removed the obsolete Render Blueprint.

See docs/vercel-backend.md for backend Container setup, exact environment variables,
PORT, daily schedule, database revision checks, frontend BACKEND_API_URL change,
private-key isolation and hosted acceptance checks. Container runtime is beta and
still scales down; this migration does not guarantee zero cold starts.

Added regression tests for scheduled-job authentication, bounded cleanup and
serverless startup without loading AI/launching an endless worker. Local Docker
CLI is present but its Linux daemon is not running, so a container image build and
live Vercel deployment cannot be verified here. Hosted OCR/cron/credential checks
remain required; no hosted project settings were changed.

Verification: full backend suite 167 passed, 5 skipped (disposable hosted-PostgreSQL
and native Windows Tesseract requirements); frontend TypeScript and changed-page
ESLint passed. Checked Container config JSON, daily schedule, separate migrations
and Docker exclusions for private environments, local databases and caches.

## 2026-11-07 — Handle backend wake-up without losing login

Fixed the API error path that cleared a session when token refresh failed due to
a temporary outage. Login profile loading also preserves a successfully created
session on temporary failure. Confirmed invalid credentials still expire sessions;
a late refresh response cannot restore credentials after logout/account changes.

Added a shared, bounded public readiness probe and illustrated connection screen.
Login, signup, recovery and session refresh wait for readiness before sending their
request. Failed GET requests can wait for the backend and retry once. Purchases,
uploads and other mutations are not automatically replayed after a timeout.
The connection wait stops after approximately 90 seconds and allows manual retry.
No credentials are sent to readiness probes and no periodic keep-alive is used.

This improves handling of Render cold starts; it does not disable free hosting's
sleep policy. Deployment to another host or an always-running plan is separate.
Added regression coverage for outages, invalid refresh, logout during refresh,
safe read retries, non-replayed purchases, shared probes and connection deadlines.

## 2026-11-07 — Remove prototype wording from the website

Removed the “Local prototype” footer label and replaced visible prototype wording
in Privacy Guardian and the public privacy notice with JOMO wording. Updated the
default operator label and environment example to match. This removes development
branding while preserving the privacy notice's actual limitations and contact
requirements. Internal module names are unchanged.

## 2026-11-07 — Complete the website prototype and add PDPA safeguards

### 1. Make manual check-ins useful in Insights

**Changed:** Manual screen-time entries now have a visible saved receipt,
7/30-day history, daily totals, social/category breakdown, intention comparison,
edit/delete controls and a shortcut to the last saved date. Offline activity totals
remain a separate section. Errors explain when a save succeeded but refresh failed.

**Why:** The previous save flow gave little visible feedback and could be confused
with offline activity time. A record should be findable, correctable and removable.

**How:** Updated `Insights.tsx` and `UsageService`; added owner-scoped manual-record
deletion, social/total validation, future-date checks and account-timezone dates.
Summaries select one record per date, prioritising a manual correction rather than
double-counting imported/native values. Manual entries never award activity coins.

### 2. Complete activity, timer and reward flows

**Changed:** Repeated starts resume without resetting time; focus sessions resume;
repeated completion/end requests do not duplicate rewards. Ending an activity
closes running focus timers. Personal no-proof completion awards eligible points
automatically; photo/peer-review completion uses the same reward path. Accepted
evidence completes the activity once no participation remains outstanding.

**Why:** Refreshes/retries should not reset elapsed time, leave timers running or
produce extra coins. Completion needs a predictable result visible to the user.

**How:** Server timestamps, lifecycle checks, PostgreSQL row locks, the existing
unique reward ledger key and transactional reward/notification writes. Rejoining
resets the participation start, preventing departed time from being rewarded.
Shared activity ending is limited to the creator or a participating owner/admin;
the UI reflects that permission. Personal time is described as self-reported.

### 3. Implement optional one-time location check-ins

**Changed:** Active participants can explicitly share one approximate location and
see its receipt/expiry, remove it, or continue without location. Permission denial,
timeouts and inaccurate readings have useful messages. Turning location off in
Settings removes stored coordinates and blocks new check-ins.

**Why:** The prototype needs a working voluntary check-in without background
tracking or unnecessary disclosure of precise location.

**How:** Browser `getCurrentPosition` with a timeout; settings and per-request
consent gates; fresh timestamp/finite-coordinate/accuracy checks; rounding to three
decimal places; one record per participant/activity. Coordinates stay server-side
and are not returned to peers. Access expires after 24 hours; cleanup removes rows.
Location sharing alone never awards coins. Consent/withdrawal metadata is recorded.

### 4. Connect private activity photo evidence

**Changed:** Actual photo selection, local preview, upload progress, private previews,
evidence status, peer approve/decline and evidence removal replace the placeholder
storage-key flow. A group participant cannot approve their own evidence.

**Why:** Proof submission previously could not store an actual file and a fabricated
storage key was not trustworthy evidence of an upload.

**How:** FastAPI receives up to 2 MiB JPEG/PNG/WebP, decodes at most 8 million pixels,
checks the real format and re-encodes to JPEG without EXIF/GPS/comments. Opaque
random filenames go to a private Supabase bucket using the server-only secret key.
Authorised uploader/reviewer previews use 60-second signed links; expired evidence
is denied. Photo consent and minimal storage/preview access events are recorded.
The legacy direct-upload URL returns a clear migration error; fabricated keys are
rejected. Personal photos are self-reported evidence, not authenticity verification.

### 5. Deliver useful website notifications

**Changed:** Header notification bell, unread count, recent history, mark-read/all
and friend/invitation actions. Events cover friend requests, invitations, group
changes, proof review/decisions and rewards. Resolved social notices lose stale actions.

**Why:** Users need to find requests and review/reward outcomes inside the website
without requiring an extension or device push service.

**How:** Owner-scoped notification APIs and safe internal links; creation respects
the notification preference. Visible-tab/focus polling about every 20 seconds;
latest 50 notices retained for 30 days. No messages/emails/push were sent externally.

### 6. Finish group administration and shared-garden transparency

**Changed:** Owner/admin invitation management, targeted in-app invitations, revoke
controls, pending requests, owner role/member management and ownership transfer.
Personal/shared gardens now expose a readable coin history with member attribution.

**Why:** A usable shared garden needs controlled membership and a clear explanation
of who spent/earned its collective coins.

**How:** Backend role checks and locked group mutations; receiver-bound invitations,
expiry/use/revocation checks, duplicate acceptance protection and blocked re-entry
for removed members. Rejoining after leaving gives member privileges. A sole-owner
departure archives the group and revokes invitations. Existing shared purchases
deduct the selected group's balance; moving planted items remains free. History
and garden/activity changes refresh while visible, normally about every 15 seconds.

### 7. Make onboarding and personalisation consistent

**Changed:** An inline first-use introduction sets display name, timezone and daily
intention and links the privacy notice. Users can defer it. Saving a name refreshes
the account greeting. Optional data collection is not silently enabled.

**Why:** New accounts need a short explanation of manual Insights, activities and
gardens, with the correct account name and calendar day.

**How:** Added onboarding timestamp/API and an explicit privacy-notice acknowledgement;
separate profile/preference requests, IANA timezone validation and a profile-refresh
event. Offline summaries date completions in the configured account timezone.
Existing graphical tab/login loaders and two-hour quiz cooldown are preserved.

### 8. Add personal-data controls and clarify Guardian

**Changed:** Settings offers account JSON export, removal of all proof photos and
screening-history cleanup, alongside the existing protected account-deletion flow.
Text Guardian now requires explicit server-validated consent, consistent with file
screening. Guardian remains explicit submission, with redacted results/downloads.

**Why:** Users need practical access, correction and withdrawal tools. A frontend
checkbox alone must not allow the backend consent requirement to be bypassed.

**How:** Owner-linked export excludes storage keys, invite-token hashes, idempotency
keys and others' proof files; JSON responses are not cached. Photo removal revokes
new access and queues private-object removal. Screening keeps category/event
metadata, not submitted content, and expires after 30 days. Formal access/disclosure
history and correction requests still require the operator process documented below.

### 9. Make retention and account cleanup real

**Changed:** Periodic expiry cleanup, durable storage-deletion retries, a trusted
operator command and database-trigger coverage for cascade deletions. Failed or
uncertain uploads are also queued for removal, including a timeout after Storage
accepted a file. Private photo access metadata has a 366-day maximum product period.

**Why:** Removing a database reference alone does not remove a file; account deletion
and provider failures must not silently leave accessible evidence behind.

**How:** `RetentionService`, `StorageDeletion`, `DataAccessEvent`, a background worker
approximately every 60 seconds and `python -m app.db.retention [--check-only]`.
PostgreSQL triggers queue old object keys on proof deletion/key changes, including
account cascades. Existing atomic Supabase Auth deletion/ownership-transfer rules
preserve other members' assets and anonymise former-member ledger attribution.
Raw Uvicorn access logs are disabled in Docker; metadata-only auditing remains.

### 10. Prepare deployment and PDPA operation

**Changed:** Public `/privacy` notice with real operator/contact configuration,
separate consent/withdrawal explanations, purpose/viewer/retention/provider details
and explicit limitations. Production optional photo/location sharing fails closed
until a privacy contact is configured. Added setup and operating documentation.

**Why:** PDPA readiness needs both privacy-preserving implementation and accountable
operation. A checkbox, an approximate coordinate or a passing test is not legal
certification.

**How:** New Render settings `PRIVACY_CONTACT_EMAIL`, `PRIVACY_ORGANISATION` and
`STORAGE_BUCKET`; reuse the backend-only `SUPABASE_SECRET_KEY`. Optional
`PROOF_RETENTION_DAYS` defaults to 7. Migration `d91e7c20b403`, fresh `schema.sql`,
existing-database `prototype_upgrade.sql` and private-bucket `storage_setup.sql`.
Updated OpenAPI and deployment/database documentation. No production data or
hosting configuration was modified during implementation.

Read **[prototype setup](docs/prototype-setup.md)** for exact SQL revision order,
Render values, deployment and two-account acceptance checks. Read
**[PDPA readiness](docs/pdpa-readiness.md)** for DPO/accountability, formal access and
correction, provider/overseas-transfer safeguards, backups, intended audience,
retention monitoring and incident handling. The periods above are product choices,
not retention periods prescribed by PDPA. Sleeping hosts/outages delay physical
cleanup; already issued signed links remain usable briefly until expiry/deletion.

### Verification

| Check | Result |
| --- | --- |
| Backend full regression suite | 164 passed, 5 skipped. Includes real Presidio/English model checks and new consent, ownership, manual usage, expiry, retry, private-file and reward tests. |
| Frontend unit/regression checks | 52 passed. |
| ESLint and TypeScript | Passed. |
| Next.js production build | Passed; all 18 static pages generated, plus dynamic activity/group/focus routes. Used a disposable copy because OneDrive restricted build output directory creation; production source config unchanged. |
| PostgreSQL/PLpgSQL in disposable PGlite | Fresh 32-table schema/RLS, idempotent existing-database upgrade, atomic Auth/account/file-queue rollback, ownership transfer/shared-asset preservation, stale-profile prevention and restrictive private bucket policy passed. |
| Headless Chrome production UI | Onboarding/name refresh, screen-time save/edit/delete receipts, notice actions/count, one-time consent/check-in removal, photo local preview/upload/removal, account export/privacy controls, Guardian consent/redacted output and mobile privacy/Insights checks passed using synthetic intercepted APIs. No uncaught browser errors. |
| Existing garden Chrome regression | Shared purchases spend group coins, collection planting works, and mouse/keyboard movement saves personal/shared plant positions without charging coins. |

The five skipped backend tests require a configured disposable PostgreSQL connection
(four) or native Tesseract on this Windows host (one). PostgreSQL trigger/RLS logic
was separately exercised in PGlite. Docker installs Tesseract; native OCR execution
still needs deployment verification. Supabase Storage/Auth transport tests use fakes,
and browser checks intercept APIs: they do not prove live credentials, quotas,
network behaviour, backups, multi-session PostgreSQL concurrency or legal compliance.
The hosted two-account acceptance check remains necessary after deploying.
