import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.usage import UsageSummary
from app.schemas.usage import UsageRecordCreate, UsageSummaryResponse


class UsageService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(
        self,
        user_id: uuid.UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> UsageSummaryResponse:
        today = date.today()
        start = from_date or (today - timedelta(days=6))
        end = to_date or today

        records = (
            self.db.query(UsageSummary)
            .filter(
                UsageSummary.user_id == user_id,
                UsageSummary.usage_date >= start,
                UsageSummary.usage_date <= end,
            )
            .order_by(UsageSummary.usage_date.asc())
            .all()
        )

        total_min = sum(r.total_minutes for r in records)
        social_min = sum(r.social_minutes or 0 for r in records)
        days = len(records)
        avg_min = int(total_min / days) if days > 0 else 0

        return UsageSummaryResponse(
            total_screen_time_minutes=total_min,
            daily_average_minutes=avg_min,
            social_time_minutes=social_min,
            start_date=start,
            end_date=end,
            days_recorded=days,
            daily_breakdown=records,
        )

    def get_daily_records(
        self,
        user_id: uuid.UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[UsageSummary]:
        today = date.today()
        start = from_date or (today - timedelta(days=14))
        end = to_date or today

        return (
            self.db.query(UsageSummary)
            .filter(
                UsageSummary.user_id == user_id,
                UsageSummary.usage_date >= start,
                UsageSummary.usage_date <= end,
            )
            .order_by(UsageSummary.usage_date.desc())
            .all()
        )

    def get_category_breakdown(
        self,
        user_id: uuid.UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Dict[str, int]:
        records = self.get_daily_records(user_id, from_date, to_date)
        totals: Dict[str, int] = {}
        for r in records:
            if r.category_breakdown and isinstance(r.category_breakdown, dict):
                for cat, mins in r.category_breakdown.items():
                    totals[cat] = totals.get(cat, 0) + int(mins)
        return totals

    def record_usage(self, user_id: uuid.UUID, data: UsageRecordCreate) -> UsageSummary:
        existing = (
            self.db.query(UsageSummary)
            .filter(
                UsageSummary.user_id == user_id,
                UsageSummary.usage_date == data.usage_date,
                UsageSummary.source == data.source.value,
            )
            .first()
        )
        if existing:
            existing.total_minutes = data.total_minutes
            existing.social_minutes = data.social_minutes
            existing.category_breakdown = data.category_breakdown
            existing.updated_at = datetime.now(timezone.utc)
            record = existing
        else:
            record = UsageSummary(
                user_id=user_id,
                usage_date=data.usage_date,
                total_minutes=data.total_minutes,
                social_minutes=data.social_minutes,
                category_breakdown=data.category_breakdown,
                source=data.source.value,
            )
            self.db.add(record)

        self.db.commit()
        self.db.refresh(record)
        return record

    def import_records(self, user_id: uuid.UUID, records: List[UsageRecordCreate]) -> None:
        for r in records:
            self.record_usage(user_id, r)
