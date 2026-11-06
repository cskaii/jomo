from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator
from app.core.config import get_settings


class DetectionItem(BaseModel):
    entity_type: str
    start: int
    end: int
    score: float
    category: str


class ScreenTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    checks: List[Literal["pii", "harmful_content"]] = Field(default_factory=lambda: ["pii", "harmful_content"], min_length=1, max_length=2)
    language: Literal["en"] = "en"

    @field_validator("text")
    @classmethod
    def configured_text_limit(cls, value):
        if len(value) > get_settings().SCREENING_MAX_TEXT_LENGTH:
            raise ValueError("Text exceeds the configured screening limit")
        return value


class ScreenTextResponse(BaseModel):
    status: str
    has_potential_pii: bool
    has_harmful_content_indicators: bool
    detections: List[DetectionItem] = Field(default_factory=list)
    redacted_text: str
    limitations: List[str] = Field(default_factory=list)
    engine: Literal["presidio", "none"] = "none"
    ner_enabled: bool = False


class WellbeingRecommendationRequest(BaseModel):
    target_date: Optional[str] = None


class WellbeingRecommendationResponse(BaseModel):
    headline: str
    suggestion: str
    category: str
    recommended_activity_category: Optional[str] = None


class MissionRecommendationRequest(BaseModel):
    category: Optional[str] = None
    max_duration_minutes: Optional[int] = None
    group_size: Optional[int] = None


class MissionItemResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    duration_minutes: int
    proof_requirement: str
    max_reward_points: int
    tags: List[str] = Field(default_factory=list)
