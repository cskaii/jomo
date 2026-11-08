import random
import uuid
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.data.quest_catalog import ACHIEVEMENTS, CATEGORIES, MISSIONS, QUESTS, XP_BY_DIFFICULTY
from app.models.activity import Activity, ActivityParticipant
from app.models.garden import Garden
from app.models.progression import (
    AchievementDefinition, DailyQuestSelection, MissionDefinition, Quest, QuestFavorite,
    UserAchievement, UserMission, UserProgression, UserQuestInstance, XpTransaction,
)
from app.models.user import User, UserPreference
from app.services.points_service import PointsService
from app.services.user_service import UserService
from app.core.config import get_settings


def xp_required(level: int) -> int:
    return 100 + 50 * (level - 1)


class ProgressionService:
    def __init__(self, db: Session):
        self.db = db

    def seed_catalog(self, *, explicit: bool = False) -> None:
        if not explicit and not get_settings().AUTO_SEED_CATALOG:
            return
        existing = {value for (value,) in self.db.query(Quest.code).all()}
        for code, title, category, minutes, difficulty, instructions in QUESTS:
            if code not in existing:
                self.db.add(Quest(
                    code=code, title=title,
                    description=instructions.split(".")[0] + ".",
                    instructions=instructions, category=category,
                    difficulty=difficulty, estimated_duration_minutes=minutes,
                    xp_reward=XP_BY_DIFFICULTY[difficulty], repeatability="daily",
                    proof_requirement="none",
                    reflection_prompt="What did you notice or enjoy?",
                ))
        mission_codes = {value for (value,) in self.db.query(MissionDefinition.code).all()}
        for code, title, kind, metric, target, categories, reward_xp in MISSIONS:
            if code not in mission_codes:
                self.db.add(MissionDefinition(
                    code=code, title=title, description="Progress updates from completed JOMO quests.",
                    mission_type=kind, metric=metric, target_value=target,
                    category_filter={"categories": categories} if categories else None,
                    reward_xp=reward_xp,
                ))
        achievement_codes = {value for (value,) in self.db.query(AchievementDefinition.code).all()}
        for code, name, metric, target, category, reward_xp in ACHIEVEMENTS:
            if code not in achievement_codes:
                self.db.add(AchievementDefinition(
                    code=code, name=name, description=f"Reach {target} qualifying completed quests.",
                    metric=metric, target_value=target, category_filter=category,
                    reward_xp=reward_xp,
                ))
        self.db.commit()

    def get_progression(self, user_id: uuid.UUID) -> UserProgression:
        # The quest entry point must also onboard a verified first-time user.
        UserService(self.db).get_or_create_profile(user_id)
        progression = self.db.get(UserProgression, user_id)
        if not progression:
            progression = UserProgression(user_id=user_id)
            self.db.add(progression)
            self.db.commit()
            self.db.refresh(progression)
        return progression

    def progression_payload(self, user_id: uuid.UUID) -> dict:
        progress = self.get_progression(user_id)
        garden = self.db.query(Garden).filter(Garden.owner_user_id == user_id, Garden.garden_type == "personal").first()
        unlocked = self.db.query(UserAchievement).filter(UserAchievement.user_id == user_id).count()
        return {
            "user_id": user_id, "level": progress.level,
            "xp_current": progress.xp_current, "xp_to_next_level": xp_required(progress.level),
            "lifetime_xp": progress.lifetime_xp, "completed_quests": progress.completed_quests,
            "current_streak": progress.current_streak, "longest_streak": progress.longest_streak,
            "garden_points": garden.points_balance if garden else 0,
            "achievements_unlocked": unlocked,
        }

    def _timezone(self, user_id: uuid.UUID) -> ZoneInfo:
        pref = self.db.get(UserPreference, user_id)
        try:
            return ZoneInfo(pref.timezone if pref else "Asia/Singapore")
        except Exception:
            return ZoneInfo("Asia/Singapore")

    def _local_date(self, user_id: uuid.UUID, value: datetime | None = None) -> date:
        value = value or datetime.now(timezone.utc)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(self._timezone(user_id)).date()

    def _quest_payload(self, quest: Quest, user_id: uuid.UUID) -> dict:
        favorite = self.db.get(QuestFavorite, (user_id, quest.id)) is not None
        active = self.db.query(UserQuestInstance).filter_by(user_id=user_id, quest_id=quest.id, status="active").first()
        completed = self.db.query(UserQuestInstance).filter_by(user_id=user_id, quest_id=quest.id, status="completed").all()
        return {
            "id": quest.id, "code": quest.code, "title": quest.title,
            "description": quest.description, "instructions": quest.instructions,
            "category": quest.category, "category_label": CATEGORIES.get(quest.category, quest.category),
            "difficulty": quest.difficulty, "estimated_duration_minutes": quest.estimated_duration_minutes,
            "xp_reward": quest.xp_reward, "repeatability": quest.repeatability,
            "proof_requirement": quest.proof_requirement, "reflection_prompt": quest.reflection_prompt,
            "is_favorite": favorite, "active_instance_id": active.id if active else None,
            "completion_count": len(completed),
            "completed_today": any(item.completed_at and self._local_date(user_id, item.completed_at) == self._local_date(user_id) for item in completed),
        }

    def _lock_user(self, user_id):
        # All quest/mission mutations take the same lock before reading state.
        # PostgreSQL serializes concurrent tabs and duplicate reward requests.
        self.db.query(User).filter_by(id=user_id).populate_existing().with_for_update().one()

    @staticmethod
    def _rotate(pool, history, count, seed, category_key=None):
        """Least-shown first: exhaust unseen content before starting another cycle.

        The previous selection is excluded at a cycle boundary when the pool
        permits it. Within each exposure tier prefer varied categories.
        """
        rng = random.Random(seed)
        candidates = list(pool)
        rng.shuffle(candidates)
        exposures = Counter(code for batch in history for code in batch)
        last_seen = {code: index for index, batch in enumerate(history) for code in batch}
        previous = set(history[-1]) if history else set()
        selected, categories = [], set()
        while candidates and len(selected) < count:
            fresh = [item for item in candidates if item.code not in previous]
            eligible = fresh if fresh else candidates
            item = min(eligible, key=lambda item: (
                exposures[item.code],
                bool(category_key and category_key(item) in categories),
                last_seen.get(item.code, -1),
            ))
            selected.append(item)
            if category_key:
                categories.add(category_key(item))
            candidates.remove(item)
        return selected

    def daily_discovery(self, user_id):
        self.seed_catalog()
        self.get_progression(user_id)
        self._lock_user(user_id)
        key, _, end = self._period(user_id, "daily")
        selection = self.db.get(DailyQuestSelection, (user_id, key))
        if selection and not (selection.quest_codes or selection.suggestion_codes):
            # A catalogue installed after an empty first visit is usable today.
            self.db.delete(selection)
            self.db.flush()
            selection = None
        if not selection:
            pool = self.db.query(Quest).filter_by(is_active=True).order_by(Quest.code).all()
            rows = self.db.query(DailyQuestSelection).filter(
                DailyQuestSelection.user_id == user_id,
                DailyQuestSelection.period_key < key,
            ).order_by(DailyQuestSelection.period_key).all()
            history = [row.quest_codes + row.suggestion_codes for row in rows]
            chosen = self._rotate(pool, history, 6, f"{user_id}:discovery:{key}", lambda item: item.category)
            # Interleave categories between the two sections.
            selection = DailyQuestSelection(user_id=user_id, period_key=key,
                quest_codes=[item.code for item in chosen[::2]],
                suggestion_codes=[item.code for item in chosen[1::2]])
            self.db.add(selection)
            self.db.flush()
        codes = selection.quest_codes + selection.suggestion_codes
        catalogue = {item.code: item for item in self.db.query(Quest).filter(
            Quest.code.in_(codes), Quest.is_active.is_(True)).all()}
        result = {
            "period_key": key, "timezone": str(self._timezone(user_id)), "refresh_at": end,
            "quests": [self._quest_payload(catalogue[code], user_id) for code in selection.quest_codes if code in catalogue],
            "suggestions": [self._quest_payload(catalogue[code], user_id) for code in selection.suggestion_codes if code in catalogue],
        }
        self.db.commit()
        return result

    def list_quests(self, user_id: uuid.UUID, category=None, difficulty=None, search=None, favorites=False) -> list[dict]:
        self.seed_catalog()
        query = self.db.query(Quest).filter(Quest.is_active.is_(True))
        if category:
            query = query.filter(Quest.category == category)
        if difficulty:
            query = query.filter(Quest.difficulty == difficulty)
        if search:
            query = query.filter(Quest.title.ilike(f"%{search}%"))
        quests = query.order_by(Quest.code).all()
        payloads = [self._quest_payload(quest, user_id) for quest in quests]
        return [item for item in payloads if item["is_favorite"]] if favorites else payloads

    def get_quest(self, user_id: uuid.UUID, code: str) -> dict:
        self.seed_catalog()
        quest = self.db.query(Quest).filter(Quest.code == code, Quest.is_active.is_(True)).first()
        if not quest:
            raise HTTPException(404, detail={"code": "QUEST_NOT_FOUND", "message": "Quest not found."})
        return self._quest_payload(quest, user_id)

    def toggle_favorite(self, user_id: uuid.UUID, code: str) -> bool:
        quest = self.db.query(Quest).filter(Quest.code == code).first()
        if not quest:
            raise HTTPException(404, detail={"code": "QUEST_NOT_FOUND", "message": "Quest not found."})
        favorite = self.db.get(QuestFavorite, (user_id, quest.id))
        if favorite:
            self.db.delete(favorite)
            state = False
        else:
            self.db.add(QuestFavorite(user_id=user_id, quest_id=quest.id))
            state = True
        self.db.commit()
        return state

    def start_quest(self, user_id: uuid.UUID, code: str) -> UserQuestInstance:
        self.seed_catalog()
        self.get_progression(user_id)
        self._lock_user(user_id)
        quest = self.db.query(Quest).filter(Quest.code == code, Quest.is_active.is_(True)).first()
        if not quest:
            raise HTTPException(404, detail={"code": "QUEST_NOT_FOUND", "message": "Quest not found."})
        active = self.db.query(UserQuestInstance).filter_by(user_id=user_id, quest_id=quest.id, status="active").first()
        if active:
            return active
        today = self._local_date(user_id)
        completed = self.db.query(UserQuestInstance).filter_by(user_id=user_id, quest_id=quest.id, status="completed").all()
        if quest.repeatability == "daily" and any(self._local_date(user_id, item.completed_at) == today for item in completed if item.completed_at):
            raise HTTPException(409, detail={"code": "QUEST_COOLDOWN", "message": "This quest can be completed again tomorrow."})
        now = datetime.now(timezone.utc)
        activity = Activity(
            created_by=user_id, group_id=None, title=quest.title, description=quest.instructions,
            category=quest.category, visibility="personal", status="active",
            duration_minutes=quest.estimated_duration_minutes, max_participants=1,
            location_required=False, proof_requirement=quest.proof_requirement,
            points_per_minute=1.0, max_reward_points=min(quest.estimated_duration_minutes, 60),
            published_at=now, started_at=now,
        )
        self.db.add(activity)
        self.db.flush()
        self.db.add(ActivityParticipant(
            activity_id=activity.id, user_id=user_id, status="active", started_at=now,
        ))
        instance = UserQuestInstance(user_id=user_id, quest_id=quest.id, activity_id=activity.id, started_at=now)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def abandon_quest(self, user_id: uuid.UUID, instance_id: uuid.UUID) -> UserQuestInstance:
        self._lock_user(user_id)
        instance = self._instance(user_id, instance_id)
        if instance.status != "active":
            raise HTTPException(409, detail={"code": "INVALID_QUEST_STATE", "message": "Only an active quest can be abandoned."})
        now = datetime.now(timezone.utc)
        instance.status, instance.abandoned_at = "abandoned", now
        activity = self.db.get(Activity, instance.activity_id)
        activity.status, activity.ended_at = "cancelled", now
        participant = self.db.query(ActivityParticipant).filter_by(activity_id=activity.id, user_id=user_id).first()
        participant.status, participant.ended_at = "left", now
        self.db.commit()
        return instance

    def complete_quest(self, user_id: uuid.UUID, instance_id: uuid.UUID, reflection: str | None) -> dict:
        self.get_progression(user_id)
        self._lock_user(user_id)
        instance = self._instance(user_id, instance_id)
        quest = instance.quest
        if instance.status == "completed":
            payload = self.progression_payload(user_id)
            return {"instance_id": instance.id, "already_completed": True, "xp_awarded": 0,
                    "garden_points_awarded": 0, "new_level": payload["level"],
                    "xp_current": payload["xp_current"], "xp_to_next_level": payload["xp_to_next_level"],
                    "unlocked_achievements": []}
        if instance.status != "active":
            raise HTTPException(409, detail={"code": "INVALID_QUEST_STATE", "message": "This quest is not active."})
        now = datetime.now(timezone.utc)
        activity = self.db.get(Activity, instance.activity_id)
        participant = self.db.query(ActivityParticipant).filter_by(activity_id=activity.id, user_id=user_id).first()
        elapsed = max(0, int((now.replace(tzinfo=None) - participant.started_at.replace(tzinfo=None)).total_seconds() / 60))
        participant.eligible_minutes = min(elapsed, activity.duration_minutes)
        participant.ended_at = now
        participant.status = "completed"
        participant.completed_at = now
        activity.ended_at, activity.status = now, "completed"
        self.db.flush()
        point_tx = PointsService(self.db).award_activity_completion_reward(participant.id, commit=False)
        instance = self._instance(user_id, instance_id)
        instance.status, instance.completed_at, instance.reflection = "completed", now, reflection
        xp_awarded = self._award_xp(user_id, quest.xp_reward, "QUEST_REWARD", "quest", str(instance.id), f"quest:{instance.id}")
        instance.xp_claimed = True
        progress = self.get_progression(user_id)
        progress.completed_quests += 1
        self._update_streak(user_id, progress, now)
        self._ensure_missions(user_id, "daily")
        self._ensure_missions(user_id, "weekly")
        self._refresh_missions(user_id)
        unlocked = self._evaluate_achievements(user_id)
        self.db.commit()
        payload = self.progression_payload(user_id)
        return {"instance_id": instance.id, "already_completed": False, "xp_awarded": xp_awarded,
                "garden_points_awarded": point_tx.amount if point_tx else 0,
                "new_level": payload["level"], "xp_current": payload["xp_current"],
                "xp_to_next_level": payload["xp_to_next_level"], "unlocked_achievements": unlocked}

    def _instance(self, user_id, instance_id):
        item = self.db.query(UserQuestInstance).filter_by(id=instance_id, user_id=user_id).first()
        if not item:
            raise HTTPException(404, detail={"code": "QUEST_INSTANCE_NOT_FOUND", "message": "Quest instance not found."})
        return item

    def _award_xp(self, user_id, amount, tx_type, source_type, source_id, key) -> int:
        if amount <= 0 or self.db.query(XpTransaction).filter_by(idempotency_key=key).first():
            return 0
        progress = self.get_progression(user_id)
        before = progress.lifetime_xp
        progress.lifetime_xp += amount
        progress.xp_current += amount
        while progress.xp_current >= xp_required(progress.level):
            progress.xp_current -= xp_required(progress.level)
            progress.level += 1
        self.db.add(XpTransaction(
            user_id=user_id, amount=amount, transaction_type=tx_type,
            source_type=source_type, source_id=source_id,
            lifetime_before=before, lifetime_after=progress.lifetime_xp, idempotency_key=key,
        ))
        self.db.flush()
        return amount

    def _update_streak(self, user_id, progress, completed_at):
        today = self._local_date(user_id, completed_at)
        if progress.last_completion_date == today:
            return
        progress.current_streak = progress.current_streak + 1 if progress.last_completion_date == today - timedelta(days=1) else 1
        progress.longest_streak = max(progress.longest_streak, progress.current_streak)
        progress.last_completion_date = today

    def _period(self, user_id, kind):
        tz = self._timezone(user_id)
        local_now = datetime.now(tz)
        start_date = local_now.date() if kind == "daily" else local_now.date() - timedelta(days=local_now.weekday())
        days = 1 if kind == "daily" else 7
        start = datetime.combine(start_date, time.min, tzinfo=tz).astimezone(timezone.utc)
        end = datetime.combine(start_date + timedelta(days=days), time.min, tzinfo=tz).astimezone(timezone.utc)
        return start_date.isoformat(), start, end

    def get_missions(self, user_id, kind):
        self.seed_catalog()
        self.get_progression(user_id)
        self._lock_user(user_id)
        self._ensure_missions(user_id, kind)
        self._refresh_missions(user_id, kind)
        self.db.commit()
        key, _, _ = self._period(user_id, kind)
        return self.db.query(UserMission).join(MissionDefinition).filter(
            UserMission.user_id == user_id, UserMission.period_key == key,
            MissionDefinition.mission_type == kind,
        ).all()

    def _ensure_missions(self, user_id, kind):
        key, start, end = self._period(user_id, kind)
        assigned = self.db.query(UserMission).join(MissionDefinition).filter(
            UserMission.user_id == user_id, UserMission.period_key == key,
            MissionDefinition.mission_type == kind,
        ).all()
        if not assigned:
            pool = self.db.query(MissionDefinition).filter_by(mission_type=kind, is_active=True).order_by(MissionDefinition.code).all()
            rows = self.db.query(UserMission).join(MissionDefinition).filter(
                UserMission.user_id == user_id, UserMission.period_key < key,
                MissionDefinition.mission_type == kind,
            ).order_by(UserMission.period_key, MissionDefinition.code).all()
            history_by_period = {}
            for row in rows:
                history_by_period.setdefault(row.period_key, []).append(row.mission.code)
            for mission in self._rotate(pool, list(history_by_period.values()), 3, f"{user_id}:{kind}:{key}"):
                self.db.add(UserMission(user_id=user_id, mission_id=mission.id, period_key=key, start_at=start, end_at=end))
            self.db.flush()

    def _refresh_missions(self, user_id, only_kind=None):
        for kind in ([only_kind] if only_kind else ["daily", "weekly"]):
            if not kind:
                continue
            key, start, end = self._period(user_id, kind)
            rows = self.db.query(UserMission).join(MissionDefinition).filter(
                UserMission.user_id == user_id, UserMission.period_key == key,
                MissionDefinition.mission_type == kind,
            ).all()
            completions = self.db.query(UserQuestInstance).join(Quest).filter(
                UserQuestInstance.user_id == user_id, UserQuestInstance.status == "completed",
                UserQuestInstance.completed_at >= start, UserQuestInstance.completed_at < end,
            ).all()
            for row in rows:
                metric, categories = row.mission.metric, (row.mission.category_filter or {}).get("categories")
                filtered = [i for i in completions if not categories or i.quest.category in categories]
                if metric in ("quest_count", "category_count"):
                    value = len(filtered)
                elif metric == "xp_earned":
                    value = sum(i.quest.xp_reward for i in completions)
                elif metric == "minutes":
                    activity_ids = [i.activity_id for i in completions]
                    value = sum(minutes for (minutes,) in self.db.query(ActivityParticipant.eligible_minutes).filter(
                        ActivityParticipant.user_id == user_id,
                        ActivityParticipant.activity_id.in_(activity_ids),
                    ).all())
                elif metric == "distinct_categories":
                    value = len({i.quest.category for i in completions})
                else:
                    value = len({self._local_date(user_id, i.completed_at) for i in completions})
                row.current_progress = min(value, row.mission.target_value)
                if row.current_progress >= row.mission.target_value and not row.reward_claimed:
                    row.status = "complete"
        self.db.flush()

    def claim_mission(self, user_id, assignment_id):
        self.get_progression(user_id)
        self._lock_user(user_id)
        row = self.db.query(UserMission).filter_by(id=assignment_id, user_id=user_id).first()
        if not row:
            raise HTTPException(404, detail={"code": "MISSION_NOT_FOUND", "message": "Mission not found."})
        self._refresh_missions(user_id, row.mission.mission_type)
        if row.current_progress < row.mission.target_value:
            raise HTTPException(409, detail={"code": "MISSION_INCOMPLETE", "message": "Mission is not complete yet."})
        if not row.reward_claimed:
            self._award_xp(user_id, row.mission.reward_xp, f"{row.mission.mission_type.upper()}_MISSION_REWARD", "mission", str(row.id), f"mission:{row.id}")
            row.reward_claimed, row.claimed_at, row.status = True, datetime.now(timezone.utc), "claimed"
            self.db.commit()
        return row

    def _achievement_progress(self, user_id, achievement):
        query = self.db.query(UserQuestInstance).join(Quest).filter(
            UserQuestInstance.user_id == user_id,
            UserQuestInstance.status == "completed",
        )
        if achievement.category_filter:
            query = query.filter(Quest.category == achievement.category_filter)
        return query.count()

    def _evaluate_achievements(self, user_id):
        unlocked = []
        for achievement in self.db.query(AchievementDefinition).all():
            exists = self.db.query(UserAchievement).filter_by(user_id=user_id, achievement_id=achievement.id).first()
            if not exists and self._achievement_progress(user_id, achievement) >= achievement.target_value:
                self.db.add(UserAchievement(user_id=user_id, achievement_id=achievement.id, claimed=True))
                self.db.flush()
                self._award_xp(user_id, achievement.reward_xp, "ACHIEVEMENT_REWARD", "achievement", achievement.code, f"achievement:{user_id}:{achievement.code}")
                unlocked.append(achievement.code)
        return unlocked

    def list_achievements(self, user_id):
        self.seed_catalog()
        result = []
        for item in self.db.query(AchievementDefinition).order_by(AchievementDefinition.code).all():
            unlocked = self.db.query(UserAchievement).filter_by(user_id=user_id, achievement_id=item.id).first()
            result.append({"code": item.code, "name": item.name, "description": item.description,
                           "current_progress": min(self._achievement_progress(user_id, item), item.target_value),
                           "target_value": item.target_value, "reward_xp": item.reward_xp,
                           "unlocked": unlocked is not None, "unlocked_at": unlocked.unlocked_at if unlocked else None})
        return result

    def history(self, user_id):
        return self.db.query(UserQuestInstance).filter_by(user_id=user_id).order_by(UserQuestInstance.started_at.desc()).all()

    def xp_history(self, user_id):
        return self.db.query(XpTransaction).filter_by(user_id=user_id).order_by(XpTransaction.created_at.desc()).all()
