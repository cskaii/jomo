"""Real Presidio SDK tests; image tests supply deterministic OCR word boxes."""
import base64
import csv
import io
import json
import shutil
import uuid

import pytest
from PIL import Image, PngImagePlugin
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.screening import ScreeningEvent


def headers(media="application/json", user=None):
    return {"Authorization": f"Bearer {user or uuid.uuid4()}", "Content-Type": media, "X-Screening-Consent": "true"}


def test_json_redacts_nested_values_preserving_shape_and_types(client):
    actor = uuid.uuid4()
    data = {"email": "alice@example.com", "a.b": {"items": ["bob@example.com", 42, True, None]}, "count": 2}
    response = client.post("/api/v1/ai/privacy/structured?format=json", content=json.dumps(data), headers=headers(user=actor))
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["engine"] == "presidio-structured"
    redacted = json.loads(result["content"])
    assert redacted == {"email": "[REDACTED]", "a.b": {"items": ["[REDACTED]", 42, True, None]}, "count": 2}
    assert "alice@example.com" not in response.text
    assert result["flagged_fields"] == 2
    with SessionLocal() as db:
        events = db.scalars(select(ScreeningEvent).where(ScreeningEvent.user_id == actor)).all()
        assert len(events) == 1 and events[0].screening_type == "structured"
        assert "EMAIL_ADDRESS" in events[0].detected_categories
        assert "alice@example.com" not in str(events[0].detected_categories)


def test_csv_scans_all_rows_and_escapes_formulas(client):
    source = "contact,note\nnone,=1+1\nalice@example.com,ordinary\n"
    response = client.post("/api/v1/ai/privacy/structured?format=csv", content=source, headers=headers("text/csv"))
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    rows = list(csv.reader(io.StringIO(result["content"])))
    assert rows[0] == ["contact", "note"]
    assert rows[1] == ["[REDACTED]", "'=1+1"]
    assert rows[2] == ["[REDACTED]", "ordinary"]
    assert result["flagged_fields"] == 1


@pytest.mark.parametrize("source", [
    '{"email": "a@x.com", "email": "b@y.com"}',
    '{"value": NaN}',
    '{"value": Infinity}',
    '"not an object"',
    '{invalid}',
    '[' * 20 + '"x"' + ']' * 20,
])
def test_invalid_or_ambiguous_json_is_rejected(client, source):
    response = client.post("/api/v1/ai/privacy/structured?format=json", content=source, headers=headers())
    assert response.status_code == 422


@pytest.mark.parametrize("source", ["", "header\n", "a,a\nx,y\n", "a,b\nx\n", "a,\nx,y\n"])
def test_invalid_csv_is_rejected(client, source):
    response = client.post("/api/v1/ai/privacy/structured?format=csv", content=source, headers=headers("text/csv"))
    assert response.status_code == 422


def test_file_routes_require_authentication_and_explicit_consent(client):
    route = "/api/v1/ai/privacy/structured?format=json"
    assert client.post(route, content="{}", headers={"Content-Type": "application/json"}).status_code == 401
    h = headers()
    h.pop("X-Screening-Consent")
    assert client.post(route, content="{}", headers=h).status_code == 400
    assert client.post("/api/v1/ai/privacy/image", content=b"x", headers={"Content-Type": "image/png"}).status_code == 401


def test_file_size_media_and_encoding_limits(client):
    assert client.post("/api/v1/ai/privacy/image", content=b"x", headers=headers("image/svg+xml")).status_code == 415
    assert client.post("/api/v1/ai/privacy/image", content=b"x" * (2 * 1024 * 1024 + 1), headers=headers("image/png")).status_code == 413
    assert client.post("/api/v1/ai/privacy/structured?format=json", content=b"x" * 262145, headers=headers()).status_code == 422
    assert client.post("/api/v1/ai/privacy/structured?format=json", content=b"\xff", headers=headers()).status_code == 422
    assert client.post("/api/v1/ai/privacy/structured?format=json", content="{}", headers=headers("text/csv")).status_code == 415


def image_bytes(size=(240, 80)):
    output = io.BytesIO()
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("private", "source-metadata@example.com")
    Image.new("RGB", size, "white").save(output, format="PNG", pnginfo=metadata)
    return output.getvalue()


def test_real_image_redactor_masks_ocr_boxes_and_strips_metadata(client, monkeypatch):
    from presidio_image_redactor import ImageAnalyzerEngine, ImageRedactorEngine, OCR

    class FixedOCR(OCR):
        def perform_ocr(self, image, **kwargs):
            assert kwargs["timeout"] == 20 and kwargs["lang"] == "eng"
            return {"text": ["alice@example.com"], "conf": [95], "left": [10], "top": [10], "width": [180], "height": [20]}

    monkeypatch.setattr("app.services.file_screening_service.image_engine", lambda provider:
        ImageRedactorEngine(image_analyzer_engine=ImageAnalyzerEngine(analyzer_engine=provider._analyzer, ocr=FixedOCR())))
    response = client.post("/api/v1/ai/privacy/image", content=image_bytes(), headers=headers("image/png"))
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["engine"] == "presidio-image-redactor"
    assert result["flagged_fields"] >= 1
    assert "EMAIL_ADDRESS" in result["detected_categories"]
    output = base64.b64decode(result["content_base64"])
    assert b"source-metadata@example.com" not in output
    with Image.open(io.BytesIO(output)) as redacted:
        assert redacted.getpixel((20, 15)) == (0, 0, 0)
        assert redacted.getpixel((220, 70)) == (255, 255, 255)
        assert not redacted.info


def test_invalid_image_and_pixel_bomb_are_rejected_before_ocr(client, monkeypatch):
    def unexpected_ocr(provider):
        raise AssertionError("Invalid images must not reach OCR")
    monkeypatch.setattr("app.services.file_screening_service.image_engine", unexpected_ocr)
    assert client.post("/api/v1/ai/privacy/image", content=b"not a PNG", headers=headers("image/png")).status_code == 422
    assert client.post("/api/v1/ai/privacy/image", content=image_bytes((2001, 2000)), headers=headers("image/png")).status_code == 422


def test_missing_tesseract_is_reported_without_a_substitute(client, monkeypatch):
    monkeypatch.setattr("app.services.file_screening_service.shutil.which", lambda name: None)
    response = client.post("/api/v1/ai/privacy/image", content=image_bytes(), headers=headers("image/png"))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "OCR_UNAVAILABLE"


def test_structured_sdk_failure_never_echoes_content(client, monkeypatch, caplog):
    def broken_sdk():
        raise RuntimeError("private-file@example.com")
    monkeypatch.setattr("app.services.file_screening_service.structured_sdk", broken_sdk)
    response = client.post("/api/v1/ai/privacy/structured?format=json", content='{"email":"private-file@example.com"}', headers=headers())
    assert response.status_code == 503
    assert "private-file@example.com" not in response.text
    assert "private-file@example.com" not in caplog.text


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="The native Tesseract executable is installed by the Docker image")
def test_real_tesseract_image_pipeline(client):
    from PIL import ImageDraw, ImageFont
    image = Image.new("RGB", (1000, 140), "white")
    ImageDraw.Draw(image).text((20, 30), "Email: hello@example.com", font=ImageFont.load_default(size=40), fill="black")
    output = io.BytesIO()
    image.save(output, format="PNG")
    response = client.post("/api/v1/ai/privacy/image", content=output.getvalue(), headers=headers("image/png"))
    assert response.status_code == 200, response.text
    assert response.json()["data"]["flagged_fields"] > 0


def test_file_scan_slot_rejects_concurrent_work_and_releases_after_failure():
    from app.services.file_screening_service import scan_slot
    from fastapi import HTTPException
    with pytest.raises(RuntimeError):
        with scan_slot():
            with pytest.raises(HTTPException) as error:
                with scan_slot():
                    pass
            assert error.value.status_code == 429
            raise RuntimeError("deliberate test failure")
    with scan_slot():
        pass
