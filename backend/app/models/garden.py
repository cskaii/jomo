import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GardenCatalogItem(Base):
    __tablename__ = "garden_catalog_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)
    price_points: Mapped[int] = mapped_column(Integer, nullable=False)
    asset_key: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Garden(Base):
    __tablename__ = "gardens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    garden_type: Mapped[str] = mapped_column(String(20), nullable=False)
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    owner_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    growth_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("points_balance >= 0", name="check_garden_points_balance_positive"),
        CheckConstraint("growth_level >= 1", name="check_garden_growth_level_positive"),
        CheckConstraint(
            "(garden_type = 'personal' AND owner_user_id IS NOT NULL AND owner_group_id IS NULL) OR "
            "(garden_type = 'group' AND owner_user_id IS NULL AND owner_group_id IS NOT NULL)",
            name="check_garden_owner_validity",
        ),
    )

    items: Mapped[list["GardenItem"]] = relationship("GardenItem", back_populates="garden", cascade="all, delete-orphan")


class GardenItem(Base):
    __tablename__ = "garden_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    garden_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("gardens.id", ondelete="CASCADE"), nullable=False, index=True)
    catalog_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("garden_catalog_items.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    position_x: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    position_y: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    placed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    garden: Mapped["Garden"] = relationship("Garden", back_populates="items")
    catalog_item: Mapped["GardenCatalogItem"] = relationship("GardenCatalogItem")
