from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from app.core.enums import GardenType, GardenItemType, PointTransactionType


class GardenCatalogItemResponse(BaseModel):
    id: UUID
    name: str
    description: str
    item_type: GardenItemType
    price_points: int
    asset_key: str
    is_active: bool

    model_config = {"from_attributes": True}


class GardenResponse(BaseModel):
    id: UUID
    garden_type: GardenType
    owner_user_id: Optional[UUID] = None
    owner_group_id: Optional[UUID] = None
    name: str
    points_balance: int
    growth_level: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GardenItemResponse(BaseModel):
    id: UUID
    garden_id: UUID
    catalog_item_id: UUID
    catalog_item: Optional[GardenCatalogItemResponse] = None
    quantity: int
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    placed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GardenPurchaseRequest(BaseModel):
    catalog_item_id: UUID
    quantity: int = Field(default=1, ge=1, le=10)


class GardenPlaceItemRequest(BaseModel):
    position_x: float = Field(ge=0, le=100, allow_inf_nan=False)
    position_y: float = Field(ge=0, le=100, allow_inf_nan=False)


class PointTransactionResponse(BaseModel):
    id: UUID
    garden_id: UUID
    user_id: Optional[UUID] = None
    activity_participant_id: Optional[UUID] = None
    transaction_type: PointTransactionType
    amount: int
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}

