import json
from pathlib import Path
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

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
from app.ai.screening_service import get_screening_provider, DEFAULT_LIMITATIONS
from app.core.logging import logger
from app.core.config import get_settings

class PrivacyService:
    def __init__(self, db: Session):
        self.db = db

    def screen_text(self, user_id: UUID, data: ScreenTextRequest) -> ScreenTextResponse:
        if not data.consent:
            raise HTTPException(400, detail={"code": "SCREENING_CONSENT_REQUIRED", "message": "Agree to submit this text before screening."})
        text = data.text
        do_pii = "pii" in (data.checks or [])

        detections: List[DetectionItem] = []
        redacted = text
        has_pii = False
        engine = "none"
        ner_enabled = False
        limitations = list(DEFAULT_LIMITATIONS)

        if do_pii:
            provider = get_screening_provider()
            if provider is None:
                raise HTTPException(503, detail={
                    "code": "SCREENING_UNAVAILABLE",
                    "message": "Microsoft Presidio is unavailable. Please try again later.",
                })
            try:
                result = provider.screen(text, data.language)
            except Exception as exc:
                # Detector errors can contain submitted text; never log their message.
                logger.warning("Presidio scan failed (%s).", type(exc).__name__)
                raise HTTPException(503, detail={
                    "code": "SCREENING_UNAVAILABLE",
                    "message": "Microsoft Presidio could not complete this scan. Please retry.",
                }) from None
            engine = "presidio"
            ner_enabled = bool(result.get("ner_enabled", False))
            limitations = result["limitations"]
            detections = [DetectionItem(**d) for d in result["detections"]]
            redacted = result["redacted_text"]
            has_pii = result["has_potential_pii"]

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
        from app.models.consent import ConsentRecord
        self.db.add(ConsentRecord(user_id=user_id, purpose="text_screening", policy_version="2026-11-07", granted=True))
        self.db.commit()

        return ScreenTextResponse(
            status="completed",
            has_potential_pii=has_pii,
            has_harmful_content_indicators=False,
            detections=detections,
            redacted_text=redacted,
            limitations=limitations,
            engine=engine,
            ner_enabled=ner_enabled,
        )

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
