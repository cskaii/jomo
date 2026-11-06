import uuid
from datetime import datetime, date, timezone
from typing import Optional, Any
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UsageSummary(Base):
    __tablename__ = "usage_summaries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    social_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category_breakdown: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", "source", name="uq_usage_summaries_user_date_source"),
    )
