"""Migrate and verify the configured database without inserting application data.

Run from backend: python -m app.db.setup
"""
import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.db.base import Base
import app.models  # register every application table


def migration_config() -> Config:
    return Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))


def setup_database(database_url: str, *, check_only=False, allow_sqlite=False) -> dict:
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql" and not (
        allow_sqlite and url.get_backend_name() == "sqlite"
    ):
        raise ValueError("Configure PostgreSQL, or explicitly use --allow-sqlite for a local test.")
    if url.get_backend_name() == "postgresql" and url.port == 6543:
        raise ValueError("Use a direct or session connection on port 5432 for migrations.")

    connect_args = {"connect_timeout": 10} if url.get_backend_name() == "postgresql" else {}
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    try:
        config = migration_config()
        expected_heads = set(ScriptDirectory.from_config(config).get_heads())
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            existing = set(inspect(connection).get_table_names())
            current = set(MigrationContext.configure(connection).get_current_heads())
            connection.rollback()
            if not check_only:
                # Never stamp an old create_all database and assume it matches.
                if existing.intersection(Base.metadata.tables) and not current:
                    raise ValueError(
                        "Unversioned application tables exist. Review/backup the schema before migration; "
                        "this command will not drop tables or stamp it automatically."
                    )
                config.attributes["connection"] = connection
                command.upgrade(config, "head")
                connection.commit()

        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())
            missing = set(Base.metadata.tables) - tables
            current = set(MigrationContext.configure(connection).get_current_heads())
            if missing or current != expected_heads:
                raise ValueError("Database is not at migration head or application tables are missing.")
            inspector = inspect(connection)
            for name, table in Base.metadata.tables.items():
                columns = {column["name"] for column in inspector.get_columns(name)}
                if set(table.columns.keys()) - columns:
                    raise ValueError(f"Required columns are missing from {name}.")

        with engine.connect() as connection:
            catalog_count = connection.execute(text("SELECT COUNT(*) FROM garden_catalog_items")).scalar_one()
        return {"tables": len(Base.metadata.tables), "revision": ", ".join(sorted(current)),
                "catalog_items": catalog_count, "check_only": check_only}
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Verify without migrating")
    parser.add_argument("--allow-sqlite", action="store_true", help="Explicitly allow a disposable local SQLite database")
    args = parser.parse_args()
    try:
        settings = get_settings()
        result = setup_database(settings.MIGRATION_DATABASE_URL or settings.DATABASE_URL,
                                check_only=args.check_only, allow_sqlite=args.allow_sqlite)
    except Exception as exc:
        # Driver/config errors may contain a full connection URI. Never echo them.
        print(f"Database setup failed ({type(exc).__name__}). No credentials displayed.")
        if isinstance(exc, ValueError):
            print("Check the connection type, existing schema and migration revision before retrying.")
        else:
            print("Check project status, hostname, password and network access; see docs/db-setup.md.")
        return 1
    print(f"Database verified: {result['tables']} application tables; revision {result['revision']}; "
          f"{result['catalog_items']} catalogue items.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
