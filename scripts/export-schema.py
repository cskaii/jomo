"""Export schema-only PostgreSQL migrations, including Alembic version metadata.

Run from the repository root: python scripts/export-schema.py
No database connection is opened and no credentials are included in the output.
"""
from io import StringIO
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from alembic import command
from app.db.setup import migration_config

output = StringIO()
config = migration_config()
config.output_buffer = output
config.attributes["database_url"] = "postgresql+psycopg://localhost/postgres"
command.upgrade(config, "head", sql=True)
target = ROOT / "supabase" / "schema.sql"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(
    "-- JOMO: fresh database only. No application data is inserted.\n"
    "-- alembic_version contains migration bookkeeping only.\n" + output.getvalue(),
    encoding="utf-8",
)
print(f"Exported schema to {target}")
