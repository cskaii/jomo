"""Exercise persisted discovery and rewards against a disposable real database."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.db.session import SessionLocal
from app.models.progression import MissionDefinition, UserMission, UserQuestInstance
from app.models.activity import ActivityParticipant
from app.models.user import UserPreference
from app.services.progression_service import ProgressionService


@pytest.fixture
def clock(monkeypatch):
    import app.services.progression_service as module

    class Clock(datetime):
        instant = datetime(2026, 11, 8, 4, tzinfo=timezone.utc)

        @classmethod
        def now(cls, tz=None):
            return cls.instant.astimezone(tz) if tz else cls.instant.replace(tzinfo=None)

    with SessionLocal() as db:
        ProgressionService(db).seed_catalog()
        original = [(m.id, m.metric, m.target_value, m.category_filter) for m in db.query(MissionDefinition).all()]
    monkeypatch.setattr(module, "datetime", Clock)
    yield Clock
    with SessionLocal() as db:
        for ident, metric, target, categories in original:
            row = db.get(MissionDefinition, ident)
            row.metric, row.target_value, row.category_filter = metric, target, categories
        db.commit()


def test_discovery_is_stable_and_rotates_across_cycles(clock):
    user_id = uuid.uuid4()
    shown, previous, mission_shown, previous_missions = set(), set(), set(), set()
    for day in range(14):
        clock.instant = datetime(2026, 11, 8, 4, tzinfo=timezone.utc) + timedelta(days=day)
        with SessionLocal() as db:
            service = ProgressionService(db)
            today = service.daily_discovery(user_id)
            assert today == service.daily_discovery(user_id)
            assert len(today["quests"]) == len(today["suggestions"]) == 3
            codes = [q["code"] for q in today["quests"] + today["suggestions"]]
            assert len(set(codes)) == 6
            assert not previous.intersection(codes)
            if shown.intersection(codes) and len(shown) < 35:
                assert len(shown.union(codes)) == 35
            shown.update(codes)
            missions = service.get_missions(user_id, "daily")
            current_missions = {m.mission.code for m in missions}
            assert len(current_missions) == 3
            assert not previous_missions.intersection(current_missions)
            if day < 3:
                assert not mission_shown.intersection(current_missions)
            mission_shown.update(current_missions)
            previous, previous_missions = set(codes), current_missions
    assert len(shown) == 35


def test_suggestion_completion_survives_midnight_and_awards_once(clock):
    user_id = uuid.uuid4()
    with SessionLocal() as db:
        service = ProgressionService(db)
        today = service.daily_discovery(user_id)
        suggestion = today["suggestions"][0]
        yesterday = service.get_missions(user_id, "daily")[0]
        yesterday_id = yesterday.id
        yesterday.mission.metric = "quest_count"
        yesterday.mission.target_value = 1
        yesterday.mission.category_filter = None
        db.commit()
        instance_id = service.start_quest(user_id, suggestion["code"]).id
        assert service.start_quest(user_id, suggestion["code"]).id == instance_id
        clock.instant += timedelta(days=1)
        tomorrow = service.daily_discovery(user_id)
        assert tomorrow["period_key"] != today["period_key"]
        assert service.get_quest(user_id, suggestion["code"])["active_instance_id"] == instance_id
        instance = db.get(UserQuestInstance, instance_id)
        participant = db.query(ActivityParticipant).filter_by(activity_id=instance.activity_id, user_id=user_id).one()
        participant.started_at = clock.instant - timedelta(minutes=suggestion["estimated_duration_minutes"])
        db.commit()
        result = service.complete_quest(user_id, instance_id, "A quiet reset")
        assert result["xp_awarded"] == suggestion["xp_reward"]
        assert result["garden_points_awarded"] > 0
        duplicate = service.complete_quest(user_id, instance_id, None)
        assert duplicate["already_completed"]
        assert duplicate["xp_awarded"] == duplicate["garden_points_awarded"] == 0
        assert service.progression_payload(user_id)["completed_quests"] == 1
        state = service.get_quest(user_id, suggestion["code"])
        assert state["completed_today"] and state["active_instance_id"] is None
        with pytest.raises(HTTPException) as error:
            service.start_quest(user_id, suggestion["code"])
        assert error.value.status_code == 409
        assert db.get(UserMission, yesterday_id).current_progress == 0


def test_suggestion_advances_daily_missions_and_reward_claim_is_idempotent(clock):
    user_id = uuid.uuid4()
    with SessionLocal() as db:
        service = ProgressionService(db)
        mission = service.get_missions(user_id, "daily")[0]
        mission.mission.metric, mission.mission.target_value, mission.mission.category_filter = "quest_count", 1, None
        db.commit()
        suggestion = service.daily_discovery(user_id)["suggestions"][0]
        instance = service.start_quest(user_id, suggestion["code"])
        service.complete_quest(user_id, instance.id, None)
        service.get_missions(user_id, "daily")
        assert mission.current_progress == 1
        before = service.progression_payload(user_id)["lifetime_xp"]
        reward = mission.mission.reward_xp
        service.claim_mission(user_id, mission.id)
        service.claim_mission(user_id, mission.id)
        assert service.progression_payload(user_id)["lifetime_xp"] == before + reward


def test_midnight_uses_saved_timezone_and_daylight_saving(clock):
    user_id = uuid.uuid4()
    with SessionLocal() as db:
        service = ProgressionService(db)
        service.get_progression(user_id)
        pref = db.get(UserPreference, user_id)
        pref.timezone = "America/New_York"
        db.commit()
        clock.instant = datetime(2026, 3, 8, 12, tzinfo=timezone.utc)
        key, start, end = service._period(user_id, "daily")
        assert key == "2026-03-08"
        assert end - start == timedelta(hours=23)
        pref.timezone = "Asia/Singapore"
        db.commit()
        clock.instant = datetime(2026, 11, 8, 15, 59, tzinfo=timezone.utc)
        before = service.daily_discovery(user_id)
        clock.instant += timedelta(minutes=1)
        after = service.daily_discovery(user_id)
        assert before["period_key"] == "2026-11-08"
        assert after["period_key"] == "2026-11-09"


def test_small_catalogues_and_independent_users(clock):
    user_id, other_user = uuid.uuid4(), uuid.uuid4()
    with SessionLocal() as db:
        service = ProgressionService(db)
        first = service.daily_discovery(user_id)
        service.daily_discovery(other_user)
        assert service.daily_discovery(user_id) == first
        # Pure selector must return fewer items rather than duplicate within a day.
        from types import SimpleNamespace
        pool = [SimpleNamespace(code=str(n)) for n in range(2)]
        assert len(service._rotate(pool, [], 6, "small")) == 2
        assert len(service._rotate([], [], 6, "empty")) == 0


def test_weekly_missions_rotate_and_minutes_use_recorded_time(clock):
    user_id = uuid.uuid4()
    seen = set()
    with SessionLocal() as db:
        service = ProgressionService(db)
        for week in range(2):
            clock.instant = datetime(2026, 11, 9, 4, tzinfo=timezone.utc) + timedelta(weeks=week)
            missions = service.get_missions(user_id, "weekly")
            codes = {m.mission.code for m in missions}
            assert not seen.intersection(codes)
            seen.update(codes)
        daily = service.get_missions(user_id, "daily")[0]
        daily.mission.metric, daily.mission.target_value, daily.mission.category_filter = "minutes", 45, None
        db.commit()
        instance = service.start_quest(user_id, "Q027")  # advertised as 60 minutes
        participant = db.query(ActivityParticipant).filter_by(activity_id=instance.activity_id, user_id=user_id).one()
        participant.started_at = clock.instant - timedelta(minutes=7)
        db.commit()
        service.complete_quest(user_id, instance.id, None)
        service.get_missions(user_id, "daily")
        assert daily.current_progress == 7


def test_explicit_catalogue_install_recovers_empty_first_visit(monkeypatch, clock):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.config import get_settings
    from app.db.base import Base
    from app.models.progression import Quest
    from app.models.user import User

    monkeypatch.setattr(get_settings(), "AUTO_SEED_CATALOG", False)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        with Session(engine, autoflush=False) as db:
            service = ProgressionService(db)
            user_id = uuid.uuid4()
            assert service.daily_discovery(user_id)["quests"] == []
            assert db.query(Quest).count() == 0
            service.seed_catalog(explicit=True)
            service.seed_catalog(explicit=True)
            assert db.query(Quest).count() == 35
            assert db.query(User).count() == 1
            assert len(service.daily_discovery(user_id)["suggestions"]) == 3
    finally:
        engine.dispose()
