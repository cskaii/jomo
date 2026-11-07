"""Exercise real migrations on disposable databases, never backend/.env."""
from io import StringIO

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.db.setup import migration_config, setup_database


def local_url(tmp_path):
    return "sqlite:///" + str(tmp_path / "migration.db").replace("\\", "/")


def test_setup_migrates_and_is_repeatable(tmp_path):
    url = local_url(tmp_path)
    first = setup_database(url, allow_sqlite=True)
    second = setup_database(url, allow_sqlite=True)
    assert first == second
    assert first["tables"] == 32
    assert first["revision"] == "d91e7c20b403"
    assert first["catalog_items"] == 0
    assert setup_database(url, allow_sqlite=True, check_only=True)["catalog_items"] == 0


def test_setup_preserves_empty_application_tables(tmp_path):
    url = local_url(tmp_path)
    setup_database(url, allow_sqlite=True)
    engine = create_engine(url)
    try:
        assert setup_database(url, allow_sqlite=True)["catalog_items"] == 0
        with engine.connect() as connection:
            for table in inspect(connection).get_table_names():
                if table != "alembic_version":
                    assert connection.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one() == 0
    finally:
        engine.dispose()


def test_check_only_does_not_create_tables(tmp_path):
    url = local_url(tmp_path)
    with pytest.raises(ValueError, match="migration head"):
        setup_database(url, allow_sqlite=True, check_only=True)
    engine = create_engine(url)
    try:
        assert inspect(engine).get_table_names() == []
    finally:
        engine.dispose()


def test_setup_refuses_unversioned_application_tables(tmp_path):
    url = local_url(tmp_path)
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE users (id TEXT PRIMARY KEY)"))
        with pytest.raises(ValueError, match="Unversioned"):
            setup_database(url, allow_sqlite=True)
        assert inspect(engine).get_table_names() == ["users"]
    finally:
        engine.dispose()


def test_connection_guards_do_not_silently_use_sqlite_or_transaction_pooler(tmp_path):
    with pytest.raises(ValueError, match="PostgreSQL"):
        setup_database(local_url(tmp_path))
    with pytest.raises(ValueError, match="5432"):
        setup_database("postgresql+psycopg://example:example@localhost:6543/postgres")


def test_postgresql_sql_generation_accepts_encoded_passwords():
    output = StringIO()
    config = migration_config()
    config.output_buffer = output
    config.attributes["database_url"] = "postgresql+psycopg://test:pass%40word%25@localhost/postgres"
    command.upgrade(config, "head", sql=True)
    sql = output.getvalue()
    assert sql.count("CREATE TABLE ") == 33  # 32 app tables plus alembic_version
    assert "TIMESTAMP WITH TIME ZONE" in sql
    assert "UUID" in sql
    assert "pass" not in sql
    assert sql.count("ENABLE ROW LEVEL SECURITY") == 33


def test_migrated_database_enforces_garden_balance_constraint(tmp_path):
    url = local_url(tmp_path)
    setup_database(url, allow_sqlite=True)
    engine = create_engine(url)
    try:
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text("INSERT INTO gardens "
                    "(id,garden_type,owner_user_id,name,points_balance,growth_level,created_at,updated_at) "
                    "VALUES ('123','personal','456','Test',-1,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"))
    finally:
        engine.dispose()
