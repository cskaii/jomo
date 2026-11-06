import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    garden_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("gardens.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    activity_participant_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("activity_participants.id"), nullable=True, index=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("transaction_type IN ('earn', 'spend', 'refund', 'adjustment')", name="check_transaction_type"),
        CheckConstraint("amount <> 0", name="check_transaction_amount_nonzero"),
        Index("idx_point_transactions_garden_date", "garden_id", "created_at"),
        Index("idx_point_transactions_user_date", "user_id", "created_at"),
    )
