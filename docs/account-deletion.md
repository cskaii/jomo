# Account deletion setup

The Settings page now includes **Delete account**. Users must enter their current
password and type `DELETE`. The server uses the authenticated identity; clients
cannot supply someone else's user ID.

## Supabase

1. Open your JOMO project, then **SQL Editor > New query**.
2. Copy the complete contents of `supabase/account_deletion.sql` and run it once.
   This installs deletion rules; it does not delete any current accounts. It is
   safe to rerun on the same migration version. Do not rerun `supabase/schema.sql`
   against an existing database.
3. Open **Settings > API Keys > Publishable and secret API keys**.
4. Copy an existing **secret** key, or create one for the Render backend. Its value
   begins with `sb_secret_`. Do not use the publishable key for account deletion.

No Supabase environment variable, Edge Function, or Realtime setting is needed.
The secret key stays out of SQL. Do not paste it into a query or commit it to Git.

## Render

Open the JOMO backend service, then **Environment > Add environment variable**:

| Key | Value |
| --- | --- |
| `SUPABASE_SECRET_KEY` | The full `sb_secret_...` key from the same Supabase project |

Save and redeploy the backend with the new code. Keep the existing
`AUTH_ISSUER_URL`, `AUTH_PUBLIC_KEY`, and `DATABASE_URL` settings. In particular,
do not replace `AUTH_PUBLIC_KEY` with the secret key.

For local backend testing, add the same variable to your private `backend/.env`.
The variable is documented, with an empty value, in `backend/.env.example`.

There is **no new Vercel or frontend environment variable**. Deploy the updated
frontend to show the Settings control.

The Render startup already runs Alembic migrations. It can install the database
changes automatically if its PostgreSQL connection has permission to create the
Auth trigger. The SQL Editor script is the manual alternative, and updates the
same Alembic revision so Render does not apply the migration twice.

## What is removed or preserved

- Supabase Auth login and the JOMO user/profile row are hard-deleted together.
- Personal garden, personal coins/items, personal activities, participation,
  focus sessions, check-ins, proof submissions, preferences, usage entries,
  screening records, friendships, quests, XP, and notifications are removed by
  database cascades. Review attribution is cleared and the user's confirmation
  records are removed.
- Remaining members keep shared gardens, plants, pets, balances, and shared
  activities. Purchases are not refunded when an account is deleted. Shared
  ledger amounts remain, with the former user's ID, participant reference, and
  descriptive text removed.
- If ownership needs transferring, an active existing owner/admin is preferred,
  then the longest-standing active member. Removed or departed members cannot
  inherit ownership. An affected group with no other active members is deleted.
- A cleanup failure rolls back the Supabase Auth deletion, rather than leaving a
  usable login with partially removed application data.
- Existing tokens are checked with Supabase on every backend request. The new
  identity foreign key also prevents requests already in progress from creating
  an orphan profile after deletion.

Current photo uploads are disabled in this project. If Supabase Storage uploads
are enabled later, implement object cleanup too: Supabase can reject deletion of
users who still own Storage objects. Backups follow your database retention
settings; this feature deletes live records, not historical backups.

## Verify after deployment

Use a disposable account, not your main account. Join a group with another test
account, buy an item using group coins, and delete the first account through
Settings. Confirm that its email can no longer sign in, its UUID is absent from
**Authentication > Users** and **Table Editor > users**, and the remaining member
still has the shared garden, purchased item, and unchanged group coin balance.

The deletion endpoint intentionally stays unavailable until both the private key
and the database triggers are configured. A wrong password never calls the admin
delete API. An incorrect/missing `DELETE` confirmation is rejected.
