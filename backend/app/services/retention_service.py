from datetime import datetime, timezone, timedelta
from app.models.location import ActivityCheckIn
from app.models.proof import ProofSubmission
from app.models.notification import Notification
from app.models.screening import ScreeningEvent
from app.models.retention import StorageDeletion, DataAccessEvent
from app.services.storage_service import StorageService
from app.core.config import get_settings
from app.utils.user_time import utc
from sqlalchemy import or_, and_


def queue_photo(db, key):
    if key and not db.get(StorageDeletion, key):
        db.add(StorageDeletion(storage_key=key))
        db.flush()


def cleanup(db, delete_objects=True):
    """Run periodically and before private-data reads. Product retention periods, not statutory deadlines."""
    now = datetime.now(timezone.utc)
    db.query(ActivityCheckIn).filter(or_(ActivityCheckIn.expires_at <= now,
        and_(ActivityCheckIn.expires_at.is_(None), ActivityCheckIn.created_at < now - timedelta(hours=24)))).delete(synchronize_session=False)
    proofs = db.query(ProofSubmission).filter(ProofSubmission.storage_key.is_not(None)).all()
    for proof in proofs:
        expiry = proof.retention_until or utc(proof.submitted_at) + timedelta(days=get_settings().PROOF_RETENTION_DAYS)
        if utc(expiry) <= now:
            queue_photo(db, proof.storage_key)
            proof.storage_key = None
    db.query(Notification).filter(Notification.created_at < now - timedelta(days=30)).delete(synchronize_session=False)
    db.query(ScreeningEvent).filter(ScreeningEvent.created_at < now - timedelta(days=30)).delete(synchronize_session=False)
    db.query(DataAccessEvent).filter(DataAccessEvent.occurred_at < now - timedelta(days=366)).delete(synchronize_session=False)
    db.commit()
    if delete_objects:
        for queued in db.query(StorageDeletion).order_by(StorageDeletion.created_at).limit(30).all():
            try:
                StorageService().delete(queued.storage_key)
            except Exception:
                # No exception bodies/keys are logged; retry on the next worker pass.
                queued.attempts += 1
                from app.core.logging import logger
                logger.warning("Private photo deletion retry pending; operator should monitor retention status.")
            else:
                db.delete(queued)
            db.commit()
