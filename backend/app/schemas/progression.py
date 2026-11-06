from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProgressionResponse(BaseModel):
    user_id: UUID
    level: int
    xp_current: int
    xp_to_next_level: int
    lifetime_xp: int
    completed_quests: int
    current_streak: int
    longest_streak: int
    garden_points: int
    achievements_unlocked: int


class QuestResponse(BaseModel):
    id: UUID
    code: str
    title: str
    description: str
    instructions: str
    category: str
    category_label: str
    difficulty: str
    estimated_duration_minutes: int
    xp_reward: int
    repeatability: str
    proof_requirement: str
    reflection_prompt: Optional[str] = None
    is_favorite: bool = False
    active_instance_id: Optional[UUID] = None
    completion_count: int = 0


class QuestInstanceResponse(BaseModel):
    id: UUID
    quest: QuestResponse
    activity_id: UUID
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    abandoned_at: Optional[datetime] = None
    reflection: Optional[str] = None
    xp_claimed: bool


class QuestCompleteRequest(BaseModel):
    reflection: Optional[str] = Field(default=None, max_length=1000)


class QuestCompletionResponse(BaseModel):
    instance_id: UUID
    already_completed: bool
    xp_awarded: int
    garden_points_awarded: int
    new_level: int
    xp_current: int
    xp_to_next_level: int
    unlocked_achievements: list[str]


class MissionResponse(BaseModel):
    id: UUID
    code: str
    title: str
    description: str
    mission_type: str
    current_progress: int
    target_value: int
    reward_xp: int
    status: str
    reward_claimed: bool
    start_at: datetime
    end_at: datetime


class AchievementResponse(BaseModel):
    code: str
    name: str
    description: str
    current_progress: int
    target_value: int
    reward_xp: int
    unlocked: bool
    unlocked_at: Optional[datetime] = None


class XpTransactionResponse(BaseModel):
    id: UUID
    amount: int
    transaction_type: str
    source_type: str
    source_id: str
    lifetime_before: int
    lifetime_after: int
    created_at: datetime

    model_config = {"from_attributes": True}
