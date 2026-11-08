"""Bound SQL round trips and preserve per-account state in Activities responses."""
import uuid
from contextlib import contextmanager

from sqlalchemy import event

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.schemas.progression import ActivitiesOverviewResponse
from app.services.progression_service import ProgressionService


@contextmanager
def select_queries(db):
    statements = []
    def record(connection, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)
    event.listen(db.bind, "before_cursor_execute", record)
    try:
        yield statements
    finally:
        event.remove(db.bind, "before_cursor_execute", record)


def test_library_queries_do_not_grow_with_card_count(monkeypatch):
    user_id = uuid.uuid4()
    with SessionLocal() as db:
        service = ProgressionService(db)
        service.seed_catalog()
        service.get_progression(user_id)
        monkeypatch.setattr(get_settings(), "AUTO_SEED_CATALOG", False)
        with select_queries(db) as statements:
            quests = service.list_quests(user_id)
        assert len(quests) == 35
        assert len(statements) <= 5, len(statements)
        with select_queries(db) as filtered_statements:
            filtered = service.list_quests(user_id, category="movement_outdoors")
        assert len(filtered) == 5
        assert len(filtered_statements) <= 5


def test_overview_has_bounded_queries_and_matches_existing_responses(monkeypatch):
    user_id = uuid.uuid4()
    with SessionLocal() as db:
        service = ProgressionService(db)
        service.seed_catalog()
        monkeypatch.setattr(get_settings(), "AUTO_SEED_CATALOG", False)
        service.activities_overview(user_id)  # First visit creates assignments.
        with select_queries(db) as statements:
            result = service.activities_overview(user_id)
        assert len(statements) <= 35, len(statements)
        ActivitiesOverviewResponse.model_validate(result)
        assert result["progress"] == service.progression_payload(user_id)
        assert result["quests"] == service.list_quests(user_id)
        assert result["discovery"] == service.daily_discovery(user_id)
        assert result["achievements"] == service.list_achievements(user_id)
        for kind in ("daily", "weekly"):
            assert result[kind] == [service.mission_payload(row) for row in service.get_missions(user_id, kind)]
        catalogue = {item["code"]: item for item in result["quests"]}
        for item in result["discovery"]["quests"] + result["discovery"]["suggestions"]:
            assert item == catalogue[item["code"]]


def test_batched_cards_and_achievements_keep_accounts_separate(monkeypatch):
    user_id, other_id = uuid.uuid4(), uuid.uuid4()
    with SessionLocal() as db:
        service = ProgressionService(db)
        service.seed_catalog()
        service.get_progression(user_id)
        service.get_progression(other_id)
        monkeypatch.setattr(get_settings(), "AUTO_SEED_CATALOG", False)
        service.toggle_favorite(user_id, "Q001")
        service.toggle_favorite(other_id, "Q005")
        completed = service.start_quest(user_id, "Q001")
        service.complete_quest(user_id, completed.id, "A quiet reset")
        active = service.start_quest(user_id, "Q003")
        active_id = active.id
        abandoned = service.start_quest(user_id, "Q004")
        service.abandon_quest(user_id, abandoned.id)
        service.start_quest(other_id, "Q002")
        cards = {q["code"]: q for q in service.list_quests(user_id)}
        assert cards["Q001"]["completion_count"] == 1
        assert cards["Q001"]["completed_today"]
        assert cards["Q001"]["is_favorite"]
        assert cards["Q003"]["active_instance_id"] == active_id
        assert cards["Q004"]["active_instance_id"] is None
        assert cards["Q004"]["completion_count"] == 0
        assert cards["Q002"]["active_instance_id"] is None
        assert not cards["Q005"]["is_favorite"]
        assert [q["code"] for q in service.list_quests(user_id, favorites=True)] == ["Q001"]
        achievements = {a["code"]: a for a in service.list_achievements(user_id)}
        assert achievements["A001"]["unlocked"]
        assert achievements["A006"]["current_progress"] == 1
        assert not any(a["unlocked"] for a in service.list_achievements(other_id))
