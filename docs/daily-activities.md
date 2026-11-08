# Daily activities

The Activities tab loads its progression, library, missions, achievements and
discovery through `GET /api/v1/progression/activities`. This synchronous route
runs database work in FastAPI's thread pool, batches per-user card state and
achievement counts, and commits its assignment changes together. Discovery
reuses the library's card payloads. The frontend uses an account-scoped stable
cache key so returning to the tab shows cached data while refreshing. Deploy the
backend route before the updated frontend; this optimisation requires no new SQL.

`GET /api/v1/quests/discovery` returns three daily quests and three additional
suggested activities, the user's timezone, and the next local midnight in UTC.
Selections are persisted per user and local date, so reloads and other devices
receive the same choices. Items disabled by an administrator are hidden.

Both sections use the quest catalogue and the existing start, complete,
abandon, favourite, XP and garden reward endpoints. Completing a suggestion
counts towards missions and achievements exactly as completing a library quest
does. User-created activities retain their separate completion/evidence flow;
customising a suggestion creates a separate activity, not a quest completion.

Discovery uses combined assignment history across both sections, including
items never started. The selector prioritises the least-shown items, mixes
categories, and avoids the previous assignment when enough alternatives exist.
After the catalogue is exhausted, another rotation begins. Small catalogues may
require consecutive repeats; a catalogue with fewer than six items displays
fewer choices without duplicating an item within the day. Manual library
replays remain allowed once per local day. Daily and weekly mission assignments
use the same history-based rotation over their own definition pools.

The full library, favourites and started quests remain available after midnight.
Mission cards link to the appropriate library category so each goal has usable
choices even when today's discovery picks have different categories. Daily
missions reset at local midnight; weekly missions reset on Monday. Midnight
boundaries use calendar dates in the saved timezone, including DST. The UI
refreshes at the supplied boundary, on returning to the tab, and once per minute
while visible. No background scheduler is needed to generate assignments.

Quest/mission mutations lock the user's database row in PostgreSQL, and reward
ledgers retain their unique idempotency keys. Minute-based goals count recorded
eligible minutes rather than the advertised quest duration. Personal quest
completion remains self-reported; the timer does not prove offline behaviour.

## Database and content

Apply migration `e21b9d73a401` with `python -m app.db.setup` from `backend`
before starting the new code. The table uses a cascading user foreign key and
is private to the backend (RLS enabled; no anon/authenticated table access).
`supabase/schema.sql` is the updated schema for fresh databases only.

Migration does not insert catalogue content. To install the included curated
activities without creating demo users or enabling automatic browsing-time
seeding, run `python -m app.db.seed_activities` from `backend`. It adds missing
quest, mission and achievement definitions, preserving existing definitions and
user progress. Run it after migration and before opening the updated page.

The existing `AUTO_SEED_CATALOG`
setting controls the development starter catalogue (35 quests, 10 daily mission
definitions and 8 weekly definitions). Production must have active catalogue
records installed explicitly; empty catalogues show empty states. Browsing does
not populate a deployment where automatic seeding is disabled.
