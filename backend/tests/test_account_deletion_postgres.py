"""Optional real PostgreSQL integration tests in isolated, rolled-back schemas.

Set JOMO_TEST_POSTGRES_URL to a development PostgreSQL connection with CREATE
SCHEMA permission. Tests never read/delete accounts in public or auth schemas.
"""
import os
from pathlib import Path
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.db.base import Base
import app.models  # register metadata
from app.models.activity import Activity, ActivityParticipant
from app.models.garden import Garden, GardenCatalogItem, GardenItem
from app.models.group import Group, GroupMember
from app.models.points import PointTransaction
from app.models.user import User, UserPreference
from app.services.garden_service import GardenService


@pytest.fixture
def deletion_database():
    url = os.environ.get("JOMO_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set JOMO_TEST_POSTGRES_URL for isolated PostgreSQL trigger tests")
    engine = create_engine(url)
    with engine.connect() as connection:
        transaction = connection.begin()
        suffix = uuid.uuid4().hex
        schema, auth = f"jomo_test_{suffix}", f"jomo_test_auth_{suffix}"
        try:
            connection.exec_driver_sql(f'CREATE SCHEMA {schema}')
            connection.exec_driver_sql(f'CREATE SCHEMA {auth}')
            connection.exec_driver_sql(f'CREATE TABLE {auth}.users (id uuid PRIMARY KEY)')
            connection.execution_options(schema_translate_map={None: schema})
            Base.metadata.create_all(connection)
            script = (Path(__file__).resolve().parents[1] / "app/db/account_deletion.sql").read_text()
            script = script.replace("public.", f"{schema}.").replace("auth.users", f"{auth}.users")
            # Also verify setup is safe to rerun.
            connection.exec_driver_sql(script, execution_options={"no_parameters": True})
            connection.exec_driver_sql(script, execution_options={"no_parameters": True})
            with Session(connection, expire_on_commit=False) as db:
                yield db, connection, schema, auth
        finally:
            transaction.rollback()  # Removes only this test's schemas and data.
    engine.dispose()


def seed(database):
    db, connection, schema, auth = database
    owner, member, removed = [uuid.uuid4() for _ in range(3)]
    for user_id in (owner, member, removed):
        connection.execute(text(f'INSERT INTO {auth}.users(id) VALUES (:id)'), {"id": user_id})
        db.add(User(id=user_id, username=f"test_{user_id.hex[:12]}", display_name="Deletion test"))
    db.flush()
    group = Group(name="Keep our garden", created_by=owner)
    db.add(group)
    db.flush()
    db.add_all([
        GroupMember(group_id=group.id, user_id=owner, role="owner", status="active"),
        GroupMember(group_id=group.id, user_id=member, role="member", status="active"),
        GroupMember(group_id=group.id, user_id=removed, role="admin", status="removed"),
        UserPreference(user_id=owner), UserPreference(user_id=member),
    ])
    shared = Garden(name="Shared", garden_type="group", owner_group_id=group.id, points_balance=100)
    personal = Garden(name="Personal", garden_type="personal", owner_user_id=owner, points_balance=500)
    flower = GardenCatalogItem(name="Test plant", description="Test", item_type="seed", price_points=25, asset_key="test")
    activity = Activity(created_by=owner, group_id=group.id, title="Group walk", category="walk",
                        visibility="group", duration_minutes=10, proof_requirement="none")
    db.add_all([shared, personal, flower, activity])
    db.flush()
    participant = ActivityParticipant(activity_id=activity.id, user_id=owner)
    db.add(participant)
    db.flush()
    GardenService(db).purchase_item(owner, shared.id, flower.id)
    db.add(PointTransaction(garden_id=shared.id, user_id=owner, activity_participant_id=participant.id,
        transaction_type="earn", amount=10, reason="Private name", idempotency_key=f"earned:{owner}"))
    shared.points_balance += 10
    db.flush()
    return owner, member, removed, group.id, shared.id, personal.id, activity.id


def delete_auth(database, user_id):
    db, connection, schema, auth = database
    connection.execute(text(f'DELETE FROM {auth}.users WHERE id = :id'), {"id": user_id})
    db.expire_all()


def test_owner_deletion_preserves_shared_assets_and_transfers_ownership(deletion_database):
    db, connection, schema, auth = deletion_database
    owner, member, removed, group_id, shared_id, personal_id, activity_id = seed(deletion_database)
    delete_auth(deletion_database, owner)
    assert db.get(User, owner) is None
    assert db.get(UserPreference, owner) is None
    assert db.get(Garden, personal_id) is None
    assert db.get(Garden, shared_id).points_balance == 85
    assert db.query(GardenItem).filter_by(garden_id=shared_id).count() == 1
    assert db.get(Group, group_id).created_by == member
    assert db.get(GroupMember, (group_id, member)).role == "owner"
    assert db.get(GroupMember, (group_id, removed)).role == "admin"
    assert db.get(Activity, activity_id).created_by == member
    assert db.query(ActivityParticipant).filter_by(user_id=owner).count() == 0
    entries = db.query(PointTransaction).filter_by(garden_id=shared_id).all()
    assert len(entries) == 2
    assert all(entry.user_id is None and entry.activity_participant_id is None for entry in entries)
    assert all(str(owner) not in entry.idempotency_key and entry.reason == "Former member transaction" for entry in entries)
    # The identity foreign key rejects recreation from a request already in flight.
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(text(f"INSERT INTO {schema}.users(id,username,display_name,created_at,updated_at) "
                                "VALUES (:id,'stale','Stale',now(),now())"), {"id": owner})


def test_last_active_member_deletion_removes_group_and_shared_garden(deletion_database):
    db = deletion_database[0]
    owner, member, _, group_id, shared_id, _, activity_id = seed(deletion_database)
    db.get(GroupMember, (group_id, member)).status = "left"
    db.flush()
    delete_auth(deletion_database, owner)
    assert db.get(Group, group_id) is None
    assert db.get(Garden, shared_id) is None
    assert db.get(Activity, activity_id) is None
    assert db.get(User, member) is not None


def test_regular_member_deletion_keeps_owner_and_shared_balance(deletion_database):
    db = deletion_database[0]
    owner, member, _, group_id, shared_id, _, _ = seed(deletion_database)
    delete_auth(deletion_database, member)
    assert db.get(User, member) is None
    assert db.get(Group, group_id).created_by == owner
    assert db.get(Garden, shared_id).points_balance == 85


def test_auth_and_app_deletion_roll_back_together(deletion_database):
    db, connection, schema, auth = deletion_database
    owner, _, _, _, shared_id, _, _ = seed(deletion_database)
    with connection.begin_nested() as savepoint:
        delete_auth(deletion_database, owner)
        assert db.get(User, owner) is None
        savepoint.rollback()
    db.expire_all()
    assert db.get(User, owner) is not None
    assert db.get(Garden, shared_id).points_balance == 85
    assert connection.execute(text(f'SELECT count(*) FROM {auth}.users WHERE id=:id'), {"id": owner}).scalar_one() == 1
