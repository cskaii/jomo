"""Exercise the real-account gateway with provider responses isolated to tests."""
import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.api.v1.auth import router
from app.core.config import get_settings
from app.schemas.usage import UsageRecordCreate

@pytest.fixture
def auth_client(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "DEV_AUTH_ENABLED", False)
    monkeypatch.setattr(settings, "AUTH_PUBLIC_KEY", "test-key")
    monkeypatch.setattr(settings, "AUTH_ISSUER_URL", "https://project.supabase.co/auth/v1")
    original = httpx.AsyncClient
    def install(handler):
        monkeypatch.setattr("app.services.auth_service.httpx.AsyncClient", lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    with TestClient(app) as client:
        yield client, install

def test_login_forwards_credentials_and_validates_session(auth_client):
    client, install = auth_client
    def provider(request):
        assert request.url.params["grant_type"] == "password"
        assert request.headers["apikey"] == "test-key"
        assert b'"password":"test-password"' in request.content
        return httpx.Response(200, json={"access_token":"signed-token", "refresh_token":"refresh", "expires_in":3600})
    install(provider)
    response = client.post("/api/v1/auth/login", json={"email":"person@example.com", "password":"test-password"})
    assert response.status_code == 200
    assert response.json()["data"]["expires_in"] == 3600

def test_provider_rejection_does_not_leak_details(auth_client):
    client, install = auth_client
    install(lambda r: httpx.Response(400, json={"msg":"private provider detail"}))
    response = client.post("/api/v1/auth/login", json={"email":"person@example.com", "password":"bad"})
    assert response.status_code == 401
    assert "private provider detail" not in response.text

def test_signup_confirmation_and_recovery_privacy(auth_client):
    client, install = auth_client
    install(lambda r: httpx.Response(200, json={"id":"new-user"}))
    response = client.post("/api/v1/auth/register", json={"email":"person@example.com", "password":"test-password"})
    assert response.status_code == 200
    assert response.json()["data"]["session"] is None
    install(lambda r: httpx.Response(400, json={"msg":"email absent"}))
    assert client.post("/api/v1/auth/recover", json={"email":"person@example.com"}).status_code == 200

def test_refresh_and_invalid_provider_sessions(auth_client):
    client, install = auth_client
    def provider(request):
        assert request.url.params["grant_type"] == "refresh_token"
        return httpx.Response(200, json={"access_token":"new-token", "refresh_token":"rotated", "expires_in":3600})
    install(provider)
    assert client.post("/api/v1/auth/refresh", json={"refresh_token":"previous"}).json()["data"]["refresh_token"] == "rotated"
    install(lambda r: httpx.Response(200, json={}))
    assert client.post("/api/v1/auth/refresh", json={"refresh_token":"previous"}).status_code == 503

def test_legacy_session_and_unauthenticated_password_change(auth_client):
    client, _ = auth_client
    assert client.post("/api/v1/auth/dev-session").status_code == 404
    assert client.post("/api/v1/auth/password", json={"password":"new-password"}).status_code == 401

def test_demo_usage_cannot_be_imported():
    with pytest.raises(ValidationError):
        UsageRecordCreate(usage_date="2026-11-06", total_minutes=30, source="demo")
