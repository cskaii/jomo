import re
import json
from pathlib import Path
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.schemas.privacy import (
    ScreenTextRequest,
    ScreenTextResponse,
    DetectionItem,
    WellbeingRecommendationRequest,
    WellbeingRecommendationResponse,
    MissionRecommendationRequest,
    MissionItemResponse,
)
from app.models.screening import ScreeningEvent
from app.services.usage_service import UsageService
from app.ai.screening_service import get_screening_provider
from app.core.config import get_settings

# Singapore specific and standard PII regex patterns (Section 10)
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
SG_PHONE_PATTERN = re.compile(r"(?:\+65\s?)?[89]\d{3}[-\s]?\d{4}\b")
SG_NRIC_PATTERN = re.compile(r"\b[STFGMstfgm]\d{7}[A-Za-z]\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")


class PrivacyService:
    def __init__(self, db: Session):
        self.db = db

    def screen_text(self, user_id: UUID, data: ScreenTextRequest) -> ScreenTextResponse:
        text = data.text
        do_pii = "pii" in (data.checks or [])

        detections: List[DetectionItem] = []
        redacted = text
        has_pii = False

        if do_pii:
            # Prefer Presidio; fall back to deterministic regex recognisers when
            # Presidio is disabled or fails to initialise (blueprint §0.2).
            provider = get_screening_provider()
            if provider is not None:
                result = provider.screen(text, data.language)
                detections = [
                    DetectionItem(
                        entity_type=d["entity_type"],
                        start=d["start"],
                        end=d["end"],
                        score=d["score"],
                        category=d["category"],
                    )
                    for d in result["detections"]
                ]
                redacted = result["redacted_text"]
                has_pii = result["has_potential_pii"]
            else:
                detections, redacted = self._regex_pii_detections(text)
                has_pii = len(detections) > 0

        categories_found = {d.entity_type for d in detections}

        # Audit event record: Section 7.4 (No raw text stored)
        audit_event = ScreeningEvent(
            user_id=user_id,
            screening_type="pii",
            source="user_submitted",
            detected_categories=list(categories_found) if categories_found else None,
            result_status="completed",
        )
        self.db.add(audit_event)
        self.db.commit()

        limitations = [
            "Automated screening can miss sensitive information.",
            "A result with no detections does not guarantee that text is safe.",
        ]

        return ScreenTextResponse(
            status="completed",
            has_potential_pii=has_pii,
            has_harmful_content_indicators=False,
            detections=detections,
            redacted_text=redacted,
            limitations=limitations,
        )

    def _regex_pii_detections(self, text: str) -> tuple[List[DetectionItem], str]:
        """Deterministic regex fallback used when Presidio is unavailable."""
        detections: List[DetectionItem] = []

        for match in EMAIL_PATTERN.finditer(text):
            detections.append(
                DetectionItem(
                    entity_type="EMAIL_ADDRESS",
                    start=match.start(),
                    end=match.end(),
                    score=0.95,
                    category="pii",
                )
            )
        for match in SG_PHONE_PATTERN.finditer(text):
            detections.append(
                DetectionItem(
                    entity_type="SG_PHONE_NUMBER",
                    start=match.start(),
                    end=match.end(),
                    score=0.90,
                    category="pii",
                )
            )
        for match in SG_NRIC_PATTERN.finditer(text):
            detections.append(
                DetectionItem(
                    entity_type="SG_NRIC_FIN",
                    start=match.start(),
                    end=match.end(),
                    score=0.98,
                    category="pii",
                )
            )
        for match in CREDIT_CARD_PATTERN.finditer(text):
            detections.append(
                DetectionItem(
                    entity_type="CREDIT_CARD",
                    start=match.start(),
                    end=match.end(),
                    score=0.90,
                    category="pii",
                )
            )

        # Redact matches in reverse order so character offsets remain aligned
        redacted = text
        for item in sorted(detections, key=lambda d: d.start, reverse=True):
            redacted = redacted[: item.start] + "[REDACTED]" + redacted[item.end :]
        return detections, redacted

    def get_wellbeing_recommendation(
        self, user_id: UUID, data: WellbeingRecommendationRequest
    ) -> WellbeingRecommendationResponse:
        # Rule-based suggestions from aggregated usage data (Section 0.3 P0 & Section 12)
        usage_service = UsageService(self.db)
        summary = usage_service.get_summary(user_id)

        if summary.daily_average_minutes > 300:
            return WellbeingRecommendationResponse(
                headline="High Screen Time Alert",
                suggestion="You've spent an average of over 5 hours daily on screens this week. Consider planning a 30-minute offline outdoor stroll or reading session with friends.",
                category="outdoor",
                recommended_activity_category="outdoor",
            )
        elif summary.social_time_minutes > 180:
            return WellbeingRecommendationResponse(
                headline="Social Media Overload",
                suggestion="Social apps took up a significant portion of your time. Reconnecting in person over tea or games can give your mind a joyful reset.",
                category="social",
                recommended_activity_category="social",
            )
        else:
            return WellbeingRecommendationResponse(
                headline="Balanced & Mindful Rhythm",
                suggestion="You're keeping a healthy balance! Keep watering your virtual sanctuary by trying an offline creative activity today.",
                category="creative",
                recommended_activity_category="creative",
            )

    def recommend_missions(
        self, user_id: UUID, data: MissionRecommendationRequest
    ) -> List[MissionItemResponse]:
        if not get_settings().AUTO_SEED_CATALOG:
            return []
        fixture_path = Path(__file__).resolve().parents[4] / "shared" / "fixtures" / "demo_missions.json"
        missions_data = []
        if fixture_path.exists():
            with open(fixture_path, "r", encoding="utf-8") as f:
                missions_data = json.load(f)

        results = []
        for m in missions_data:
            if data.category and m.get("category") != data.category:
                continue
            if data.max_duration_minutes and m.get("duration_minutes", 0) > data.max_duration_minutes:
                continue
            results.append(
                MissionItemResponse(
                    id=m["id"],
                    title=m["title"],
                    description=m["description"],
                    category=m["category"],
                    duration_minutes=m["duration_minutes"],
                    proof_requirement=m["proof_requirement"],
                    max_reward_points=m["max_reward_points"],
                    tags=m.get("tags", []),
                )
            )
        return results
