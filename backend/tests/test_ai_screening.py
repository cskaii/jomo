"""Tests for the Presidio-backed Privacy Guardian text screening.

Run with the project venv (Presidio + spaCy installed):
    /home/s4mgoh/.venv/bin/python -m pytest tests/test_ai_screening.py
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ai.screening_service import get_screening_provider
from app.core.config import get_settings

pytestmark = pytest.mark.skipif(
    not get_settings().AI_PRESIDIO_ENABLED,
    reason="Presidio integration is disabled in this test environment.",
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

SAMPLE = (
    "Reach me at alex@example.com or +65 9123 4567. "
    "My NRIC is S1234567A. Card 4111 1111 1111 1111."
)


def test_presidio_provider_detects_sg_pii():
    provider = get_screening_provider()
    assert provider is not None, "Presidio screening provider should initialise"

    result = provider.screen(SAMPLE, "en")
    entity_types = {d["entity_type"] for d in result["detections"]}

    assert "EMAIL_ADDRESS" in entity_types
    assert "SG_NRIC_FIN" in entity_types
    assert "SG_PHONE_NUMBER" in entity_types
    assert "CREDIT_CARD" in entity_types
    assert result["has_potential_pii"] is True

    redacted = result["redacted_text"]
    assert "[REDACTED]" in redacted
    assert "alex@example.com" not in redacted
    assert "S1234567A" not in redacted
    assert "+65 9123 4567" not in redacted
    assert "4111 1111 1111 1111" not in redacted


def test_presidio_provider_clean_text():
    provider = get_screening_provider()
    assert provider is not None

    result = provider.screen("Just a friendly message with no personal data.", "en")
    assert result["has_potential_pii"] is False
    assert result["detections"] == []
    # Limitations must always be present: no green "safe" status (blueprint §4.4 F).
    assert result["limitations"], "limitations must always be returned"


def test_privacy_text_endpoint_presidio(client):
    user_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {user_id}"}
    payload = {"text": "Contact jane@example.com, NRIC T7654321B.", "checks": ["pii"], "consent": True}

    response = client.post("/api/v1/ai/privacy/text", json=payload, headers=headers)
    assert response.status_code == 200

    res = response.json()
    assert res["data"]["has_potential_pii"] is True
    assert "[REDACTED]" in res["data"]["redacted_text"]
    assert "jane@example.com" not in res["data"]["redacted_text"]
    assert "T7654321B" not in res["data"]["redacted_text"]

    entity_types = {d["entity_type"] for d in res["data"]["detections"]}
    assert "EMAIL_ADDRESS" in entity_types
    assert "SG_NRIC_FIN" in entity_types
    assert res["data"]["engine"] == "presidio"


# --- Extended coverage -----------------------------------------------------

def test_credit_card_detected():
    provider = get_screening_provider()
    assert provider is not None
    result = provider.screen("Card 4111 1111 1111 1111 on file.", "en")
    assert "CREDIT_CARD" in {d["entity_type"] for d in result["detections"]}
    assert "4111 1111 1111 1111" not in result["redacted_text"]


def test_sg_phone_without_country_code():
    provider = get_screening_provider()
    assert provider is not None
    result = provider.screen("Call 9123 4567 anytime.", "en")
    assert "SG_PHONE_NUMBER" in {d["entity_type"] for d in result["detections"]}
    assert "9123 4567" not in result["redacted_text"]


def test_url_inside_email_is_deduped():
    provider = get_screening_provider()
    assert provider is not None
    result = provider.screen("Contact alex@example.com please.", "en")
    types = [d["entity_type"] for d in result["detections"]]
    assert types.count("EMAIL_ADDRESS") == 1
    assert "URL" not in types  # overlaps the email -> deduped away


def test_multiple_emails_all_redacted():
    provider = get_screening_provider()
    assert provider is not None
    result = provider.screen("a@x.com and b@y.com and c@z.com", "en")
    assert result["has_potential_pii"] is True
    assert "a@x.com" not in result["redacted_text"]
    assert "b@y.com" not in result["redacted_text"]
    assert "c@z.com" not in result["redacted_text"]


def test_redaction_preserves_surrounding_text():
    provider = get_screening_provider()
    assert provider is not None
    result = provider.screen("Hello there, my email is test@example.com and goodbye.", "en")
    assert result["redacted_text"].startswith("Hello there, my email is ")
    assert result["redacted_text"].endswith(" and goodbye.")


def test_empty_text_is_safe():
    provider = get_screening_provider()
    assert provider is not None
    result = provider.screen("", "en")
    assert result["has_potential_pii"] is False
    assert result["detections"] == []
    assert result["redacted_text"] == ""


def test_ner_detects_person_and_location_when_model_available():
    provider = get_screening_provider()
    if provider is None or not getattr(provider, "ner_enabled", False):
        pytest.skip("spaCy NER model not installed (optional)")
    result = provider.screen("I will meet Wei Ming at Marina Bay.", "en")
    types = {d["entity_type"] for d in result["detections"]}
    assert "PERSON" in types
    assert "LOCATION" in types


def test_endpoint_enforces_max_text_length(client):
    headers = {"Authorization": f"Bearer {uuid.uuid4()}"}
    response = client.post(
        "/api/v1/ai/privacy/text",
        json={"text": "a" * 10001, "checks": ["pii"], "consent": True},
        headers=headers,
    )
    assert response.status_code == 422


def test_endpoint_rejects_missing_auth(client):
    response = client.post(
        "/api/v1/ai/privacy/text",
        json={"text": "test@example.com", "checks": ["pii"], "consent": True},
    )
    assert response.status_code == 401


def test_disabled_presidio_never_substitutes_another_detector(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "AI_PRESIDIO_ENABLED", False)
    response = client.post("/api/v1/ai/privacy/text", json={"text": "test@example.com", "checks": ["pii"], "consent": True},
                           headers={"Authorization": f"Bearer {uuid.uuid4()}"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SCREENING_UNAVAILABLE"
    assert "redacted_text" not in response.text


def test_presidio_failure_reports_unavailability_without_logging_input(client, monkeypatch, caplog):
    class BrokenProvider:
        def screen(self, text, language):
            raise RuntimeError("private-input@example.com")

    monkeypatch.setattr("app.services.privacy_service.get_screening_provider", lambda: BrokenProvider())
    response = client.post("/api/v1/ai/privacy/text", json={"text": "private-input@example.com", "checks": ["pii"], "consent": True},
                           headers={"Authorization": f"Bearer {uuid.uuid4()}"})
    assert response.status_code == 503
    assert "private-input@example.com" not in response.text
    assert "private-input@example.com" not in caplog.text


def test_presidio_email_validation_does_not_use_network(monkeypatch):
    import requests

    def unexpected_network(*args, **kwargs):
        raise AssertionError("Text screening must not make outbound requests")

    monkeypatch.setattr(requests.sessions.Session, "request", unexpected_network)
    result = get_screening_provider().screen("Please email privacy@example.com", "en")
    assert "EMAIL_ADDRESS" in {d["entity_type"] for d in result["detections"]}
    assert "privacy@example.com" not in result["redacted_text"]


def test_unsupported_screening_language_is_rejected(client):
    response = client.post("/api/v1/ai/privacy/text", json={"text": "test", "checks": ["pii"], "consent": True, "language": "xx"},
                           headers={"Authorization": f"Bearer {uuid.uuid4()}"})
    assert response.status_code == 422
