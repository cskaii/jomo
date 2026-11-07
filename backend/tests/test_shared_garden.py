"""Garden collaboration tests use a disposable in-memory database only."""
import unittest
import uuid

from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.garden import Garden, GardenCatalogItem, GardenItem
from app.models.points import PointTransaction
from app.models.activity import Activity, ActivityParticipant
from app.services.garden_service import GardenService
from app.services.points_service import PointsService


class SharedGardenTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        event.listen(self.engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.owner, self.member, self.outsider, self.removed = [uuid.uuid4() for _ in range(4)]
        for user_id in (self.owner, self.member, self.outsider, self.removed):
            self.db.add(User(id=user_id, username=str(user_id), display_name="Garden test user"))
        self.db.flush()
        self.group = Group(name="Our garden", created_by=self.owner)
        self.db.add(self.group)
        self.db.flush()
        self.db.add_all([
            GroupMember(group_id=self.group.id, user_id=self.owner, role="owner", status="active"),
            GroupMember(group_id=self.group.id, user_id=self.member, role="member", status="active"),
            GroupMember(group_id=self.group.id, user_id=self.removed, role="member", status="removed"),
        ])
        self.shared = Garden(name="Shared", garden_type="group", owner_group_id=self.group.id, points_balance=100)
        self.personal = Garden(name="Personal", garden_type="personal", owner_user_id=self.member, points_balance=1000)
        self.flower = GardenCatalogItem(name="Daisy", description="A flower", item_type="seed", price_points=25, asset_key="plant_daisy")
        self.db.add_all([self.shared, self.personal, self.flower])
        self.db.commit()
        self.service = GardenService(self.db)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_ordinary_member_spends_only_group_points_and_owner_can_plant(self):
        self.service.purchase_item(self.member, self.shared.id, self.flower.id)
        items = self.service.get_inventory(self.owner, self.shared.id)
        self.assertEqual(len(items), 1)
        self.service.place_item(self.owner, self.shared.id, items[0].id, 40, 60)
        self.assertEqual(self.shared.points_balance, 75)
        self.assertEqual(self.personal.points_balance, 1000)
        self.assertEqual(self.service.get_inventory(self.member, self.shared.id)[0].position_x, 40)
        spend = self.db.query(PointTransaction).one()
        self.assertEqual(spend.user_id, self.member)
        self.assertEqual(spend.garden_id, self.shared.id)
        self.assertEqual(spend.amount, -25)

    def test_outsider_and_removed_member_cannot_read_spend_or_move(self):
        self.service.purchase_item(self.owner, self.shared.id, self.flower.id)
        item = self.service.get_inventory(self.owner, self.shared.id)[0]
        for actor in (self.outsider, self.removed):
            for operation in (
                lambda: self.service.get_inventory(actor, self.shared.id),
                lambda: self.service.purchase_item(actor, self.shared.id, self.flower.id),
                lambda: self.service.place_item(actor, self.shared.id, item.id, 20, 30),
            ):
                with self.assertRaises(HTTPException) as error:
                    operation()
                self.assertEqual(error.exception.status_code, 403)
                self.db.rollback()
        self.assertEqual(self.shared.points_balance, 75)

    def test_each_purchased_unit_can_be_planted_and_new_purchase_stays_unplaced(self):
        self.service.purchase_item(self.member, self.shared.id, self.flower.id, 2)
        first = self.service.get_inventory(self.owner, self.shared.id)[0]
        self.service.place_item(self.owner, self.shared.id, first.id, 30, 50)
        remaining = next(item for item in self.service.get_inventory(self.member, self.shared.id) if item.position_x is None)
        self.service.place_item(self.member, self.shared.id, remaining.id, 60, 70)
        self.service.purchase_item(self.owner, self.shared.id, self.flower.id)
        items = self.service.get_inventory(self.member, self.shared.id)
        self.assertEqual(sum(item.quantity for item in items), 3)
        self.assertEqual(len([item for item in items if item.position_x is not None]), 2)
        self.assertEqual(len([item for item in items if item.position_x is None]), 1)

    def test_moving_personal_or_shared_plants_costs_nothing_and_keeps_inventory(self):
        for garden in (self.personal, self.shared):
            self.service.purchase_item(self.member, garden.id, self.flower.id)
            item = self.service.get_inventory(self.member, garden.id)[0]
            self.service.place_item(self.member, garden.id, item.id, 30, 50)
            balance = garden.points_balance
            transactions = self.db.query(PointTransaction).count()
            self.service.place_item(self.member, garden.id, item.id, 70, 80)
            self.assertEqual(garden.points_balance, balance)
            self.assertEqual(self.db.query(PointTransaction).count(), transactions)
            self.assertEqual(len(self.service.get_inventory(self.member, garden.id)), 1)
            self.assertEqual(item.position_x, 70)
            self.assertEqual(item.position_y, 80)

    def test_personal_inventory_cannot_be_moved_into_the_group_garden(self):
        self.service.purchase_item(self.member, self.personal.id, self.flower.id)
        item = self.service.get_inventory(self.member, self.personal.id)[0]
        with self.assertRaises(HTTPException) as error:
            self.service.place_item(self.member, self.shared.id, item.id, 30, 50)
        self.assertEqual(error.exception.status_code, 404)
        self.assertIsNone(item.position_x)

    def test_insufficient_group_points_do_not_spend_personal_points(self):
        with self.assertRaises(HTTPException) as error:
            self.service.purchase_item(self.member, self.shared.id, self.flower.id, 5)
        self.assertEqual(error.exception.detail["code"], "INSUFFICIENT_POINTS")
        self.assertEqual(self.shared.points_balance, 100)
        self.assertEqual(self.personal.points_balance, 1000)
        self.assertEqual(self.db.query(PointTransaction).count(), 0)
        self.assertEqual(self.db.query(GardenItem).count(), 0)

    def test_group_rewards_credit_shared_balance_and_remain_idempotent(self):
        activity = Activity(created_by=self.owner, group_id=self.group.id, title="Group walk", category="walk",
                            visibility="group", duration_minutes=10, proof_requirement="none", max_reward_points=60)
        self.db.add(activity)
        self.db.flush()
        participant = ActivityParticipant(activity_id=activity.id, user_id=self.member, status="completed", eligible_minutes=10)
        self.db.add(participant)
        self.db.commit()
        rewards = PointsService(self.db)
        first = rewards.award_activity_completion_reward(participant.id)
        again = rewards.award_activity_completion_reward(participant.id)
        self.assertEqual(first.id, again.id)
        self.assertEqual(self.shared.points_balance, 110)
        self.assertEqual(self.personal.points_balance, 1000)
        self.assertEqual(self.db.query(PointTransaction).count(), 1)


if __name__ == "__main__":
    unittest.main()
