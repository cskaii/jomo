"""Read panels must not acquire PostgreSQL write locks; mutations still do."""
import uuid
from contextlib import contextmanager

import pytest
from fastapi import HTTPException
from sqlalchemy import event
from sqlalchemy.dialects import postgresql

from app.db.session import SessionLocal
from app.schemas.activity import ActivityCreateRequest
from app.services.activity_service import ActivityService
from app.services.focus_service import FocusService
from app.services.proof_service import ProofService
from app.services.user_service import UserService


@pytest.fixture
def activity_context():
    with SessionLocal() as db:
        user_id = uuid.uuid4()
        UserService(db).get_or_create_profile(user_id)
        service = ActivityService(db)
        activity = service.create_activity(user_id, ActivityCreateRequest(
            title="Quiet walk", category="outdoor", duration_minutes=30,
            max_participants=1, proof_requirement="none",
        ))
        yield db, user_id, activity.id


@contextmanager
def postgres_statements(db):
    statements = []
    def record(state):
        if state.is_select:
            statements.append(str(state.statement.compile(dialect=postgresql.dialect())))
    event.listen(db, "do_orm_execute", record)
    try:
        yield statements
    finally:
        event.remove(db, "do_orm_execute", record)


def test_activity_read_panels_do_not_take_exclusive_locks(activity_context):
    db, user_id, activity_id = activity_context
    service, proofs = ActivityService(db), ProofService(db)
    with postgres_statements(db) as statements:
        assert service.get_activity(user_id, activity_id).status == "published"
        assert len(service.list_participants(user_id, activity_id)) == 1
        assert proofs.list_for_review(user_id, activity_id) == []
        with pytest.raises(HTTPException) as missing:
            proofs.get_my_proof(user_id, activity_id)
        assert missing.value.status_code == 404
    assert statements
    assert not any("FOR UPDATE" in sql for sql in statements)


def test_start_is_locked_and_retries_preserve_start_time(activity_context):
    db, user_id, activity_id = activity_context
    service = ActivityService(db)
    with postgres_statements(db) as statements:
        started = service.start_activity(user_id, activity_id, None)
        original_start = started.started_at
    assert started.status == "active"
    assert any("FROM activities" in sql and "FOR UPDATE" in sql for sql in statements)
    assert service.start_activity(user_id, activity_id, None).started_at == original_start
    participant = service.list_participants(user_id, activity_id)[0]
    assert participant.status == "active" and participant.started_at == original_start
    service.end_activity(user_id, activity_id)
    first_end = service.get_activity(user_id, activity_id).ended_at
    assert service.end_activity(user_id, activity_id).ended_at == first_end
    assert service.list_participants(user_id, activity_id)[0].points_awarded == 0


def test_focus_reads_are_unlocked_and_updates_are_locked(activity_context):
    db, user_id, activity_id = activity_context
    ActivityService(db).start_activity(user_id, activity_id, None)
    service = FocusService(db)
    focus_id = service.start_session(user_id, activity_id).id
    assert service.start_session(user_id, activity_id).id == focus_id
    with postgres_statements(db) as reads:
        assert service.get_session(user_id, focus_id).status == "active"
    assert not any("FOR UPDATE" in sql for sql in reads)
    with postgres_statements(db) as writes:
        assert service.end_session(user_id, focus_id).status == "completed"
    assert any("FROM focus_sessions" in sql and "FOR UPDATE" in sql for sql in writes)


def test_read_and_write_authorization_remain_enforced(activity_context):
    db, user_id, activity_id = activity_context
    outsider = uuid.uuid4()
    UserService(db).get_or_create_profile(outsider)
    service = ActivityService(db)
    for action in (
        lambda: service.get_activity(outsider, activity_id),
        lambda: service.start_activity(outsider, activity_id, None),
        lambda: ProofService(db).list_for_review(outsider, activity_id),
    ):
        with pytest.raises(HTTPException) as denied:
            action()
        assert denied.value.status_code == 403
