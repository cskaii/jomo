from datetime import datetime, timezone
from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, select
from app.db.base import Base
from app.models.user import User, UserPreference
from app.models.activity import ActivityParticipant
from app.models.proof import ProofSubmission
from app.models.location import ActivityCheckIn
from app.models.screening import ScreeningEvent
from app.models.consent import ConsentRecord
from app.services.retention_service import queue_photo, cleanup


class DataControlService:
    def __init__(self, db):
        self.db = db

    def export(self, user_id, email):
        cleanup(self.db, delete_objects=False)
        output = {"exported_at": datetime.now(timezone.utc), "account_email": email,
                  "scope": "Self-service account and participation records. Contact the privacy operator for formal access/disclosure-history requests."}
        # Export rows linked directly to this identity; never export token hashes,
        # signed URLs, internal retry queues or other members' private proof files.
        excluded = {"token_hash", "storage_key", "idempotency_key"}
        for name, table in Base.metadata.tables.items():
            columns = [column for column in table.columns if any(fk.target_fullname == "users.id" for fk in column.foreign_keys)]
            if name == "users":
                columns = [table.c.id]
            if name == "data_access_events":
                columns = [table.c.subject_user_id]
            if not columns:
                continue
            rows = self.db.execute(select(table).where(or_(*(column == user_id for column in columns)))).mappings()
            output[name] = [{key: value for key, value in row.items() if key not in excluded | ({"actor_user_id"} if name == "data_access_events" else set())} for row in rows]
        ids = self.db.query(ActivityParticipant.id).filter_by(user_id=user_id)
        for model, name in ((ProofSubmission, "proof_submissions"), (ActivityCheckIn, "location_check_ins")):
            rows = self.db.query(model).filter(model.participant_id.in_(ids)).all()
            output[name] = [{column.name: getattr(row, column.name) for column in model.__table__.columns
                             if column.name not in excluded | {"reviewed_by"}} for row in rows]
        # Personal inventory belongs to the user; shared inventory is collectively
        # owned and remains accessible through the garden interface instead.
        from app.models.garden import Garden, GardenItem
        gardens = self.db.query(Garden).filter_by(owner_user_id=user_id).all()
        output["personal_gardens"] = [{column.name: getattr(row, column.name) for column in Garden.__table__.columns} for row in gardens]
        items = self.db.query(GardenItem).filter(GardenItem.garden_id.in_([garden.id for garden in gardens])).all()
        output["personal_inventory"] = [{column.name: getattr(row, column.name) for column in GardenItem.__table__.columns} for row in items]
        return jsonable_encoder(output)

    def remove_photos(self, user_id):
        ids = self.db.query(ActivityParticipant.id).filter_by(user_id=user_id)
        for proof in self.db.query(ProofSubmission).filter(ProofSubmission.participant_id.in_(ids)).all():
            queue_photo(self.db, proof.storage_key)
            proof.storage_key = None
        self.db.add(ConsentRecord(user_id=user_id, purpose="activity_photo", policy_version="2026-11-07", granted=False))
        self.db.commit()

    def clear_screening(self, user_id):
        self.db.query(ScreeningEvent).filter_by(user_id=user_id).delete()
        self.db.commit()
