# JOMO — Database Schema Reference

The current database models 32 application tables, implemented with SQLAlchemy and
migrated with Alembic to `d91e7c20b403`.

The table list below describes the original core tables; later migrations add
quests/progression, private-photo deletion retries and photo-access metadata.
Use `python -m app.db.setup` from `backend/` to migrate/verify, or add `--check-only`
for read-only verification. Setup does not seed application rows. The live database
revision has not been checked in this implementation session. See
[prototype setup](prototype-setup.md) for the existing-database upgrade order.

The latest additions are `storage_deletions` (opaque object keys and retry counts,
server-only) and `data_access_events` (photo subject/actor, purpose, resource and
time, server-only). Both have RLS enabled. Private photo bytes live in Storage,
not PostgreSQL. User preferences add an onboarding acknowledgement timestamp;
group invitations add an optional recipient ID.

| Table | Purpose | Primary Key | Key Invariants |
|---|---|---|---|
| `users` | Profile & identity | UUID | Matches auth provider ID |
| `user_preferences` | User settings & toggles | user_id (FK) | 1-to-1 with users |
| `friendships` | Accepted friend relations | UUID | `user_low_id < user_high_id`, canonical ordering |
| `friend_requests` | Outgoing friend requests | UUID | Unique pending between sender and receiver |
| `groups` | Friend circles | UUID | Invite-only / private |
| `group_members` | Group membership | (group_id, user_id) | role in ('owner', 'admin', 'member') |
| `group_invites` | Token-based invites | UUID | Stores SHA-256 hash, not plaintext token |
| `activities` | Offline activities | UUID | Personal (group_id=NULL) vs Group (group_id!=NULL) |
| `activity_participants`| Participant records | UUID | Unique (activity_id, user_id) |
| `activity_check_ins` | Coarse location proofs | UUID | Opt-in consent required; 24h retention |
| `focus_sessions` | Voluntary focus timer | UUID | Linked to participant |
| `proof_submissions` | Photo / group proof metadata | UUID | Never stores raw bytes in DB; private storage key |
| `proof_confirmations` | Peer proof review | UUID | Cannot confirm own proof |
| `usage_summaries` | Daily aggregated screen time | UUID | Unique (user_id, usage_date, source) |
| `garden_catalog_items`| Shop inventory items | UUID | seed, plant, pet, decoration |
| `gardens` | Personal & group sanctuaries| UUID | Personal (user_id!=null) vs Group (group_id!=null) |
| `garden_items` | Acquired inventory | UUID | Linked to garden and catalog item |
| `point_transactions` | Immutable points ledger | UUID | Unique idempotency_key, amount != 0 |
| `notifications` | In-app user notifications | UUID | No sensitive PII in payloads |
| `consent_records` | Regulatory audit log | UUID | Singapore PDPA alignment |
| `screening_events` | Privacy screening audit | UUID | No raw user text stored |
