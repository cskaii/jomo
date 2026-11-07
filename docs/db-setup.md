# Empty database setup

See `docs/deployment.md` for the current project and complete environment mapping.

See [prototype setup](prototype-setup.md) for upgrading an existing database to
`d91e7c20b403` and installing the private activity-photo bucket.

For account deletion on an existing database, see `docs/account-deletion.md` and
run `supabase/account_deletion.sql`, rather than rerunning the initial schema.

From `backend`, with dependencies installed and `backend/.env` filled:

```powershell
.\.venv\Scripts\python.exe -m app.db.setup
.\.venv\Scripts\python.exe -m app.db.setup --check-only
```

For a disposable local SQLite database, explicitly add `--allow-sqlite`. The setup command creates 32 application tables through Alembic and inserts no application rows. It preserves existing records, checks the migration head, and refuses an unversioned existing application schema.

For a fresh Supabase database you can instead run `supabase/schema.sql` in SQL Editor. It contains schema DDL and Alembic bookkeeping only. PostgreSQL RLS is enabled for all application tables; access goes through FastAPI.

The full initial script is for a fresh schema only. Do not drop existing hosted tables to work around a migration error. No deployed database was cleared during this rebuild.
