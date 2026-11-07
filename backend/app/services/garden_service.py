import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.garden import Garden, GardenCatalogItem, GardenItem
from app.models.points import PointTransaction
from app.models.group import GroupMember
from app.models.user import User
from app.core.config import get_settings


class GardenService:
    def __init__(self, db: Session):
        self.db = db

    def check_garden_access(self, user_id: uuid.UUID, garden_id: uuid.UUID, *, for_update: bool = False) -> Garden:
        query = self.db.query(Garden).filter(Garden.id == garden_id)
        if for_update:
            # Serialize purchases/planting against this garden's shared balance and inventory.
            query = query.populate_existing().with_for_update()
        garden = query.first()
        if not garden:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "GARDEN_NOT_FOUND", "message": "Garden not found."},
            )

        if garden.garden_type == "personal":
            if garden.owner_user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "NOT_GARDEN_OWNER", "message": "You do not own this personal garden."},
                )
        elif garden.garden_type == "group":
            member = (
                self.db.query(GroupMember)
                .filter(
                    GroupMember.group_id == garden.owner_group_id,
                    GroupMember.user_id == user_id,
                    GroupMember.status == "active",
                )
                .first()
            )
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "NOT_GROUP_MEMBER", "message": "You are not a member of this group garden."},
                )
        return garden

    def list_gardens(self, user_id: uuid.UUID) -> List[Garden]:
        # Personal garden
        personal_gardens = (
            self.db.query(Garden)
            .filter(Garden.garden_type == "personal", Garden.owner_user_id == user_id)
            .all()
        )
        if not personal_gardens:
            # Auto create personal garden if missing
            new_garden = Garden(
                garden_type="personal",
                owner_user_id=user_id,
                name="My Sanctuary",
                points_balance=0,
                growth_level=1,
            )
            self.db.add(new_garden)
            self.db.commit()
            personal_gardens = [new_garden]

        # Group gardens
        user_group_ids = [
            m.group_id
            for m in self.db.query(GroupMember)
            .filter(GroupMember.user_id == user_id, GroupMember.status == "active")
            .all()
        ]
        group_gardens = (
            self.db.query(Garden)
            .filter(Garden.garden_type == "group", Garden.owner_group_id.in_(user_group_ids))
            .all()
            if user_group_ids
            else []
        )
        return personal_gardens + group_gardens

    def get_garden(self, user_id: uuid.UUID, garden_id: uuid.UUID) -> Garden:
        return self.check_garden_access(user_id, garden_id)

    def get_inventory(self, user_id: uuid.UUID, garden_id: uuid.UUID) -> List[GardenItem]:
        self.check_garden_access(user_id, garden_id)
        return (
            self.db.query(GardenItem)
            .filter(GardenItem.garden_id == garden_id)
            .all()
        )

    def get_ledger(self, user_id: uuid.UUID, garden_id: uuid.UUID) -> List[PointTransaction]:
        self.check_garden_access(user_id, garden_id)
        return (
            self.db.query(PointTransaction)
            .filter(PointTransaction.garden_id == garden_id)
            .order_by(PointTransaction.created_at.desc())
            .all()
        )

    def list_catalog_items(self) -> List[GardenCatalogItem]:
        if get_settings().AUTO_SEED_CATALOG:
            self._seed_default_catalog_items()
        items = (
            self.db.query(GardenCatalogItem)
            .filter(GardenCatalogItem.is_active.is_(True))
            .all()
        )
        return items

    def _seed_default_catalog_items(self) -> None:
        catalog = [
            ("Sunflower", "A bright golden flower for a sunny corner.", "seed", 25, "plant_sunflower"),
            ("Daisy", "A cheerful white garden daisy.", "seed", 25, "plant_daisy"),
            ("Orchid", "A delicate purple orchid in full bloom.", "plant", 45, "plant_orchid"),
            ("Red Rose", "A classic red rose bush.", "seed", 35, "plant_red_rose"),
            ("Pink Rose", "A soft pink rose bush.", "seed", 35, "plant_pink_rose"),
            ("Purple Rose", "A dreamy purple rose bush.", "seed", 40, "plant_purple_rose"),
            ("Golden Rose", "A rare rose with golden petals.", "plant", 60, "plant_gold_rose"),
            ("Red Tulip", "A bold red spring tulip.", "seed", 30, "plant_red_tulip"),
            ("Pink Tulip", "A warm pink spring tulip.", "seed", 30, "plant_pink_tulip"),
            ("Purple Tulip", "A violet tulip for a calm patch.", "seed", 35, "plant_purple_tulip"),
            ("Golden Tulip", "A rare golden tulip.", "plant", 55, "plant_gold_tulip"),
            ("Apple Tree", "A full apple tree that anchors the garden.", "plant", 110, "tree_apple"),
            ("Coconut Tree", "A tropical coconut tree for the island edge.", "plant", 120, "tree_coconut"),
            ("Blue Bird", "A tiny blue garden visitor.", "pet", 75, "pet_bird"),
            ("Garden Cat", "A friendly cat who enjoys the warm grass.", "pet", 100, "pet_calico_cat"),
            ("Chicken", "A curious chicken for your garden flock.", "pet", 85, "pet_chicken"),
            ("Puppy", "A playful puppy to keep you company.", "pet", 110, "pet_dog"),
            ("Duck", "A bright little duck for the waterside.", "pet", 90, "pet_duck"),
            ("Goldfish", "A lively orange fish for the pond.", "pet", 70, "pet_fish"),
            ("Leafy Bush", "A round green bush for filling quiet corners.", "decoration", 30, "decor_bush"),
            ("Mossy Log", "A fallen log with a little moss.", "decoration", 35, "decor_log"),
            ("Purple Mushroom", "A whimsical purple mushroom.", "decoration", 25, "decor_mushroom"),
            ("Garden Rock", "A smooth stone for a natural border.", "decoration", 20, "decor_rock"),
            ("Grass Tuft", "A small tuft of wild grass.", "decoration", 15, "decor_grass_tuft"),
            ("Wooden Bridge", "A broad wooden bridge for crossing water.", "decoration", 90, "decor_bridge"),
            ("Wooden Fence", "A low fence section for shaping your patch.", "decoration", 30, "decor_fence"),
            ("Flower Gate", "A welcoming wooden garden gate.", "decoration", 55, "decor_gate"),
            ("Cozy Cottage", "A warm cottage with a terracotta roof.", "decoration", 180, "decor_cottage"),
            ("Greenhouse", "A glass greenhouse for special plants.", "decoration", 160, "decor_greenhouse"),
            ("Garden Shed", "A tidy wooden shed for garden tools.", "decoration", 130, "decor_shed"),
        ]
        defaults = [
            GardenCatalogItem(
                name=name,
                description=description,
                item_type=item_type,
                price_points=price,
                asset_key=asset_key,
                is_active=True,
            )
            for name, description, item_type, price, asset_key in catalog
        ]
        existing_assets = {
            asset for (asset,) in self.db.query(GardenCatalogItem.asset_key).all()
        }
        for item in defaults:
            if item.asset_key not in existing_assets:
                self.db.add(item)
        self.db.query(GardenCatalogItem).filter(
            GardenCatalogItem.asset_key.in_(["plant_bonsai", "decor_bench", "decor_fountain"])
        ).update({"is_active": False}, synchronize_session=False)
        self.db.commit()

    def purchase_item(
        self,
        user_id: uuid.UUID,
        garden_id: uuid.UUID,
        catalog_item_id: uuid.UUID,
        quantity: int = 1,
    ) -> None:
        garden = self.check_garden_access(user_id, garden_id, for_update=True)
        catalog_item = (
            self.db.query(GardenCatalogItem)
            .filter(GardenCatalogItem.id == catalog_item_id, GardenCatalogItem.is_active.is_(True))
            .first()
        )
        if not catalog_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ITEM_NOT_FOUND", "message": "Shop item not found."},
            )

        total_cost = catalog_item.price_points * quantity
        if garden.points_balance < total_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INSUFFICIENT_POINTS",
                    "message": f"Requires {total_cost} points, but garden balance is {garden.points_balance}.",
                },
            )

        # Idempotency key for spend
        idempotency_key = f"purchase:{garden.id}:{catalog_item.id}:{uuid.uuid4()}"

        # Deduct balance & create negative point transaction
        garden.points_balance -= total_cost
        garden.updated_at = datetime.now(timezone.utc)

        tx = PointTransaction(
            garden_id=garden.id,
            user_id=user_id,
            activity_participant_id=None,
            transaction_type="spend",
            amount=-total_cost,
            reason=f"Purchased {quantity}x {catalog_item.name}",
            idempotency_key=idempotency_key,
        )
        self.db.add(tx)

        # Add or update inventory
        existing_item = (
            self.db.query(GardenItem)
            .filter(
                GardenItem.garden_id == garden.id,
                GardenItem.catalog_item_id == catalog_item.id,
                GardenItem.position_x.is_(None),
                GardenItem.position_y.is_(None),
            )
            .first()
        )
        if existing_item:
            existing_item.quantity += quantity
        else:
            garden_item = GardenItem(
                garden_id=garden.id,
                catalog_item_id=catalog_item.id,
                quantity=quantity,
            )
            self.db.add(garden_item)

        self.db.commit()

    def place_item(
        self,
        user_id: uuid.UUID,
        garden_id: uuid.UUID,
        item_id: uuid.UUID,
        position_x: float,
        position_y: float,
    ) -> None:
        self.check_garden_access(user_id, garden_id, for_update=True)
        item = (
            self.db.query(GardenItem)
            .filter(GardenItem.id == item_id, GardenItem.garden_id == garden_id)
            .populate_existing()
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ITEM_NOT_IN_INVENTORY", "message": "Item is not in garden inventory."},
            )

        # One click plants one unit, retaining any remaining units in the collection.
        if item.quantity > 1:
            self.db.add(GardenItem(
                garden_id=garden_id,
                catalog_item_id=item.catalog_item_id,
                quantity=item.quantity - 1,
            ))
            item.quantity = 1

        item.position_x = position_x
        item.position_y = position_y
        item.placed_at = datetime.now(timezone.utc)
        self.db.commit()
