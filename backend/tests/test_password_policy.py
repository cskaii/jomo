"""Policy checks never create accounts or contact the real Auth provider."""
import json
from pathlib import Path
import uuid
from unittest.mock import AsyncMock

from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest

from app.core.password_policy import validate_new_password
from app.main import app

VECTORS = json.loads((Path(__file__).parent / "password-policy-vectors.json").read_text(encoding="utf-8"))


@pytest.fixture
def client():
    # Isolate this module's auth attempts from other tests' per-IP rate counters.
    with TestClient(app, client=("192.0.2.15", 50000)) as test_client:
        yield test_client


@pytest.mark.parametrize("case", VECTORS, ids=lambda case: case["name"])
def test_password_policy(case):
    if case["accepted"]:
        validate_new_password(case["password"], case.get("email", ""))
    else:
        with pytest.raises(HTTPException) as caught:
            validate_new_password(case["password"], case.get("email", ""))
        assert caught.value.detail["code"] == "WEAK_PASSWORD"
        assert case["password"] not in str(caught.value.detail)


def test_invalid_unicode_is_rejected_safely():
    with pytest.raises(HTTPException):
        validate_new_password("violet orbit lantern\ud800")


def test_weak_signup_cannot_bypass_browser_meter(client, monkeypatch):
    provider = AsyncMock()
    monkeypatch.setattr("app.services.auth_service.AuthService.call", provider)
    response = client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "aaaaaaaaaaaaaaaaaaaa"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "WEAK_PASSWORD"
    provider.assert_not_called()


def test_short_complex_signup_is_rejected(client, monkeypatch):
    provider = AsyncMock()
    monkeypatch.setattr("app.services.auth_service.AuthService.call", provider)
    response = client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "N7!tB2@qR9#xM4"})
    assert response.status_code == 422
    assert "N7!tB2@qR9#xM4" not in response.text
    provider.assert_not_called()


def test_password_reset_enforces_same_policy(client, monkeypatch):
    provider = AsyncMock()
    monkeypatch.setattr("app.services.auth_service.AuthService.call", provider)
    response = client.post("/api/v1/auth/password", headers={"Authorization": f"Bearer {uuid.uuid4()}"},
                           json={"password": "aaaaaaaaaaaaaaaaaaaa"})
    assert response.status_code == 400
    provider.assert_not_called()


def test_accepted_password_is_forwarded_exactly_and_not_returned(client, monkeypatch):
    password = "  violet orbit lantern meadow  "
    provider = AsyncMock(return_value={"id": "new-user"})
    monkeypatch.setattr("app.services.auth_service.AuthService.call", provider)
    response = client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": password})
    assert response.status_code == 200
    assert provider.call_args.args[2]["password"] == password
    assert password not in response.text


def test_existing_short_password_still_reaches_sign_in_provider(client, monkeypatch):
    provider = AsyncMock(return_value={"access_token": "signed", "refresh_token": "refresh", "expires_in": 3600})
    monkeypatch.setattr("app.services.auth_service.AuthService.call", provider)
    response = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "old"})
    assert response.status_code == 200
    assert provider.call_args.args[2]["password"] == "old"
