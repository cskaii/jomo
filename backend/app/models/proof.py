import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, BigInteger, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProofSubmission(Base):
    __tablename__ = "proof_submissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_participants.id", ondelete="CASCADE"), nullable=False, index=True)
    proof_type: Mapped[str] = mapped_column(String(30), nullable=False)
    storage_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    retention_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("proof_type IN ('photo', 'group_confirmation')", name="check_proof_type"),
        CheckConstraint("status IN ('pending', 'accepted', 'rejected')", name="check_proof_status"),
        Index("idx_proof_submissions_activity", "activity_id", "status"),
    )

    confirmations: Mapped[list["ProofConfirmation"]] = relationship("ProofConfirmation", back_populates="proof", cascade="all, delete-orphan")


class ProofConfirmation(Base):
    __tablename__ = "proof_confirmations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    proof_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proof_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    confirmed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("proof_id", "confirmed_by", name="uq_proof_confirmations_user"),
        CheckConstraint("decision IN ('confirm', 'reject')", name="check_confirmation_decision"),
    )

    proof: Mapped["ProofSubmission"] = relationship("ProofSubmission", back_populates="confirmations")
