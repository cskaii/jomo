"""Tests always use a disposable database, never a developer or deployed database."""
import os
import tempfile

_test_database = tempfile.TemporaryDirectory(prefix="jomo-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + _test_database.name.replace("\\", "/") + "/test.db"
os.environ["APP_ENV"] = "test"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["AUTO_SEED_CATALOG"] = "true"  # Fixtures only; deployment defaults to empty.
os.environ["AI_PRESIDIO_ENABLED"] = "true"

# Clear the lru_cache on Settings so the test env vars above are picked up
# even if get_settings() was already imported elsewhere before conftest runs.
from app.core.config import get_settings
get_settings.cache_clear()


import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine
import app.models as _models  # register metadata without shadowing the FastAPI app


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database tables exist for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    _test_database.cleanup()


@pytest.fixture
def client():
    """Yield a TestClient running within FastAPI lifespan."""
    with TestClient(app) as test_client:
        yield test_client
