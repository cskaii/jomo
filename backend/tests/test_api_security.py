"""Boundary and integration regressions for blueprint sections 5, 16 and 17."""

import asyncio
import json
import logging
import uuid

import httpx
import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.dependencies import CurrentUser
from app.core.config import Settings, get_settings
from app.middleware import setup_middleware
from app.middleware.body_limit import BodyLimitMiddleware
from app.middleware.rate_limit import SlidingWindowLimiter


ORIGIN = "http://localhost:3000"


def demo_headers(actor=None):
    return {"Authorization": f"Bearer dev-user-{actor or uuid.uuid4()}"}


@pytest.fixture
def boundary():
    app = FastAPI()
    setup_middleware(app, max_requests_per_minute=600, max_body_bytes=256)

    @app.get("/api/v1/private")
    def private(actor: CurrentUser):
        return {"id": str(actor.id)}

    @app.post("/api/v1/echo")
    async def echo(request: Request):
        return {"bytes": len(await request.body())}

    @app.post("/group-invites/{token}/accept")
    def failure(token: str):
        raise RuntimeError("secret raw screened text and SQL parameters")

    @app.get("/api/v1/internal-http-error")
    def internal_http_error():
        raise HTTPException(500, detail="secret SQL")

    @app.post("/api/v1/ai/privacy/text")
    @app.post("/api/v1/groups/{group_id}/invites")
    @app.post("/api/v1/activities")
    @app.post("/api/v1/activities/{activity_id}/proofs/upload-url")
    def limited(actor: CurrentUser):
        return {"ok": True}

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def assert_response_headers(response):
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"
    uuid.UUID(response.headers["x-request-id"])
    assert response.headers["access-control-allow-origin"] == ORIGIN
    if response.status_code >= 400:
        assert response.json()["request_id"] == response.headers["x-request-id"]


def test_preflight_and_early_errors_keep_headers(boundary):
    preflight = boundary.options("/api/v1/private", headers={
        "Origin": ORIGIN, "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization,X-Request-Id",
    })
    assert preflight.status_code == 200
    assert_response_headers(preflight)
    for path, expected in [("/api/v1/private", 401), ("/unknown", 404),
                           ("/api/v1/internal-http-error", 500)]:
        response = boundary.get(path, headers={"Origin": ORIGIN})
        assert response.status_code == expected
        assert_response_headers(response)
        assert "secret SQL" not in response.text


def test_disallowed_origin_not_authorized_by_cors(boundary):
    response = boundary.options("/api/v1/private", headers={
        "Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET",
    })
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
    assert response.json()["error"]["code"] == "CORS_REJECTED"
    assert response.json()["request_id"] == response.headers["x-request-id"]


@pytest.mark.parametrize("supplied", ["not-a-uuid", "x" * 1000])
def test_untrusted_request_id_is_replaced(boundary, supplied):
    response = boundary.get("/unknown", headers={"X-Request-Id": supplied})
    generated = response.headers["x-request-id"]
    assert generated != supplied
    uuid.UUID(generated)


def test_audit_records_metadata_without_private_values(boundary, caplog):
    with caplog.at_level(logging.INFO, logger="jomo"):
        response = boundary.post("/group-invites/private-invite-token/accept?token=secret-query",
                                 headers={"Origin": ORIGIN, "Authorization": "Bearer private-token"},
                                 content="private-body")
    assert response.status_code == 500
    assert_response_headers(response)
    assert not any(secret in caplog.text for secret in (
        "private-invite-token", "secret-query", "private-token", "private-body", "SQL parameters",
    ))
    events = [json.loads(r.message) for r in caplog.records if r.message.startswith('{"event"')]
    assert events[-1]["endpoint"] == "/group-invites/{token}/accept"
    assert events[-1]["error_code"] == "INTERNAL_SERVER_ERROR"
    assert events[-1]["duration_ms"] >= 0


def test_body_limits_and_encoding(boundary):
    response = boundary.post("/api/v1/echo", content=b"a" * 257, headers={"Origin": ORIGIN})
    assert response.status_code == 413
    assert_response_headers(response)
    assert boundary.post("/api/v1/echo", content=b"a" * 256).json() == {"bytes": 256}
    assert boundary.post("/api/v1/echo", content=b"x", headers={"Content-Encoding": "gzip"}).status_code == 415
    assert boundary.post("/api/v1/echo", content=b"x", headers={"Content-Length": "invalid"}).status_code == 400


@pytest.mark.parametrize("headers", [[], [(b"content-length", b"1")]])
def test_chunked_and_underdeclared_bodies_never_reach_route(headers):
    called = []
    sent = []

    async def downstream(scope, receive, send):
        called.append(True)

    async def run():
        messages = iter([
            {"type": "http.request", "body": b"123", "more_body": True},
            {"type": "http.request", "body": b"456", "more_body": False},
        ])

        async def receive():
            return next(messages)

        async def send(message):
            sent.append(message)

        await BodyLimitMiddleware(downstream, max_body_bytes=5)(
            {"type": "http", "headers": headers, "state": {}}, receive, send)

    asyncio.run(run())
    assert not called
    assert sent[0]["status"] == 413


@pytest.mark.parametrize("path,limit", [
    ("/api/v1/ai/privacy/text", 20),
    ("/api/v1/groups/example/invites", 10),
    ("/api/v1/activities", 20),
    ("/api/v1/activities/example/proofs/upload-url", 10),
])
def test_endpoint_limits_use_verified_user(boundary, path, limit):
    headers = {**demo_headers(), "Origin": ORIGIN}
    for _ in range(limit):
        assert boundary.post(path, headers=headers).status_code == 200
    response = boundary.post(path, headers=headers)
    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0
    assert_response_headers(response)
    # Same IP, different verified user: independent allowance.
    assert boundary.post(path, headers=demo_headers()).status_code == 200
    headers["X-Forwarded-For"] = "203.0.113.1"
    assert boundary.post(path, headers=headers).status_code == 429


def test_window_expiry_and_bounded_identity_storage():
    now = [0.0]
    limiter = SlidingWindowLimiter(clock=lambda: now[0], max_keys=1)
    assert limiter.check("a", 1, 60) is None
    assert limiter.check("a", 1, 60) == 60
    with pytest.raises(HTTPException) as exc:
        limiter.check("b", 1, 60)
    assert exc.value.status_code == 503
    now[0] = 61
    assert limiter.check("b", 1, 60) is None
    assert "a" not in limiter.buckets


@pytest.fixture
def provider(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "DEV_AUTH_ENABLED", False)
    monkeypatch.setattr(settings, "AUTH_ISSUER_URL", "https://project.supabase.co/auth/v1")
    monkeypatch.setattr(settings, "AUTH_PUBLIC_KEY", "test-publishable-key")
    original = httpx.AsyncClient

    def install(handler):
        monkeypatch.setattr("app.core.auth.httpx.AsyncClient", lambda **kw: original(
            transport=httpx.MockTransport(handler), **kw))

    return install


def test_provider_identity_and_actor_audit(boundary, provider, caplog):
    actor = str(uuid.uuid4())

    def respond(request):
        assert str(request.url) == "https://project.supabase.co/auth/v1/user"
        assert request.headers["authorization"] == "Bearer signed.access.token"
        assert request.headers["apikey"] == "test-publishable-key"
        return httpx.Response(200, json={"id": actor, "aud": "authenticated", "role": "authenticated"})

    provider(respond)
    with caplog.at_level(logging.INFO, logger="jomo"):
        response = boundary.get("/api/v1/private", headers={"Authorization": "Bearer signed.access.token"})
    assert response.json() == {"id": actor}
    assert actor in caplog.text
    assert "signed.access.token" not in caplog.text


@pytest.mark.parametrize("status", [401, 403, 429, 500])
def test_provider_rejections_and_outages_fail_closed(boundary, provider, status):
    provider(lambda request: httpx.Response(status, json={"message": "private provider detail"}))
    response = boundary.get("/api/v1/private", headers={"Authorization": "Bearer forged.or.expired"})
    assert response.status_code == (401 if status in (401, 403) else 503)
    assert "private provider detail" not in response.text


def test_provider_timeout_fails_closed(boundary, provider):
    def timeout(request):
        raise httpx.ReadTimeout("private request details")
    provider(timeout)
    response = boundary.get("/api/v1/private", headers={"Authorization": "Bearer signed.access.token"})
    assert response.status_code == 503
    assert "private request" not in response.text


@pytest.mark.parametrize("payload", [
    {"id": "bad", "aud": "authenticated", "role": "authenticated"},
    {"id": str(uuid.uuid4()), "aud": "wrong-project", "role": "authenticated"},
    {"id": str(uuid.uuid4()), "aud": "authenticated", "role": "service_role"},
])
def test_invalid_provider_identity_is_never_accepted(boundary, provider, payload):
    provider(lambda request: httpx.Response(200, json=payload))
    assert boundary.get("/api/v1/private", headers={"Authorization": "Bearer signed.access.token"}).status_code in (401, 503)


@pytest.mark.parametrize("header", ["Bearer plain", "Bearer dev-user-" + str(uuid.uuid4()),
                                    "Bearer " + str(uuid.uuid4()), "Basic abc"])
def test_demo_and_uuid_tokens_rejected_when_disabled(boundary, provider, header):
    response = boundary.get("/api/v1/private", headers={"Authorization": header, "X-Dev-User-Id": str(uuid.uuid4())})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_production_configuration_rejects_demo_and_wildcard_cors():
    common = dict(_env_file=None, FRONTEND_URL="https://app.example", APP_ENV="production", AUTH_ISSUER_URL="https://project.supabase.co/auth/v1", AUTH_PUBLIC_KEY="public-key")
    with pytest.raises(ValidationError):
        Settings(**common, DEV_AUTH_ENABLED=True)
    with pytest.raises(ValidationError):
        Settings(**common, DEV_AUTH_ENABLED=False, CORS_ORIGINS="*")
    assert not Settings(**common, DEV_AUTH_ENABLED=False).dev_auth_allowed


def test_demo_endpoint_disabled_without_opt_in(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "DEV_AUTH_ENABLED", False)
    assert client.post("/api/v1/auth/dev-session").status_code == 404


def test_openapi_documents_bearer_and_standard_errors(client):
    schema = client.get("/api/openapi.json").json()
    operation = schema["paths"]["/api/v1/users/me"]["get"]
    assert operation["security"] == [{"HTTPBearer": []}]
    assert {"401", "403", "413", "422", "429", "503"} <= operation["responses"].keys()


def onboard(client):
    headers = demo_headers()
    assert client.get("/api/v1/users/me", headers=headers).status_code == 200
    return headers


def create_activity(client, headers, **changes):
    payload = {"title": "Offline reading", "category": "reading", "duration_minutes": 15,
               "proof_requirement": "photo"}
    payload.update(changes)
    response = client.post("/api/v1/activities", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


def test_activity_focus_permissions_and_state_transitions(client):
    owner, outsider = onboard(client), onboard(client)
    activity = create_activity(client, owner)
    for suffix in ("", "/participants"):
        assert client.get(f"/api/v1/activities/{activity}{suffix}", headers=outsider).status_code == 403
    assert client.post(f"/api/v1/activities/{activity}/complete", headers=owner).status_code == 409
    assert client.post(f"/api/v1/activities/{activity}/start", headers=owner, json={}).status_code == 200
    assert client.post(f"/api/v1/activities/{activity}/start", headers=owner, json={}).status_code == 409
    focus = client.post(f"/api/v1/activities/{activity}/focus-sessions", headers=owner)
    assert focus.status_code == 201
    session = focus.json()["data"]["id"]
    assert client.get(f"/api/v1/focus-sessions/{session}", headers=outsider).status_code == 403
    assert client.post(f"/api/v1/focus-sessions/{session}/end", headers=outsider).status_code == 403
    assert client.post(f"/api/v1/focus-sessions/{session}/end", headers=owner).status_code == 200
    assert client.post(f"/api/v1/activities/{activity}/end", headers=outsider).status_code == 403
    assert client.post(f"/api/v1/activities/{activity}/end", headers=owner).status_code == 200
    assert client.post(f"/api/v1/activities/{activity}/complete", headers=owner).status_code == 200
    participants = client.get(f"/api/v1/activities/{activity}/participants", headers=owner).json()["data"]
    assert participants[0]["status"] == "awaiting_proof"


@pytest.mark.parametrize("changes", [
    {"mime_type": "application/javascript"}, {"file_name": "../photo.jpg"},
    {"file_size_bytes": 10 * 1024 * 1024 + 1},
])
def test_upload_metadata_validation(client, changes):
    payload = {"file_name": "photo.jpg", "mime_type": "image/jpeg", "file_size_bytes": 100}
    payload.update(changes)
    response = client.post(f"/api/v1/activities/{uuid.uuid4()}/proofs/upload-url", headers=demo_headers(), json=payload)
    assert response.status_code == 422


def test_mock_uploads_and_fabricated_photo_proof_are_not_accepted(client):
    owner = onboard(client)
    activity = create_activity(client, owner)
    response = client.post(f"/api/v1/activities/{activity}/proofs/upload-url", headers=owner,
                           json={"file_name": "photo.jpg", "mime_type": "image/jpeg", "file_size_bytes": 100})
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "STORAGE_NOT_CONFIGURED"
    client.post(f"/api/v1/activities/{activity}/start", headers=owner, json={})
    client.post(f"/api/v1/activities/{activity}/end", headers=owner)
    response = client.post(f"/api/v1/activities/{activity}/proofs", headers=owner,
                           json={"proof_type": "photo", "storage_key": "fabricated-photo"})
    assert response.status_code == 501


def test_group_proof_requires_current_membership_and_participation(client):
    owner, peer, nonparticipant, outsider = [onboard(client) for _ in range(4)]
    group = client.post("/api/v1/groups", headers=owner, json={"name": "Reading circle"}).json()["data"]["id"]
    invite = client.post(f"/api/v1/groups/{group}/invites", headers=owner, json={}).json()["data"]["invite_token"]
    for headers in (peer, nonparticipant):
        assert client.post(f"/api/v1/group-invites/{invite}/accept", headers=headers).status_code == 200
    activity = create_activity(client, owner, visibility="group", group_id=group,
                               proof_requirement="group_confirmation")
    assert client.post(f"/api/v1/activities/{activity}/start", headers=owner, json={}).status_code == 200
    assert client.post(f"/api/v1/activities/{activity}/join", headers=peer).status_code == 200
    assert client.post(f"/api/v1/activities/{activity}/end", headers=owner).status_code == 200
    response = client.post(f"/api/v1/activities/{activity}/proofs", headers=owner,
                           json={"proof_type": "group_confirmation"})
    assert response.status_code == 201, response.text
    proof = response.json()["data"]["id"]
    assert client.delete(f"/api/v1/proofs/{proof}", headers=outsider).status_code == 403
    for headers in (outsider, nonparticipant):
        assert client.post(f"/api/v1/proofs/{proof}/confirm", headers=headers,
                           json={"decision": "confirm"}).status_code == 403
    assert client.post(f"/api/v1/proofs/{proof}/confirm", headers=owner,
                       json={"decision": "confirm"}).status_code == 400
    assert client.post(f"/api/v1/proofs/{proof}/confirm", headers=peer,
                       json={"decision": "confirm"}).status_code == 200
    assert client.post(f"/api/v1/proofs/{proof}/confirm", headers=peer,
                       json={"decision": "reject"}).status_code == 409
    assert client.post(f"/api/v1/groups/{group}/leave", headers=peer).status_code == 200
    assert client.get(f"/api/v1/activities/{activity}", headers=peer).status_code == 403


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "status=made-up"])
def test_activity_query_validation(client, query):
    response = client.get("/api/v1/activities?" + query, headers=demo_headers())
    assert response.status_code == 422


def test_former_group_creator_cannot_browse_private_group_activities(client):
    owner = onboard(client)
    group = client.post("/api/v1/groups", headers=owner, json={"name": "Solo group"}).json()["data"]["id"]
    activity = create_activity(client, owner, visibility="group", group_id=group)
    assert client.post(f"/api/v1/groups/{group}/leave", headers=owner).status_code == 200
    assert client.get(f"/api/v1/activities/{activity}", headers=owner).status_code == 403
    assert client.get("/api/v1/activities", headers=owner).json()["data"] == []


def test_screening_configured_limit_and_allowed_checks(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "SCREENING_MAX_TEXT_LENGTH", 5)
    for payload in ({"text": "123456"}, {"text": "ok", "checks": ["unknown"]}, {"text": ""}):
        response = client.post("/api/v1/ai/privacy/text", headers=demo_headers(), json=payload)
        assert response.status_code == 422
