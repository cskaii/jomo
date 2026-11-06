# JOMO — Comprehensive Database Design

**Database:** PostgreSQL  
**Recommended implementation:** SQLAlchemy models + Alembic migrations  
**Primary ID format:** UUID  
**Timestamp convention:** `TIMESTAMPTZ`, stored in UTC  
**Source of truth:** Backend and database; the frontend must never independently award points, grant inventory, or determine activity eligibility.

## 1. Database design principles

1. Every user has one individual garden, whether or not they belong to a group.
2. Every group has its own separate shared garden.
3. Personal points and each group's shared points are separate balances.
4. Every activity participant has their own participation and focus-session records.
5. A group member starting an activity does not automatically start or lock other members' devices.
6. Points are recorded in an immutable transaction ledger. Balances are calculated from transactions or maintained as carefully reconciled cached values.
7. Proof, location and privacy data should be collected only when needed and with appropriate consent.
8. Raw messages and sensitive text should not be retained just to support Privacy Guardian. Store scan metadata where possible.
9. The database should distinguish an activity definition from an activity session and an individual participant's completion.
10. Use foreign keys and database constraints rather than relying only on frontend validation.

---

# 2. User accounts and profiles

### `users` — MVP

Stores the main account identity.

| Column | Type | Description |
|---|---|---|
| `user_id` | UUID, PK | Unique user ID |
| `email` | VARCHAR(255), UNIQUE | Login email, if email login is used |
| `username` | VARCHAR(50), UNIQUE | Public username |
| `password_hash` | TEXT, nullable | Password hash; null when using external authentication |
| `auth_provider` | VARCHAR(30) | `local`, `google`, etc. |
| `auth_provider_id` | VARCHAR(255), nullable | External provider's user ID |
| `account_status` | VARCHAR(20) | `active`, `suspended`, `deleted` |
| `email_verified_at` | TIMESTAMPTZ, nullable | Email verification time |
| `created_at` | TIMESTAMPTZ | Account creation time |
| `updated_at` | TIMESTAMPTZ | Last update |

**Constraints:** At least one valid authentication method must be configured. Do not store plaintext passwords.

### `user_profiles` — MVP

Stores information shown in the application.

| Column | Type | Description |
|---|---|---|
| `user_id` | UUID, PK, FK → `users.user_id` | One profile per user |
| `display_name` | VARCHAR(80) | Name displayed in JOMO |
| `avatar_url` | TEXT, nullable | Avatar image |
| `bio` | VARCHAR(250), nullable | Optional short description |
| `timezone` | VARCHAR(50) | User's timezone |
| `preferred_language` | VARCHAR(10) | Interface language |
| `created_at` | TIMESTAMPTZ | Creation time |
| `updated_at` | TIMESTAMPTZ | Last update |

### `user_settings` — MVP

Stores user preferences.

| Column | Type | Description |
|---|---|---|
| `user_id` | UUID, PK, FK → `users.user_id` | Owner |
| `profile_visibility` | VARCHAR(20) | `private`, `friends`, `group` |
| `allow_friend_requests` | BOOLEAN | Whether requests are allowed |
| `allow_activity_invites` | BOOLEAN | Whether activity invitations are allowed |
| `notifications_enabled` | BOOLEAN | Main notification preference |
| `weekly_summary_enabled` | BOOLEAN | Whether to receive a weekly summary |
| `updated_at` | TIMESTAMPTZ | Last update |

### `user_goals` — MVP

Stores a user's personal digital wellbeing goals.

| Column | Type | Description |
|---|---|---|
| `goal_id` | UUID, PK | Goal ID |
| `user_id` | UUID, FK → `users.user_id` | Goal owner |
| `goal_type` | VARCHAR(30) | e.g. `daily_screen_time`, `focus_minutes` |
| `target_value` | NUMERIC(10,2) | Goal value |
| `unit` | VARCHAR(20) | e.g. `minutes` |
| `period` | VARCHAR(20) | `daily`, `weekly` |
| `is_active` | BOOLEAN | Whether the goal is active |
| `created_at` | TIMESTAMPTZ | Creation time |
| `updated_at` | TIMESTAMPTZ | Last update |

### `user_consents` — MVP

Records important permission and consent decisions.

| Column | Type | Description |
|---|---|---|
| `consent_id` | UUID, PK | Consent record |
| `user_id` | UUID, FK → `users.user_id` | User |
| `consent_type` | VARCHAR(50) | e.g. `location`, `photo_processing`, `analytics` |
| `policy_version` | VARCHAR(30) | Version of the notice or policy |
| `granted` | BOOLEAN | Whether consent was granted |
| `granted_at` | TIMESTAMPTZ, nullable | Grant time |
| `withdrawn_at` | TIMESTAMPTZ, nullable | Withdrawal time |
| `created_at` | TIMESTAMPTZ | Record creation |

Keep a history of consent changes rather than overwriting the only record.

---

# 3. Friends and groups

### `friendships` — MVP

Stores friend requests and accepted friendships.

| Column | Type | Description |
|---|---|---|
| `friendship_id` | UUID, PK | Friendship ID |
| `requester_id` | UUID, FK → `users.user_id` | Person sending request |
| `addressee_id` | UUID, FK → `users.user_id` | Person receiving request |
| `status` | VARCHAR(20) | `pending`, `accepted`, `rejected`, `blocked` |
| `created_at` | TIMESTAMPTZ | Request time |
| `updated_at` | TIMESTAMPTZ | Last status change |

**Constraints:**
- Requester and addressee cannot be the same user.
- Prevent duplicate active relationships for the same user pair.
- Normalise the user pair when enforcing uniqueness, so reversed pairs cannot create duplicates.

### `groups` — MVP

Stores friend groups.

| Column | Type | Description |
|---|---|---|
| `group_id` | UUID, PK | Group ID |
| `group_name` | VARCHAR(80) | Group name |
| `description` | VARCHAR(250), nullable | Group description |
| `created_by` | UUID, FK → `users.user_id` | Creator |
| `group_avatar_url` | TEXT, nullable | Group image |
| `status` | VARCHAR(20) | `active`, `archived` |
| `created_at` | TIMESTAMPTZ | Creation time |
| `updated_at` | TIMESTAMPTZ | Last update |

### `group_members` — MVP

Many-to-many relationship between users and groups.

| Column | Type | Description |
|---|---|---|
| `group_id` | UUID, PK, FK → `groups.group_id` | Group |
| `user_id` | UUID, PK, FK → `users.user_id` | Member |
| `role` | VARCHAR(20) | `owner`, `admin`, `member` |
| `membership_status` | VARCHAR(20) | `active`, `left`, `removed` |
| `joined_at` | TIMESTAMPTZ | Join time |

**Primary key:** (`group_id`, `user_id`).

### `group_invitations` — MVP

Stores invitations to join a group.

| Column | Type | Description |
|---|---|---|
| `invitation_id` | UUID, PK | Invitation ID |
| `group_id` | UUID, FK → `groups.group_id` | Target group |
| `invited_by` | UUID, FK → `users.user_id` | Inviter |
| `invite_code_hash` | TEXT, UNIQUE | Hashed invitation code |
| `invited_user_id` | UUID, nullable, FK → `users.user_id` | Specific invitee, if applicable |
| `status` | VARCHAR(20) | `pending`, `accepted`, `rejected`, `expired`, `revoked` |
| `expires_at` | TIMESTAMPTZ | Expiry |
| `created_at` | TIMESTAMPTZ | Creation time |

Store a hash of an invitation code rather than a reusable raw token.

---

# 4. Activities and focus sessions

These tables are central to JOMO. Keep the activity, session, participant and focus-session records separate.

### `activities` — MVP

An activity is a reusable or one-time activity definition, such as "Go for a 30-minute walk".

| Column | Type | Description |
|---|---|---|
| `activity_id` | UUID, PK | Activity ID |
| `created_by` | UUID, FK → `users.user_id` | Creator |
| `group_id` | UUID, nullable, FK → `groups.group_id` | Group activity; null for solo activity |
| `mission_id` | UUID, nullable, FK → `missions.mission_id` | Source mission, if applicable |
| `title` | VARCHAR(120) | Activity title |
| `description` | TEXT | Instructions |
| `category` | VARCHAR(40) | `outdoor`, `creative`, `fitness`, `social`, etc. |
| `suggested_duration_minutes` | INTEGER | Suggested duration |
| `proof_type` | VARCHAR(30) | `photo`, `group_confirmation`, `none` |
| `visibility` | VARCHAR(20) | `private`, `group` |
| `status` | VARCHAR(20) | `active`, `completed`, `cancelled`, `archived` |
| `created_at` | TIMESTAMPTZ | Creation time |

### `activity_sessions` — MVP

A particular occurrence of an activity. Multiple sessions may be created from the same activity definition.

| Column | Type | Description |
|---|---|---|
| `session_id` | UUID, PK | Session ID |
| `activity_id` | UUID, FK → `activities.activity_id` | Activity definition |
| `created_by` | UUID, FK → `users.user_id` | Person who starts/creates the session |
| `status` | VARCHAR(20) | `open`, `in_progress`, `completed`, `cancelled` |
| `scheduled_at` | TIMESTAMPTZ, nullable | Planned start |
| `started_at` | TIMESTAMPTZ, nullable | Session start |
| `ended_at` | TIMESTAMPTZ, nullable | Session end |
| `created_at` | TIMESTAMPTZ | Creation time |

### `activity_participants` — MVP

One row for each person participating in a session.

| Column | Type | Description |
|---|---|---|
| `participant_id` | UUID, PK | Participant record |
| `session_id` | UUID, FK → `activity_sessions.session_id` | Session |
| `user_id` | UUID, FK → `users.user_id` | Participating user |
| `status` | VARCHAR(20) | `joined`, `in_progress`, `submitted`, `approved`, `rejected`, `withdrawn` |
| `joined_at` | TIMESTAMPTZ | Join time |
| `completed_at` | TIMESTAMPTZ, nullable | Completion time |
| `eligible_minutes` | INTEGER, default 0 | Backend-calculated eligible duration |
| `reviewed_by` | UUID, nullable, FK → `users.user_id` | Reviewer, if manual review is used |
| `reviewed_at` | TIMESTAMPTZ, nullable | Review time |

**Constraint:** Unique (`session_id`, `user_id`). A user can participate only once in a particular session unless you deliberately support repeat attempts.

### `focus_sessions` — MVP

Records each participant's own voluntary focus timer.

| Column | Type | Description |
|---|---|---|
| `focus_session_id` | UUID, PK | Focus session ID |
| `participant_id` | UUID, FK → `activity_participants.participant_id` | Participant |
| `started_at` | TIMESTAMPTZ | Timer start |
| `ended_at` | TIMESTAMPTZ, nullable | Timer end |
| `duration_seconds` | INTEGER, nullable | Backend-calculated duration |
| `status` | VARCHAR(20) | `running`, `completed`, `interrupted`, `cancelled` |
| `created_at` | TIMESTAMPTZ | Creation time |

The server should calculate duration from timestamps, enforce reasonable limits and prevent duplicate reward claims.

### `proof_submissions` — MVP

Stores references to evidence submitted for an activity.

| Column | Type | Description |
|---|---|---|
| `proof_id` | UUID, PK | Proof ID |
| `participant_id` | UUID, FK → `activity_participants.participant_id` | Participant |
| `proof_type` | VARCHAR(30) | `photo`, `group_confirmation`, `text_note` |
| `storage_key` | TEXT, nullable | Private object-storage key |
| `description` | TEXT, nullable | Optional explanation |
| `status` | VARCHAR(20) | `pending`, `approved`, `rejected` |
| `submitted_at` | TIMESTAMPTZ | Submission time |
| `reviewed_by` | UUID, nullable, FK → `users.user_id` | Reviewer |
| `reviewed_at` | TIMESTAMPTZ, nullable | Review time |
| `retention_expires_at` | TIMESTAMPTZ, nullable | Planned deletion time |

Do not store publicly accessible photo URLs. Store private storage keys and use controlled access.

### `proof_reviews` — MVP if group confirmation is implemented

Allows more than one group member to review proof.

| Column | Type | Description |
|---|---|---|
| `review_id` | UUID, PK | Review ID |
| `proof_id` | UUID, FK → `proof_submissions.proof_id` | Submitted proof |
| `reviewer_id` | UUID, FK → `users.user_id` | Reviewer |
| `decision` | VARCHAR(20) | `approve`, `reject` |
| `comment` | VARCHAR(250), nullable | Optional comment |
| `created_at` | TIMESTAMPTZ | Review time |

Unique (`proof_id`, `reviewer_id`) prevents duplicate votes by the same reviewer.

### `location_samples` — Optional MVP / future

Only create location records if a feature genuinely needs them and the user has granted permission.

| Column | Type | Description |
|---|---|---|
| `location_id` | UUID, PK | Sample ID |
| `participant_id` | UUID, FK → `activity_participants.participant_id` | Participant |
| `latitude` | NUMERIC(9,6) | Latitude |
| `longitude` | NUMERIC(9,6) | Longitude |
| `accuracy_m` | NUMERIC(8,2), nullable | Reported accuracy |
| `captured_at` | TIMESTAMPTZ | Capture time |
| `expires_at` | TIMESTAMPTZ, nullable | Deletion deadline |

Avoid continuous tracking. For the hackathon, you can omit this table and use photo or group confirmation instead.

---

# 5. Missions and verified places

### `missions` — MVP

A curated catalogue of offline challenges.

| Column | Type | Description |
|---|---|---|
| `mission_id` | UUID, PK | Mission ID |
| `title` | VARCHAR(120) | Mission title |
| `description` | TEXT | Mission instructions |
| `category` | VARCHAR(40) | Mission category |
| `duration_minutes` | INTEGER | Suggested duration |
| `min_group_size` | INTEGER | Minimum participants |
| `max_group_size` | INTEGER, nullable | Maximum participants |
| `proof_type` | VARCHAR(30) | Expected proof |
| `safety_notes` | JSONB | Safety guidance |
| `place_id` | UUID, nullable, FK → `places.place_id` | Suggested verified place |
| `is_active` | BOOLEAN | Whether available |
| `created_at` | TIMESTAMPTZ | Creation time |

### `places` — Optional MVP / future

A curated catalogue of real-world locations. This is the source of truth for approved venues; an AI model must not invent venue records.

| Column | Type | Description |
|---|---|---|
| `place_id` | UUID, PK | Place ID |
| `place_name` | VARCHAR(150) | Name |
| `address` | TEXT | Address |
| `latitude` | NUMERIC(9,6), nullable | Latitude |
| `longitude` | NUMERIC(9,6), nullable | Longitude |
| `place_category` | VARCHAR(50) | `park`, `library`, `community_centre`, etc. |
| `public_access` | BOOLEAN | Whether public access is expected |
| `safety_notes` | TEXT, nullable | Curated notes |
| `source_name` | VARCHAR(100), nullable | Data source |
| `source_url` | TEXT, nullable | Source reference |
| `last_verified_at` | TIMESTAMPTZ, nullable | Last verification |
| `is_active` | BOOLEAN | Whether available |

### `mission_generations` — Future / optional

Records metadata about AI-assisted mission generation, not unnecessary personal conversation content.

| Column | Type | Description |
|---|---|---|
| `generation_id` | UUID, PK | Generation ID |
| `requested_by` | UUID, FK → `users.user_id` | Requesting user |
| `group_id` | UUID, nullable, FK → `groups.group_id` | Optional group |
| `mission_id` | UUID, nullable, FK → `missions.mission_id` | Accepted mission |
| `model_provider` | VARCHAR(50), nullable | Provider |
| `model_name` | VARCHAR(100), nullable | Model |
| `status` | VARCHAR(20) | `generated`, `validated`, `rejected`, `accepted` |
| `created_at` | TIMESTAMPTZ | Generation time |

Do not store raw prompts containing personal data unless there is a clearly justified, consented retention purpose.

---

# 6. Gardens and plant growth

The design must support one individual garden per user and one shared garden per group.

### `gardens` — MVP

| Column | Type | Description |
|---|---|---|
| `garden_id` | UUID, PK | Garden ID |
| `garden_type` | VARCHAR(20) | `individual` or `group` |
| `owner_user_id` | UUID, nullable, FK → `users.user_id` | Individual owner |
| `owner_group_id` | UUID, nullable, FK → `groups.group_id` | Group owner |
| `garden_name` | VARCHAR(80) | Garden name |
| `created_at` | TIMESTAMPTZ | Creation time |
| `updated_at` | TIMESTAMPTZ | Last update |

**Important database constraints:**
- Individual garden: `owner_user_id` must be set and `owner_group_id` must be null.
- Group garden: `owner_group_id` must be set and `owner_user_id` must be null.
- Unique individual garden per user.
- Unique shared garden per group.

Use a database `CHECK` constraint to enforce exactly one owner.

### `garden_plots` — MVP

Available positions for plants and decorations.

| Column | Type | Description |
|---|---|---|
| `plot_id` | UUID, PK | Plot ID |
| `garden_id` | UUID, FK → `gardens.garden_id` | Garden |
| `position_x` | INTEGER | Horizontal position |
| `position_y` | INTEGER | Vertical position |
| `is_unlocked` | BOOLEAN | Whether available |
| `created_at` | TIMESTAMPTZ | Creation time |

Unique (`garden_id`, `position_x`, `position_y`).

### `garden_plants` — MVP

Plants placed in garden plots.

| Column | Type | Description |
|---|---|---|
| `plant_id` | UUID, PK | Plant ID |
| `plot_id` | UUID, FK → `garden_plots.plot_id` | Plot |
| `item_id` | UUID, FK → `item_catalog.item_id` | Seed or plant definition |
| `growth_stage` | INTEGER | Current growth stage |
| `planted_at` | TIMESTAMPTZ | Planting time |
| `last_watered_at` | TIMESTAMPTZ, nullable | Last watering time |
| `matured_at` | TIMESTAMPTZ, nullable | Maturity time |
| `status` | VARCHAR(20) | `growing`, `mature`, `removed` |

Plants should not die because a user stops opening the app. Growth should be positive and non-punitive.

### `garden_assets` — MVP

Stores placed decorations, pets and other garden objects.

| Column | Type | Description |
|---|---|---|
| `asset_id` | UUID, PK | Placed asset ID |
| `garden_id` | UUID, FK → `gardens.garden_id` | Garden |
| `item_id` | UUID, FK → `item_catalog.item_id` | Item definition |
| `position_x` | INTEGER | Horizontal position |
| `position_y` | INTEGER | Vertical position |
| `rotation` | INTEGER, default 0 | Optional rotation |
| `placed_at` | TIMESTAMPTZ | Placement time |

### `garden_contributions` — MVP

Tracks which users contributed to a shared garden.

| Column | Type | Description |
|---|---|---|
| `contribution_id` | UUID, PK | Contribution ID |
| `garden_id` | UUID, FK → `gardens.garden_id` | Garden |
| `user_id` | UUID, FK → `users.user_id` | Contributing user |
| `point_transaction_id` | UUID, FK → `point_transactions.transaction_id` | Related reward transaction |
| `contribution_points` | INTEGER | Contribution amount |
| `created_at` | TIMESTAMPTZ | Contribution time |

This table is useful for group contribution history. It must not grant points a second time; the point transaction is the actual financial-style record.

---

# 7. Items, shop, inventory and JOMO Points

### `item_catalog` — MVP

Master list of every resource, seed, pet, decoration and character accessory.

| Column | Type | Description |
|---|---|---|
| `item_id` | UUID, PK | Item ID |
| `item_name` | VARCHAR(100) | Display name |
| `item_type` | VARCHAR(30) | `resource`, `seed`, `pet`, `decoration`, `character_accessory` |
| `description` | TEXT | Item description |
| `rarity` | VARCHAR(20) | `common`, `rare`, `special` |
| `image_url` | TEXT, nullable | Asset image |
| `is_consumable` | BOOLEAN | Whether use consumes it |
| `metadata` | JSONB | Type-specific settings |
| `is_active` | BOOLEAN | Whether available |
| `created_at` | TIMESTAMPTZ | Creation time |

Examples:
- Water pouch: `resource`
- Flower seed: `seed`
- Bunny: `pet`
- Bench: `decoration`
- Hat: `character_accessory`

Use `metadata` for limited type-specific information such as growth duration, plant stages or cosmetic animation settings. Keep frequently queried fields as normal columns.

### `shop_catalog` — MVP

Controls which items can be purchased and their prices.

| Column | Type | Description |
|---|---|---|
| `shop_item_id` | UUID, PK | Shop listing ID |
| `item_id` | UUID, FK → `item_catalog.item_id` | Listed item |
| `price_points` | INTEGER | JOMO Points price |
| `owner_type_allowed` | VARCHAR(20) | `user`, `group`, `both` |
| `available_from` | TIMESTAMPTZ, nullable | Start of availability |
| `available_to` | TIMESTAMPTZ, nullable | End of availability |
| `quantity_limit` | INTEGER, nullable | Optional stock limit |
| `is_active` | BOOLEAN | Whether listed |

### `inventory` — MVP

Tracks owned items.

| Column | Type | Description |
|---|---|---|
| `inventory_id` | UUID, PK | Inventory row |
| `user_id` | UUID, nullable, FK → `users.user_id` | Personal owner |
| `group_id` | UUID, nullable, FK → `groups.group_id` | Shared group owner |
| `item_id` | UUID, FK → `item_catalog.item_id` | Item |
| `quantity` | INTEGER | Quantity owned |
| `updated_at` | TIMESTAMPTZ | Last update |

**Constraints:**
- Exactly one of `user_id` or `group_id` must be non-null.
- Unique item per owner.
- Quantity cannot be negative.

This avoids an unsafe generic `owner_type` + `owner_id` pair without a real foreign key.

### `point_transactions` — MVP

The immutable ledger for JOMO Points.

| Column | Type | Description |
|---|---|---|
| `transaction_id` | UUID, PK | Transaction ID |
| `user_id` | UUID, nullable, FK → `users.user_id` | Personal wallet owner |
| `group_id` | UUID, nullable, FK → `groups.group_id` | Group wallet owner |
| `amount` | INTEGER | Positive for credit, negative for debit |
| `transaction_type` | VARCHAR(30) | `activity_reward`, `purchase`, `adjustment`, etc. |
| `reference_id` | UUID, nullable | Related business record |
| `idempotency_key` | VARCHAR(150), UNIQUE | Prevents duplicate processing |
| `description` | VARCHAR(250), nullable | Transaction explanation |
| `created_at` | TIMESTAMPTZ | Transaction time |

**Constraints:**
- Exactly one of `user_id` or `group_id` must be set.
- Do not edit or delete a completed transaction to change a balance. Record a reversing transaction instead.
- Use a unique idempotency key so retries cannot grant duplicate points.

A wallet balance can be calculated using `SUM(amount)` grouped by owner. If performance later requires a cached balance table, treat the ledger as the source of truth.

### `item_transactions` — MVP

Tracks item purchases, use and placement.

| Column | Type | Description |
|---|---|---|
| `item_transaction_id` | UUID, PK | Item transaction |
| `user_id` | UUID, nullable, FK → `users.user_id` | Personal owner |
| `group_id` | UUID, nullable, FK → `groups.group_id` | Group owner |
| `item_id` | UUID, FK → `item_catalog.item_id` | Item |
| `quantity` | INTEGER | Quantity affected |
| `transaction_type` | VARCHAR(20) | `purchase`, `consume`, `place`, `remove`, `grant` |
| `point_transaction_id` | UUID, nullable, FK → `point_transactions.transaction_id` | Related point transaction |
| `idempotency_key` | VARCHAR(150), UNIQUE | Duplicate protection |
| `created_at` | TIMESTAMPTZ | Transaction time |

### `garden_events` — Optional MVP

Tracks plant growth and garden actions for history and debugging.

| Column | Type | Description |
|---|---|---|
| `event_id` | UUID, PK | Event ID |
| `garden_id` | UUID, FK → `gardens.garden_id` | Garden |
| `plant_id` | UUID, nullable, FK → `garden_plants.plant_id` | Related plant |
| `user_id` | UUID, nullable, FK → `users.user_id` | Actor |
| `event_type` | VARCHAR(30) | `planted`, `watered`, `grew`, `matured`, `decorated` |
| `metadata` | JSONB | Small event details |
| `created_at` | TIMESTAMPTZ | Event time |

---

# 8. Insights and digital usage

The web MVP can show manually entered, imported or demo usage summaries. It cannot continuously read native app usage from a normal browser.

### `usage_sources` — MVP / future

Records where a usage summary came from.

| Column | Type | Description |
|---|---|---|
| `source_id` | UUID, PK | Source ID |
| `user_id` | UUID, FK → `users.user_id` | User |
| `source_type` | VARCHAR(30) | `manual`, `native_android`, `native_ios`, `demo` |
| `source_name` | VARCHAR(80), nullable | Source label |
| `permission_status` | VARCHAR(20) | `granted`, `denied`, `not_requested`, `revoked` |
| `created_at` | TIMESTAMPTZ | Creation time |
| `updated_at` | TIMESTAMPTZ | Last update |

### `app_usage_records` — Optional MVP / future

Individual app usage records, if a supported native integration supplies them.

| Column | Type | Description |
|---|---|---|
| `usage_record_id` | UUID, PK | Record ID |
| `user_id` | UUID, FK → `users.user_id` | User |
| `source_id` | UUID, FK → `usage_sources.source_id` | Usage source |
| `app_identifier` | VARCHAR(255) | App package/bundle identifier |
| `app_display_name` | VARCHAR(100), nullable | Display name |
| `usage_date` | DATE | Local reporting date |
| `duration_seconds` | INTEGER | Usage duration |
| `recorded_at` | TIMESTAMPTZ | Import time |

### `daily_usage_summaries` — MVP

Stores daily totals for Insights.

| Column | Type | Description |
|---|---|---|
| `summary_id` | UUID, PK | Summary ID |
| `user_id` | UUID, FK → `users.user_id` | User |
| `usage_date` | DATE | Reporting date |
| `total_screen_time_seconds` | INTEGER | Total usage |
| `social_media_seconds` | INTEGER | Social media usage |
| `entertainment_seconds` | INTEGER | Entertainment usage |
| `productivity_seconds` | INTEGER | Productivity usage |
| `source_type` | VARCHAR(30) | `manual`, `native`, `demo` |
| `created_at` | TIMESTAMPTZ | Creation time |
| `updated_at` | TIMESTAMPTZ | Last update |

Unique (`user_id`, `usage_date`, `source_type`).

### `weekly_usage_summaries` — Optional

Can be calculated from daily summaries. Do not store it initially unless you need a snapshot for reporting.

| Column | Type | Description |
|---|---|---|
| `summary_id` | UUID, PK | Summary ID |
| `user_id` | UUID, FK → `users.user_id` | User |
| `week_start_date` | DATE | Week start |
| `total_screen_time_seconds` | BIGINT | Weekly total |
| `daily_average_seconds` | INTEGER | Daily average |
| `created_at` | TIMESTAMPTZ | Creation time |

---

# 9. Privacy Guardian and Wellbeing Coach

### `privacy_scan_events` — MVP

Stores scan metadata, not the user's original message.

| Column | Type | Description |
|---|---|---|
| `scan_id` | UUID, PK | Scan ID |
| `user_id` | UUID, nullable, FK → `users.user_id` | User, if logged in |
| `scan_type` | VARCHAR(30) | `text`, `image` |
| `entity_counts` | JSONB | Counts by detected entity type |
| `redaction_applied` | BOOLEAN | Whether redaction was performed |
| `processing_status` | VARCHAR(20) | `completed`, `failed` |
| `created_at` | TIMESTAMPTZ | Scan time |

Do not store original text, detected values or full screenshots in this table. Detection scores are not probabilities and a scan with no detections does not prove content is safe.

### `wellbeing_recommendations` — MVP

Stores recommendations shown to users.

| Column | Type | Description |
|---|---|---|
| `recommendation_id` | UUID, PK | Recommendation ID |
| `user_id` | UUID, FK → `users.user_id` | User |
| `recommendation_type` | VARCHAR(40) | `gentle_break`, `goal_support`, `positive_feedback` |
| `message` | TEXT | Recommendation text |
| `input_summary` | JSONB | Minimal aggregated values used |
| `was_viewed` | BOOLEAN | Whether user viewed it |
| `feedback` | VARCHAR(20), nullable | `helpful`, `not_helpful`, `dismissed` |
| `created_at` | TIMESTAMPTZ | Creation time |

Use aggregated usage figures, not raw message contents or diagnostic labels.

### `safety_reports` — Future / optional

For user-submitted reports of potentially harmful content within JOMO.

| Column | Type | Description |
|---|---|---|
| `report_id` | UUID, PK | Report ID |
| `reported_by` | UUID, FK → `users.user_id` | Reporting user |
| `content_category` | VARCHAR(40) | `harassment`, `scam`, `threat`, etc. |
| `description` | TEXT, nullable | User-provided context |
| `status` | VARCHAR(20) | `open`, `reviewing`, `resolved`, `dismissed` |
| `reviewed_by` | UUID, nullable, FK → `users.user_id` | Reviewer |
| `created_at` | TIMESTAMPTZ | Creation time |
| `resolved_at` | TIMESTAMPTZ, nullable | Resolution time |

Only add this if the product actually includes reporting and review workflows. Avoid automatically labelling people as offenders based on a model output.

---

# 10. Reflections and engagement

### `user_reflections` — Optional MVP

Allows optional weekly reflection without making the app a clinical assessment tool.

| Column | Type | Description |
|---|---|---|
| `reflection_id` | UUID, PK | Reflection ID |
| `user_id` | UUID, FK → `users.user_id` | User |
| `reflection_date` | DATE | Reflection date |
| `mood_label` | VARCHAR(30), nullable | Optional self-selected label |
| `intentionality_rating` | SMALLINT, nullable | Optional user rating |
| `reflection_text` | TEXT, nullable | Optional personal note |
| `created_at` | TIMESTAMPTZ | Creation time |

Keep reflections private by default. Do not expose them to groups.

### `notifications` — MVP

Stores in-app notifications.

| Column | Type | Description |
|---|---|---|
| `notification_id` | UUID, PK | Notification ID |
| `user_id` | UUID, FK → `users.user_id` | Recipient |
| `notification_type` | VARCHAR(40) | `friend_request`, `group_invite`, `activity_invite`, etc. |
| `title` | VARCHAR(120) | Notification title |
| `message` | TEXT | Notification content |
| `reference_type` | VARCHAR(40), nullable | Related entity type |
| `reference_id` | UUID, nullable | Related entity ID |
| `is_read` | BOOLEAN | Read status |
| `created_at` | TIMESTAMPTZ | Creation time |

### `weekly_missions` — Future

For scheduled or rotating missions.

| Column | Type | Description |
|---|---|---|
| `weekly_mission_id` | UUID, PK | Record ID |
| `mission_id` | UUID, FK → `missions.mission_id` | Mission |
| `week_start_date` | DATE | Week |
| `is_active` | BOOLEAN | Availability |
| `created_at` | TIMESTAMPTZ | Creation time |

### `user_mission_progress` — Future

Tracks individual mission progress.

| Column | Type | Description |
|---|---|---|
| `progress_id` | UUID, PK | Progress ID |
| `mission_id` | UUID, FK → `missions.mission_id` | Mission |
| `user_id` | UUID, FK → `users.user_id` | User |
| `status` | VARCHAR(20) | `started`, `completed`, `claimed` |
| `started_at` | TIMESTAMPTZ, nullable | Start time |
| `completed_at` | TIMESTAMPTZ, nullable | Completion time |
| `claimed_at` | TIMESTAMPTZ, nullable | Reward claim time |

Unique (`mission_id`, `user_id`) if each user can complete a mission only once.

---

# 11. Security and operations

### `audit_logs` — MVP

Records important backend actions for debugging and security.

| Column | Type | Description |
|---|---|---|
| `audit_id` | UUID, PK | Audit record |
| `actor_user_id` | UUID, nullable, FK → `users.user_id` | User performing action |
| `action` | VARCHAR(80) | e.g. `group.member_removed`, `reward.issued` |
| `entity_type` | VARCHAR(50) | Affected entity type |
| `entity_id` | UUID, nullable | Affected entity |
| `metadata` | JSONB | Minimal non-sensitive details |
| `ip_hash` | TEXT, nullable | Optional privacy-conscious IP reference |
| `created_at` | TIMESTAMPTZ | Event time |

Never put passwords, access tokens, raw private messages, full NRIC/FIN values or photo contents in audit logs.

### `user_sessions` — Optional

Only required if you implement your own session/token management rather than relying on a managed authentication provider.

| Column | Type | Description |
|---|---|---|
| `session_id` | UUID, PK | Session ID |
| `user_id` | UUID, FK → `users.user_id` | User |
| `refresh_token_hash` | TEXT | Hashed refresh token |
| `expires_at` | TIMESTAMPTZ | Expiry |
| `revoked_at` | TIMESTAMPTZ, nullable | Revocation |
| `created_at` | TIMESTAMPTZ | Creation time |

Do not store raw refresh tokens.

---

# 12. Relationship overview

The main relationships are:

| Parent | Child | Relationship |
|---|---|---|
| `users` | `user_profiles` | One-to-one |
| `users` | `user_settings` | One-to-one |
| `users` | `user_goals` | One-to-many |
| `users` | `friendships` | One-to-many, as requester/addressee |
| `users` | `group_members` | One-to-many |
| `groups` | `group_members` | One-to-many |
| `groups` | `group_invitations` | One-to-many |
| `users` | `activities` | One-to-many, as creator |
| `groups` | `activities` | One-to-many, optional |
| `activities` | `activity_sessions` | One-to-many |
| `activity_sessions` | `activity_participants` | One-to-many |
| `users` | `activity_participants` | One-to-many |
| `activity_participants` | `focus_sessions` | One-to-many |
| `activity_participants` | `proof_submissions` | One-to-many |
| `users` | `gardens` | One individual garden |
| `groups` | `gardens` | One shared garden |
| `gardens` | `garden_plots` | One-to-many |
| `garden_plots` | `garden_plants` | One-to-many over time, subject to plot occupancy rules |
| `gardens` | `garden_assets` | One-to-many |
| `item_catalog` | `inventory` | One-to-many |
| `users` / `groups` | `inventory` | Personal or group ownership |
| `users` / `groups` | `point_transactions` | Personal or group ledger |
| `users` | `daily_usage_summaries` | One-to-many |
| `users` | `privacy_scan_events` | One-to-many, optional user |
| `users` | `wellbeing_recommendations` | One-to-many |
| `users` | `notifications` | One-to-many |

---

# 13. Critical constraints and indexes

These are important enough to implement at database level.

## Ownership and uniqueness

- `user_profiles.user_id` is both primary key and foreign key.
- `user_settings.user_id` is both primary key and foreign key.
- One individual garden per user.
- One shared garden per group.
- A garden must have exactly one owner: either a user or a group.
- An inventory row must have exactly one owner: either a user or a group.
- A point transaction must have exactly one owner: either a user or a group.
- One participant record per user per activity session.
- One inventory row per owner and item.
- One garden plot position per garden.

## Reward integrity

- `point_transactions.amount` cannot be zero.
- `inventory.quantity` cannot be negative.
- Item transaction quantity must be positive.
- `eligible_minutes` cannot be negative.
- Focus session end time cannot precede start time.
- Unique idempotency keys prevent duplicate reward issuance.
- Award points only after the backend validates the participant's completion.
- Perform point-ledger and inventory updates inside a database transaction.
- Use a reversing transaction for refunds or corrections.

## Recommended indexes

| Table | Index |
|---|---|
| `friendships` | `(requester_id, status)`, `(addressee_id, status)` |
| `group_members` | `(user_id, membership_status)` |
| `group_invitations` | `(group_id, status)`, unique `invite_code_hash` |
| `activities` | `(group_id, status)`, `(created_by, created_at)` |
| `activity_sessions` | `(activity_id, status)`, `(started_at)` |
| `activity_participants` | `(user_id, status)`, unique `(session_id, user_id)` |
| `focus_sessions` | `(participant_id, started_at)` |
| `proof_submissions` | `(participant_id, status)` |
| `gardens` | Unique partial indexes on `owner_user_id` and `owner_group_id` |
| `garden_plots` | Unique `(garden_id, position_x, position_y)` |
| `garden_plants` | `(plot_id, status)` |
| `inventory` | Unique owner/item combination |
| `point_transactions` | `(user_id, created_at)`, `(group_id, created_at)`, unique `idempotency_key` |
| `daily_usage_summaries` | Unique `(user_id, usage_date, source_type)` |
| `notifications` | `(user_id, is_read, created_at)` |

---

# 14. What the hackathon team should actually implement

Do not attempt all the tables at once. Start with the tables that make the complete demo work.

## Phase 1 — Core MVP

**Accounts**
- `users`
- `user_profiles`
- `user_settings`

**Friends and groups**
- `friendships`
- `groups`
- `group_members`
- `group_invitations`

**Activities**
- `activities`
- `activity_sessions`
- `activity_participants`
- `focus_sessions`
- `proof_submissions`

**Gardens and gamification**
- `gardens`
- `garden_plots`
- `garden_plants`
- `garden_assets`
- `item_catalog`
- `shop_catalog`
- `inventory`
- `point_transactions`
- `item_transactions`
- `garden_contributions`

**AI and Insights**
- `daily_usage_summaries`
- `user_goals`
- `privacy_scan_events`
- `wellbeing_recommendations`

**Operations**
- `user_consents`
- `notifications`
- `audit_logs`

This is the practical core schema for the JOMO prototype.

## Phase 2 — Optional additions

- `proof_reviews`
- `missions`
- `places`
- `garden_events`
- `user_reflections`
- `usage_sources`
- `app_usage_records`

## Phase 3 — Future native app and advanced features

- `weekly_usage_summaries`
- `mission_generations`
- `safety_reports`
- `weekly_missions`
- `user_mission_progress`
- `user_sessions` if not using managed authentication

---

# 15. Recommended implementation order

1. Create the PostgreSQL database and configure SQLAlchemy.
2. Create `users`, `user_profiles` and `user_settings`.
3. Create groups, friendships, memberships and invitations.
4. Create activities, sessions, participants and focus sessions.
5. Create gardens, plots, plants and assets.
6. Create the item catalogue, shop, inventory and point ledger.
7. Implement reward issuance with database transactions and idempotency.
8. Add proof submissions and notifications.
9. Add daily usage summaries and personal goals.
10. Add Privacy Guardian and Wellbeing Coach metadata tables.
11. Add optional missions, places, reviews and future integrations.
12. Add indexes, constraints, migrations and automated tests.

## Final architectural recommendation

Use PostgreSQL as the single source of truth. Keep the database relational and normalised for users, groups, activities, rewards and inventory. Use JSONB only for flexible metadata such as item settings and minimal audit details—not as a replacement for proper relational tables.

For the hackathon, the most important database flow is:

**User → Group → Activity → Session → Participant → Focus Session → Proof → Reward Transaction → Inventory → Garden.**

If that flow works reliably, JOMO's central experience is demonstrable. The other tables extend the product without forcing the team to build every future feature now.
