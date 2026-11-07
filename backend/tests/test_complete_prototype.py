"""Complete prototype flows on disposable SQLite, with a private Storage HTTP fake.

No live account, email, database, or hosted file is touched by these tests.
"""
import io
import json
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from PIL import Image
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import get_settings
from app.models.user import User
from app.models.activity import ActivityParticipant
from app.models.garden import Garden
from app.models.location import ActivityCheckIn
from app.models.proof import ProofSubmission
from app.models.points import PointTransaction
from app.models.retention import StorageDeletion
from app.models.usage import UsageSummary
from app.services.retention_service import cleanup
from app.utils.user_time import user_today


@pytest.fixture
def sandbox(monkeypatch):
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    def database():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = database
    settings = get_settings()
    monkeypatch.setattr(settings, "AUTH_ISSUER_URL", "https://private-test.supabase.co/auth/v1")
    from pydantic import SecretStr
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", SecretStr("sb_secret_test-only"))
    state = {"objects": {}, "public": False, "fail_delete": False}
    original = httpx.Client
    def storage(request):
        assert request.headers["apikey"] == "sb_secret_test-only"
        path = request.url.path
        if request.method == "GET" and "/bucket/" in path:
            return httpx.Response(200, json={"public": state["public"]})
        if request.method == "POST" and "/object/sign/" in path:
            return httpx.Response(200, json={"signedURL": path.removeprefix("/storage/v1") + "?token=temporary-test-token"})
        if request.method == "POST" and "/object/activity-proofs/" in path:
            key = path.split("/object/activity-proofs/", 1)[1]
            assert request.headers["content-type"] == "image/jpeg"
            state["objects"][key] = request.content
            return httpx.Response(200, json={"Key": key})
        if request.method == "DELETE":
            if state["fail_delete"]:
                return httpx.Response(503, text="private provider detail")
            for key in json.loads(request.content)["prefixes"]:
                state["objects"].pop(key, None)
            return httpx.Response(200, json=[])
        raise AssertionError(f"Unexpected fake Storage operation: {request.method} {path}")
    monkeypatch.setattr("app.services.storage_service.httpx.Client", lambda **options: original(transport=httpx.MockTransport(storage), **options))
    with TestClient(app, client=("192.0.2.81", 50000)) as client:
        yield client, engine, state
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def identity(client):
    user = uuid.uuid4()
    headers = {"Authorization": f"Bearer {user}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200, response.text
    return user, headers


def planned(client, headers, group=None, requirement="none"):
    response = client.post("/api/v1/activities", headers=headers, json={"title": "Offline walk", "category": "walk",
        "duration_minutes": 10, "visibility": "group" if group else "personal", "group_id": group,
        "proof_requirement": requirement})
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


def elapsed(client, engine, headers, activity):
    assert client.post(f"/api/v1/activities/{activity}/start", headers=headers, json={}).status_code == 200
    with Session(engine) as db:
        for row in db.query(ActivityParticipant).filter_by(activity_id=uuid.UUID(activity)):
            row.started_at = datetime.now(timezone.utc) - timedelta(minutes=12)
        db.commit()


def photo():
    output = io.BytesIO()
    image = Image.new("RGB", (32, 24), "green")
    exif = Image.Exif()
    exif[270] = "Private description must not survive upload"
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


def upload(client, headers, activity, consent=True):
    return client.post(f"/api/v1/activities/{activity}/proofs/photo?consent={str(consent).lower()}",
                       content=photo(), headers={**headers, "Content-Type": "image/jpeg"})


def group_pair(client):
    owner, oh = identity(client)
    member, mh = identity(client)
    group = client.post("/api/v1/groups", headers=oh, json={"name": "Private group"}).json()["data"]["id"]
    token = client.post(f"/api/v1/groups/{group}/invites", headers=oh, json={"max_uses": 5}).json()["data"]["invite_token"]
    assert client.post("/api/v1/group-invites/accept", headers=mh, json={"token": token}).status_code == 200
    return owner, oh, member, mh, group, token


def test_manual_screen_time_updates_one_day_and_is_owner_scoped(sandbox):
    client, engine, _ = sandbox
    owner, headers = identity(client)
    _, outsider = identity(client)
    with Session(engine) as db:
        today = user_today(db, owner).isoformat()
    payload = {"usage_date": today, "total_minutes": 120, "social_minutes": 30, "source": "manual"}
    saved = client.post("/api/v1/insights/manual", headers=headers, json=payload)
    assert saved.status_code == 200, saved.text
    record_id = saved.json()["data"]["id"]
    assert client.post("/api/v1/insights/manual", headers=headers, json={**payload, "total_minutes": 90}).json()["data"]["id"] == record_id
    summary = client.get("/api/v1/insights/summary", headers=headers).json()["data"]
    assert summary["days_recorded"] == 1 and summary["total_screen_time_minutes"] == 90
    assert summary["daily_breakdown"][0]["category_breakdown"] == {"social": 30, "other": 60}
    assert client.post("/api/v1/insights/manual", headers=headers, json={**payload, "social_minutes": 121}).status_code == 422
    assert client.delete(f"/api/v1/insights/records/{record_id}", headers=outsider).status_code == 404
    assert client.delete(f"/api/v1/insights/records/{record_id}", headers=headers).status_code == 200
    assert client.get("/api/v1/insights/summary", headers=headers).json()["data"]["days_recorded"] == 0


def test_manual_dates_use_account_timezone_and_sources_do_not_double_count(sandbox, monkeypatch):
    client, engine, _ = sandbox
    owner, headers = identity(client)
    assert client.patch("/api/v1/users/me/preferences", headers=headers, json={"timezone": "Pacific/Kiritimati"}).status_code == 200
    import app.utils.user_time as clock
    class Fixed(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 6, 23, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(clock, "datetime", Fixed)
    payload = {"usage_date": "2026-11-07", "total_minutes": 90, "social_minutes": 20}
    assert client.post("/api/v1/insights/manual", headers=headers, json=payload).status_code == 200
    with Session(engine) as db:
        db.add(UsageSummary(user_id=owner, usage_date=datetime(2026, 11, 7).date(), total_minutes=200, source="import"))
        db.commit()
    summary = client.get("/api/v1/insights/summary", headers=headers).json()["data"]
    assert summary["end_date"] == "2026-11-07" and summary["days_recorded"] == 1 and summary["total_screen_time_minutes"] == 90
    assert client.post("/api/v1/insights/manual", headers=headers, json={**payload, "usage_date": "2026-11-08"}).status_code == 400


def test_completion_and_focus_retries_never_duplicate_time_or_coins(sandbox):
    client, engine, _ = sandbox
    owner, headers = identity(client)
    activity = planned(client, headers)
    elapsed(client, engine, headers, activity)
    first = client.post(f"/api/v1/activities/{activity}/focus-sessions", headers=headers).json()["data"]
    again = client.post(f"/api/v1/activities/{activity}/focus-sessions", headers=headers).json()["data"]
    assert first["id"] == again["id"]
    end = client.post(f"/api/v1/focus-sessions/{first['id']}/end", headers=headers).json()["data"]
    repeated = client.post(f"/api/v1/focus-sessions/{first['id']}/end", headers=headers).json()["data"]
    assert end["ended_at"] == repeated["ended_at"]
    running = client.post(f"/api/v1/activities/{activity}/focus-sessions", headers=headers).json()["data"]
    for _ in range(2):
        assert client.post(f"/api/v1/activities/{activity}/end", headers=headers).status_code == 200
        assert client.post(f"/api/v1/activities/{activity}/complete", headers=headers).status_code == 200
    stopped = client.get(f"/api/v1/focus-sessions/{running['id']}", headers=headers).json()["data"]
    assert stopped["status"] == "completed" and stopped["ended_at"]
    with Session(engine) as db:
        assert db.query(PointTransaction).filter_by(user_id=owner).count() == 1
        assert db.query(Garden).filter_by(owner_user_id=owner).one().points_balance == 10
    notices = client.get("/api/v1/notifications", headers=headers).json()["data"]
    assert len([row for row in notices if row["type"] == "reward"]) == 1


def test_location_is_optional_fresh_private_and_really_expires(sandbox):
    client, engine, _ = sandbox
    owner, headers = identity(client)
    _, other = identity(client)
    activity = planned(client, headers)
    elapsed(client, engine, headers, activity)
    payload = {"latitude": 1.352123, "longitude": 103.819876, "accuracy_meters": 30,
               "captured_at": datetime.now(timezone.utc).isoformat(), "consent": True}
    path = f"/api/v1/activities/{activity}/check-ins"
    assert client.post(path, headers=headers, json=payload).status_code == 403
    assert client.patch("/api/v1/users/me/preferences", headers=headers, json={"location_enabled": True}).status_code == 200
    assert client.post(path, headers=headers, json={**payload, "consent": False}).status_code == 400
    assert client.post(path, headers=headers, json={**payload, "captured_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()}).status_code == 400
    first = client.post(path, headers=headers, json=payload)
    assert first.status_code == 201, first.text
    assert "latitude" not in first.text and "longitude" not in first.text
    assert client.post(path, headers=headers, json=payload).status_code == 201
    assert client.get(path + "/me", headers=other).status_code == 404
    with Session(engine) as db:
        row = db.query(ActivityCheckIn).one()
        assert float(row.latitude) == 1.352 and float(row.longitude) == 103.82
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert client.get(path + "/me", headers=headers).status_code == 404
    with Session(engine) as db:
        cleanup(db, delete_objects=False)
        assert db.query(ActivityCheckIn).count() == 0


def test_location_withdrawal_deletes_existing_records_and_blocks_new_ones(sandbox):
    client, engine, _ = sandbox
    _, headers = identity(client)
    activity = planned(client, headers)
    elapsed(client, engine, headers, activity)
    client.patch("/api/v1/users/me/preferences", headers=headers, json={"location_enabled": True})
    payload = {"latitude": 1.35, "longitude": 103.82, "accuracy_meters": 20, "captured_at": datetime.now(timezone.utc).isoformat(), "consent": True}
    assert client.post(f"/api/v1/activities/{activity}/check-ins", headers=headers, json=payload).status_code == 201
    assert client.patch("/api/v1/users/me/preferences", headers=headers, json={"location_enabled": False}).status_code == 200
    with Session(engine) as db:
        assert db.query(ActivityCheckIn).count() == 0
    assert client.post(f"/api/v1/activities/{activity}/check-ins", headers=headers, json=payload).status_code == 403


def test_private_photo_upload_strips_metadata_and_deletion_retries(sandbox):
    client, engine, state = sandbox
    _, headers = identity(client)
    _, outsider = identity(client)
    activity = planned(client, headers, requirement="photo")
    elapsed(client, engine, headers, activity)
    client.post(f"/api/v1/activities/{activity}/end", headers=headers)
    assert upload(client, headers, activity, consent=False).status_code == 400
    uploaded = upload(client, headers, activity)
    assert uploaded.status_code == 200, uploaded.text
    proof_id = uploaded.json()["data"]["id"]
    assert uploaded.json()["data"]["status"] == "accepted"
    assert client.get(f"/api/v1/activities/{activity}", headers=headers).json()["data"]["status"] == "completed"
    assert len(state["objects"]) == 1
    key, clean = next(iter(state["objects"].items()))
    assert "Private description" not in str(clean)
    with Image.open(io.BytesIO(clean)) as image:
        assert not image.getexif() and image.format == "JPEG"
    assert client.get(f"/api/v1/proofs/{proof_id}/preview", headers=headers).json()["data"]["expires_in"] == 60
    assert client.get(f"/api/v1/proofs/{proof_id}/preview", headers=outsider).status_code == 403
    assert client.delete(f"/api/v1/proofs/{proof_id}", headers=outsider).status_code == 403
    assert client.delete(f"/api/v1/proofs/{proof_id}", headers=headers).status_code == 200
    state["fail_delete"] = True
    with Session(engine) as db:
        cleanup(db)
        assert db.get(StorageDeletion, key).attempts == 1
    state["fail_delete"] = False
    with Session(engine) as db:
        cleanup(db)
        assert db.get(StorageDeletion, key) is None
    assert not state["objects"]


def test_uncertain_upload_is_queued_for_removal(sandbox, monkeypatch):
    client, engine, state = sandbox
    _, headers = identity(client)
    activity = planned(client, headers, requirement="photo")
    elapsed(client, engine, headers, activity)
    client.post(f"/api/v1/activities/{activity}/end", headers=headers)
    from app.services.storage_service import StorageService
    original = StorageService.upload
    def timeout_after_store(self, key, content, mime):
        original(self, key, content, mime)
        raise HTTPException(503, detail={"code": "STORAGE_UNAVAILABLE", "message": "Upload timed out."})
    monkeypatch.setattr(StorageService, "upload", timeout_after_store)
    assert upload(client, headers, activity).status_code == 503
    assert len(state["objects"]) == 1
    with Session(engine) as db:
        assert db.query(ProofSubmission).count() == 0
        assert db.query(StorageDeletion).count() == 1
        cleanup(db)
        assert db.query(StorageDeletion).count() == 0
    assert not state["objects"]


def test_public_bucket_or_fabricated_photo_is_rejected(sandbox):
    client, engine, state = sandbox
    _, headers = identity(client)
    activity = planned(client, headers, requirement="photo")
    elapsed(client, engine, headers, activity)
    client.post(f"/api/v1/activities/{activity}/end", headers=headers)
    state["public"] = True
    assert upload(client, headers, activity).status_code == 503
    assert not state["objects"]
    invalid = client.post(f"/api/v1/activities/{activity}/proofs/photo?consent=true", headers={**headers, "Content-Type": "image/jpeg"}, content=b"not an image")
    assert invalid.status_code == 400
    assert client.post(f"/api/v1/activities/{activity}/proofs", headers=headers, json={"proof_type": "photo", "storage_key": "other-user/private.jpg"}).status_code == 400


def test_group_photo_review_requires_other_eligible_member_and_rewards_once(sandbox):
    client, engine, _ = sandbox
    owner, oh, member, mh, group, _ = group_pair(client)
    activity = planned(client, oh, group, "photo_or_group_confirmation")
    assert client.post(f"/api/v1/activities/{activity}/join", headers=mh).status_code == 200
    elapsed(client, engine, oh, activity)
    assert client.post(f"/api/v1/activities/{activity}/end", headers=mh).status_code == 403
    assert client.post(f"/api/v1/activities/{activity}/end", headers=oh).status_code == 200
    response = upload(client, oh, activity)
    assert response.status_code == 200, response.text
    proof_id = response.json()["data"]["id"]
    assert response.json()["data"]["status"] == "pending"
    assert client.post(f"/api/v1/proofs/{proof_id}/confirm", headers=oh, json={"decision": "confirm"}).status_code == 403
    assert len(client.get(f"/api/v1/activities/{activity}/proofs/review", headers=mh).json()["data"]) == 1
    assert client.post(f"/api/v1/proofs/{proof_id}/confirm", headers=mh, json={"decision": "confirm"}).status_code == 200
    assert client.post(f"/api/v1/proofs/{proof_id}/confirm", headers=mh, json={"decision": "confirm"}).status_code == 409
    with Session(engine) as db:
        assert db.query(PointTransaction).filter_by(user_id=owner).count() == 1
        assert db.query(Garden).filter_by(owner_group_id=uuid.UUID(group)).one().points_balance == 10
    assert any(row["type"] == "proof_decision" for row in client.get("/api/v1/notifications", headers=oh).json()["data"])


def test_group_owner_transfer_revocation_and_removed_access(sandbox):
    client, _, _ = sandbox
    owner, oh, member, mh, group, token = group_pair(client)
    invitation = client.post(f"/api/v1/groups/{group}/invites", headers=oh, json={"max_uses": 1}).json()["data"]
    assert client.patch(f"/api/v1/groups/{group}/members/{owner}", headers=mh, json={"role": "admin"}).status_code == 403
    assert client.delete(f"/api/v1/groups/{group}/invites/{invitation['id']}", headers=oh).status_code == 200
    _, third = identity(client)
    assert client.post("/api/v1/group-invites/accept", headers=third, json={"token": invitation["invite_token"]}).status_code == 400
    assert client.post(f"/api/v1/groups/{group}/transfer-ownership", headers=oh, json={"user_id": str(member)}).status_code == 200
    assert client.delete(f"/api/v1/groups/{group}/members/{owner}", headers=mh).status_code == 200
    assert client.get(f"/api/v1/groups/{group}", headers=oh).status_code == 403
    assert client.post("/api/v1/group-invites/accept", headers=oh, json={"token": token}).status_code == 403


def test_notifications_friend_requests_and_targeted_invites_are_private(sandbox):
    client, _, _ = sandbox
    sender, sh = identity(client)
    receiver, rh = identity(client)
    _, outsider = identity(client)
    assert client.post("/api/v1/friend-requests", headers=sh, json={"receiver_id": str(receiver)}).status_code == 201
    request = client.get("/api/v1/friend-requests", headers=rh).json()["data"][0]
    assert client.post(f"/api/v1/friend-requests/{request['id']}/accept", headers=outsider).status_code == 404
    notice = client.get("/api/v1/notifications", headers=rh).json()["data"][0]
    assert client.post(f"/api/v1/notifications/{notice['id']}/read", headers=sh).status_code == 404
    assert client.post(f"/api/v1/friend-requests/{request['id']}/accept", headers=rh).status_code == 200
    assert client.post("/api/v1/notifications/read-all", headers=rh).status_code == 200
    assert all(row["read_at"] for row in client.get("/api/v1/notifications", headers=rh).json()["data"])
    group = client.post("/api/v1/groups", headers=sh, json={"name": "Targeted"}).json()["data"]["id"]
    invite = client.post(f"/api/v1/groups/{group}/invites", headers=sh, json={"receiver_id": str(receiver)}).json()["data"]
    assert client.post(f"/api/v1/group-invitations/{invite['id']}/accept", headers=outsider).status_code == 400
    assert client.post(f"/api/v1/group-invitations/{invite['id']}/accept", headers=rh).status_code == 200


def test_export_is_owner_scoped_and_never_contains_invitation_hashes(sandbox):
    client, engine, _ = sandbox
    owner, oh, _, mh, group, _ = group_pair(client)
    client.post(f"/api/v1/groups/{group}/invites", headers=oh, json={})
    with Session(engine) as db:
        other = db.query(User).filter(User.id != owner).one()
        other.display_name = "Other person's private account profile"
        db.commit()
    response = client.get("/api/v1/users/me/export", headers=oh)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert "token_hash" not in response.text and "storage_key" not in response.text
    assert "Other person's private account profile" not in response.text
    assert response.json()["data"]["users"][0]["id"] == str(owner)
    assert client.get("/api/v1/users/me/export").status_code == 401


def test_expired_photo_access_stops_and_file_is_really_removed(sandbox):
    client, engine, state = sandbox
    _, headers = identity(client)
    activity = planned(client, headers, requirement="photo")
    elapsed(client, engine, headers, activity)
    client.post(f"/api/v1/activities/{activity}/end", headers=headers)
    proof_id = upload(client, headers, activity).json()["data"]["id"]
    with Session(engine) as db:
        db.get(ProofSubmission, uuid.UUID(proof_id)).retention_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert client.get(f"/api/v1/proofs/{proof_id}/preview", headers=headers).status_code == 404
    with Session(engine) as db:
        cleanup(db)
        assert db.get(ProofSubmission, uuid.UUID(proof_id)).storage_key is None
    assert not state["objects"]


def test_onboarding_requires_notice_ack_and_privacy_notice_is_public(sandbox):
    client, _, _ = sandbox
    _, headers = identity(client)
    assert client.get("/api/v1/privacy-notice").status_code == 200
    assert client.post("/api/v1/users/me/onboarding", headers=headers, json={"privacy_notice_acknowledged": False}).status_code == 422
    assert client.post("/api/v1/users/me/onboarding", headers=headers, json={"privacy_notice_acknowledged": True}).status_code == 200
    assert client.get("/api/v1/users/me/preferences", headers=headers).json()["data"]["onboarding_completed_at"]


def test_optional_sharing_requires_operator_privacy_contact_in_production(monkeypatch):
    from app.utils.privacy_setup import require_optional_data_setup
    settings = get_settings()
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "PRIVACY_CONTACT_EMAIL", "")
    with pytest.raises(HTTPException):
        require_optional_data_setup()
    monkeypatch.setattr(settings, "PRIVACY_CONTACT_EMAIL", "privacy@example.com")
    require_optional_data_setup()
