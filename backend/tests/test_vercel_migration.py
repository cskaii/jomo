import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings


def test_cron_denies_unconfigured_and_wrong_credentials(monkeypatch):
    from pydantic import SecretStr
    settings = get_settings()
    with TestClient(app, client=("192.0.2.90", 50100)) as client:
        monkeypatch.setattr(settings, "CRON_SECRET", SecretStr(""))
        assert client.get("/api/v1/internal/retention").status_code == 401
        monkeypatch.setattr(settings, "CRON_SECRET", SecretStr("a" * 40))
        assert client.get("/api/v1/internal/retention", headers={"Authorization": "Bearer wrong"}).status_code == 401
        assert client.get("/api/v1/internal/retention?secret=" + "a" * 40).status_code == 401


def test_cron_authenticates_and_runs_bounded_cleanup(monkeypatch):
    from pydantic import SecretStr
    import app.api.v1.maintenance as job
    from unittest.mock import MagicMock
    settings = get_settings()
    monkeypatch.setattr(settings, "CRON_SECRET", SecretStr("a" * 40))
    session = MagicMock()
    session.__enter__.return_value.query.return_value.count.return_value = 2
    monkeypatch.setattr(job, "SessionLocal", lambda: session)
    calls = []
    monkeypatch.setattr(job, "cleanup", lambda db, **options: calls.append(options))
    with TestClient(app, client=("192.0.2.91", 50100)) as client:
        result = client.get("/api/v1/internal/retention", headers={"Authorization": "Bearer " + "a" * 40})
    assert result.status_code == 200
    assert result.json() == {"success": True, "pending_deletions": 2}
    assert calls == [{"time_budget_seconds": 150}]


def test_serverless_startup_does_not_start_worker_or_load_ai(monkeypatch):
    import app.main as main
    monkeypatch.setattr(main.settings, "SERVERLESS_MODE", True)
    monkeypatch.setattr(main.settings, "AI_PRESIDIO_ENABLED", True)
    monkeypatch.setattr(main.asyncio, "create_task", lambda *_: pytest.fail("A serverless instance must not launch an endless worker"))
    import app.ai.screening_service as screening
    monkeypatch.setattr(screening, "get_screening_provider", lambda: pytest.fail("AI must load only when screening is requested"))
    async def start():
        async with main.lifespan(app):
            pass
    import asyncio
    asyncio.run(start())
