import uuid
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.middleware import (
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    register_exception_handlers,
    setup_prototype_middleware,
)


def create_test_app():
    """Builds a test application with all prototype middlewares attached."""
    test_app = FastAPI()
    setup_prototype_middleware(test_app, max_requests_per_minute=5)

    class ItemPayload(BaseModel):
        name: str = Field(..., min_length=3)
        count: int = Field(..., gt=0)

    @test_app.get("/health")
    def health():
        return {"status": "ok"}

    @test_app.get("/api/v1/ping")
    def api_ping():
        return {"message": "pong"}

    @test_app.post("/api/v1/items")
    def create_item(payload: ItemPayload):
        return {"item": payload.name, "count": payload.count}

    @test_app.get("/api/v1/trigger-error")
    def trigger_error():
        raise HTTPException(
            status_code=403,
            detail={"code": "PERMISSION_DENIED", "message": "Access is forbidden", "details": None},
        )

    @test_app.get("/api/v1/trigger-crash")
    def trigger_crash():
        raise RuntimeError("Unexpected critical failure")

    return test_app


@pytest.fixture
def test_client():
    app = create_test_app()
    with TestClient(app) as c:
        yield c


def test_request_id_generated_when_missing(test_client):
    """RequestIdMiddleware should generate a UUID4 when client does not supply X-Request-Id."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert "X-Request-Id" in response.headers
    req_id = response.headers["X-Request-Id"]
    # Check that it's a valid UUID
    uuid_obj = uuid.UUID(req_id)
    assert str(uuid_obj) == req_id


def test_request_id_preserved_when_provided(test_client):
    """RequestIdMiddleware should preserve client-supplied X-Request-Id."""
    custom_id = str(uuid.uuid4())
    response = test_client.get("/health", headers={"X-Request-Id": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-Id") == custom_id


def test_security_headers_present(test_client):
    """SecurityHeadersMiddleware must add all prescribed OWASP headers."""
    response = test_client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("Permissions-Policy") == "camera=(), microphone=(), geolocation=()"


def test_rate_limiting_triggers_429(test_client):
    """RateLimitMiddleware should allow up to max_requests_per_minute, then return 429."""
    # max_requests_per_minute is configured to 5 in test_app
    for i in range(5):
        res = test_client.get("/api/v1/ping")
        assert res.status_code == 200

    # 6th request must be rate limited
    blocked_res = test_client.get("/api/v1/ping")
    assert blocked_res.status_code == 429
    assert blocked_res.headers.get("Retry-After") == "60"
    data = blocked_res.json()
    assert "error" in data
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "request_id" in data


def test_rate_limit_exempts_non_api_paths(test_client):
    """Non-api paths like /health must not be blocked by RateLimitMiddleware."""
    for _ in range(10):
        res = test_client.get("/health")
        assert res.status_code == 200


def test_validation_error_envelope(test_client):
    """register_exception_handlers must format 422 errors into standard JOMO envelope."""
    response = test_client.post("/api/v1/items", json={"name": "a", "count": -1})
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in data
    assert data["error"]["details"] is not None


def test_http_exception_envelope(test_client):
    """register_exception_handlers must format HTTPExceptions with custom dict details."""
    response = test_client.get("/api/v1/trigger-error")
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "PERMISSION_DENIED"
    assert data["error"]["message"] == "Access is forbidden"
    assert "request_id" in data


def test_generic_500_exception_envelope():
    """register_exception_handlers must catch unhandled exceptions, hiding internal traces."""
    app = create_test_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/trigger-crash")
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "Unexpected critical failure" not in data["error"]["message"]
        assert "request_id" in data


def test_setup_prototype_middleware_helper():
    """Tests the convenience setup_prototype_middleware function."""
    demo_app = FastAPI()
    setup_prototype_middleware(demo_app, max_requests_per_minute=20)

    with TestClient(demo_app) as client:
        # 404 handler test
        res = client.get("/non-existent")
        assert res.status_code == 404
        data = res.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "request_id" in data
        assert "X-Request-Id" in res.headers
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
