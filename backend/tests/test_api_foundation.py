import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_unauthenticated_request_rejected(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert "request_id" in data


def test_authenticated_user_profile(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    res = response.json()
    assert "data" in res
    assert res["data"]["id"] == user_id
    assert "request_id" in res


def test_privacy_text_screening_pii(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}"}
    payload = {
        "text": "Hi, email me at test@example.com or reach S1234567A.",
        "checks": ["pii"],
    }
    response = client.post("/api/v1/ai/privacy/text", json=payload, headers=headers)
    assert response.status_code == 200
    res = response.json()
    assert res["data"]["has_potential_pii"] is True
    assert "[REDACTED]" in res["data"]["redacted_text"]
    assert "test@example.com" not in res["data"]["redacted_text"]


def test_shop_and_gardens_flow(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}"}

    # List accessible gardens
    response = client.get("/api/v1/gardens", headers=headers)
    assert response.status_code == 200
    gardens = response.json()["data"]
    assert len(gardens) >= 1
    personal_garden = gardens[0]
    assert personal_garden["garden_type"] == "personal"

    # List shop items
    response = client.get("/api/v1/shop/items", headers=headers)
    assert response.status_code == 200
    items = response.json()["data"]
    assert len(items) >= 4
