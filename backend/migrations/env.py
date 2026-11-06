import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

# Ensure app and shared are in python path
backend_root = Path(__file__).resolve().parents[1]
repo_root = backend_root.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.core.config import get_settings
from app.db.base import Base
import app.models  # load all models for metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
# Pass the URI directly to SQLAlchemy, avoiding ConfigParser interpolation of
# percent-encoded passwords. An explicit connection supports setup/test runners.
database_url = config.attributes.get("database_url") or settings.MIGRATION_DATABASE_URL or settings.DATABASE_URL

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    supplied_connection = config.attributes.get("connection")
    if supplied_connection is not None:
        with_migration_connection(supplied_connection)
        return

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    try:
        with connectable.connect() as connection:
            with_migration_connection(connection)
    finally:
        connectable.dispose()


def with_migration_connection(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
