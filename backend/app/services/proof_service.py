import io
import uuid
import warnings
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

from app.models.proof import ProofSubmission, ProofConfirmation
from app.models.activity import ActivityParticipant
from app.models.group import GroupMember
from app.models.consent import ConsentRecord
from app.models.retention import DataAccessEvent
from app.services.activity_service import ActivityService
from app.services.points_service import PointsService
from app.services.notification_service import notify
from app.services.storage_service import StorageService
from app.services.retention_service import queue_photo
from app.core.config import get_settings
from app.utils.user_time import utc


class ProofService:
    def __init__(self, db):
        self.db = db

    def participant(self, actor, activity_id, *, for_update=True):
        activity = ActivityService(self.db).get_activity(actor, activity_id, for_update=for_update)
        query = self.db.query(ActivityParticipant).filter_by(activity_id=activity_id, user_id=actor).populate_existing()
        if for_update:
            query = query.with_for_update()
        participant = query.first()
        if not participant or participant.status == "left":
            raise HTTPException(403, detail={"code": "PARTICIPATION_REQUIRED", "message": "Join this activity before submitting evidence."})
        return activity, participant

    def ready(self, actor, activity_id):
        activity, participant = self.participant(actor, activity_id)
        if not participant.ended_at or participant.status not in ("awaiting_proof", "completed"):
            raise HTTPException(409, detail={"code": "INVALID_STATE", "message": "End the activity before submitting evidence."})
        existing = self.db.query(ProofSubmission).filter_by(participant_id=participant.id).order_by(ProofSubmission.submitted_at.desc()).first()
        if existing and existing.status in ("pending", "accepted"):
            raise HTTPException(409, detail={"code": "PROOF_EXISTS", "message": "Evidence has already been submitted. Review or remove it before resubmitting."})
        return activity, participant

    def generate_upload_url(self, actor, activity_id, data):
        self.participant(actor, activity_id)
        raise HTTPException(410, detail={"code": "UPLOAD_FLOW_CHANGED", "message": "Use the photo upload form. Photos are validated and metadata is removed by the backend."})

    def reviewers(self, activity_id, owner):
        return self.db.query(ActivityParticipant).join(GroupMember,
            (GroupMember.user_id == ActivityParticipant.user_id)).filter(
            ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id != owner,
            ActivityParticipant.status.in_(["active", "awaiting_proof", "completed"]),
            GroupMember.status == "active")

    def notify_reviewers(self, activity, participant, proof):
        if activity.group_id:
            for peer in self.reviewers(activity.id, participant.user_id).filter(GroupMember.group_id == activity.group_id).all():
                notify(self.db, peer.user_id, "proof_review", "Activity evidence needs review", "A group participant submitted evidence for review.",
                       f"/activities/{activity.id}", proof_id=proof.id, activity_id=activity.id)

    def settle_activity(self, activity):
        self.db.flush()
        outstanding = self.db.query(ActivityParticipant.id).filter(
            ActivityParticipant.activity_id == activity.id,
            ActivityParticipant.status.notin_(["completed", "left"])).first()
        if not outstanding:
            activity.status = "completed"

    @staticmethod
    def sanitise_photo(content, mime):
        if mime not in ("image/jpeg", "image/png", "image/webp") or not content or len(content) > 2 * 1024 * 1024:
            raise HTTPException(400, detail={"code": "INVALID_PHOTO", "message": "Choose a JPEG, PNG or WebP photo up to 2 MB."})
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                return ProofService._reencode(content, mime)
        except (UnidentifiedImageError, OSError, ValueError, Warning, Image.DecompressionBombError):
            raise HTTPException(400, detail={"code": "INVALID_PHOTO", "message": "This photo cannot be processed safely. Use a smaller valid image, up to 8 megapixels."}) from None

    @staticmethod
    def _reencode(content, mime):
        with Image.open(io.BytesIO(content)) as source:
            expected = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}[mime]
            if source.format != expected or source.width * source.height > 8_000_000:
                raise ValueError()
            image = ImageOps.exif_transpose(source).convert("RGB")
            output = io.BytesIO()
            # Re-encoding discards EXIF/GPS, comments, filenames and metadata.
            image.save(output, format="JPEG", quality=85)
            clean = output.getvalue()
            if len(clean) > 2 * 1024 * 1024:
                raise ValueError()
            return clean

    def upload_photo(self, actor, activity_id, content, mime, consent):
        from app.utils.privacy_setup import require_optional_data_setup
        require_optional_data_setup()
        if not consent:
            raise HTTPException(400, detail={"code": "CONSENT_REQUIRED", "message": "Read the photo notice and agree before uploading."})
        activity, participant = self.ready(actor, activity_id)
        if activity.proof_requirement not in ("photo", "photo_or_group_confirmation", "none"):
            raise HTTPException(400, detail={"code": "INVALID_PROOF_TYPE", "message": "This activity uses group confirmation instead of a photo."})
        clean = self.sanitise_photo(content, mime)
        key = f"proofs/{uuid.uuid4().hex}.jpg"
        storage = StorageService()
        bucket = storage.call("GET", f"bucket/{storage.settings.STORAGE_BUCKET}").json()
        if bucket.get("public") is not False:
            raise HTTPException(503, detail={"code": "STORAGE_UNAVAILABLE", "message": "The evidence bucket must be private."})
        try:
            # A provider timeout may happen after it stored the object. Queue the
            # opaque key on any failure so uncertain uploads are also removed.
            storage.upload(key, clean, "image/jpeg")
            proof = ProofSubmission(activity_id=activity_id, participant_id=participant.id,
                proof_type="photo", storage_key=key, mime_type="image/jpeg", file_size_bytes=len(clean),
                status="pending" if activity.group_id else "accepted",
                retention_until=datetime.now(timezone.utc) + timedelta(days=get_settings().PROOF_RETENTION_DAYS))
            self.db.add(proof)
            self.db.add(ConsentRecord(user_id=actor, purpose="activity_photo", policy_version="2026-11-07", granted=True))
            self.db.flush()
            self.db.add(DataAccessEvent(subject_user_id=actor, actor_user_id=actor, purpose="private_photo_storage", resource_id=proof.id))
            if not activity.group_id:
                # Personal evidence is self-reported; elapsed participation, not
                # an automated photo authenticity claim, determines the reward.
                participant.status = "completed"
                participant.completed_at = participant.completed_at or datetime.now(timezone.utc)
                proof.reviewed_at = datetime.now(timezone.utc)
                self.db.flush()
                PointsService(self.db).award_activity_completion_reward(participant.id, commit=False)
                self.settle_activity(activity)
            self.notify_reviewers(activity, participant, proof)
            self.db.commit()
            self.db.refresh(proof)
            return proof
        except Exception:
            self.db.rollback()
            queue_photo(self.db, key)
            self.db.commit()
            raise

    def register_proof(self, actor, activity_id, data):
        activity, participant = self.ready(actor, activity_id)
        if data.proof_type.value != "group_confirmation" or data.storage_key or not activity.group_id or activity.proof_requirement not in ("group_confirmation", "photo_or_group_confirmation"):
            raise HTTPException(400, detail={"code": "INVALID_PROOF_TYPE", "message": "Use the photo upload form, or request group confirmation where supported."})
        proof = ProofSubmission(activity_id=activity_id, participant_id=participant.id, proof_type="group_confirmation", status="pending")
        self.db.add(proof)
        self.db.flush()
        self.notify_reviewers(activity, participant, proof)
        self.db.commit()
        self.db.refresh(proof)
        return proof

    def get_my_proof(self, actor, activity_id):
        _, participant = self.participant(actor, activity_id, for_update=False)
        proof = self.db.query(ProofSubmission).filter_by(participant_id=participant.id).order_by(ProofSubmission.submitted_at.desc()).first()
        if not proof:
            raise HTTPException(404, detail={"code": "PROOF_NOT_FOUND", "message": "No evidence submitted yet."})
        return proof

    def can_review(self, actor, proof):
        activity, peer = self.participant(actor, proof.activity_id)
        owner = self.db.get(ActivityParticipant, proof.participant_id)
        member = self.db.get(GroupMember, (activity.group_id, owner.user_id)) if activity.group_id and owner else None
        if not activity.group_id or not member or member.status != "active" or not owner or owner.user_id == actor or peer.status not in ("active", "awaiting_proof", "completed"):
            raise HTTPException(403, detail={"code": "PROOF_REVIEW_DENIED", "message": "Only another eligible active group participant can review this evidence."})
        return activity, owner

    def list_for_review(self, actor, activity_id):
        activity, peer = self.participant(actor, activity_id, for_update=False)
        if not activity.group_id or peer.status not in ("active", "awaiting_proof", "completed"):
            return []
        return self.db.query(ProofSubmission).join(ActivityParticipant, ProofSubmission.participant_id == ActivityParticipant.id).join(GroupMember,
            (GroupMember.user_id == ActivityParticipant.user_id) & (GroupMember.group_id == activity.group_id)).filter(
                ProofSubmission.activity_id == activity_id, ProofSubmission.status == "pending",
                ActivityParticipant.user_id != actor, GroupMember.status == "active").all()

    def preview(self, actor, proof_id):
        proof = self.db.get(ProofSubmission, proof_id)
        if not proof:
            raise HTTPException(404, detail={"code": "PROOF_NOT_FOUND", "message": "Evidence not found."})
        owner = self.db.get(ActivityParticipant, proof.participant_id)
        self.participant(actor, proof.activity_id)
        if owner.user_id != actor:
            self.can_review(actor, proof)
        expiry = proof.retention_until or utc(proof.submitted_at) + timedelta(days=get_settings().PROOF_RETENTION_DAYS)
        if not proof.storage_key or utc(expiry) <= datetime.now(timezone.utc):
            raise HTTPException(404, detail={"code": "PHOTO_EXPIRED", "message": "The photo is unavailable or its retention period has ended."})
        url = StorageService().signed_url(proof.storage_key)
        self.db.add(DataAccessEvent(subject_user_id=owner.user_id, actor_user_id=actor, purpose="private_photo_preview", resource_id=proof.id))
        self.db.commit()
        return {"url": url, "expires_in": 60}

    def confirm_proof(self, actor, proof_id, data):
        proof = self.db.query(ProofSubmission).filter_by(id=proof_id).populate_existing().with_for_update().first()
        if not proof:
            raise HTTPException(404, detail={"code": "PROOF_NOT_FOUND", "message": "Evidence not found."})
        activity, owner = self.can_review(actor, proof)
        if proof.status != "pending":
            raise HTTPException(409, detail={"code": "INVALID_STATE", "message": "Evidence has already been reviewed."})
        proof.status = "accepted" if data.decision == "confirm" else "rejected"
        proof.reviewed_at, proof.reviewed_by = datetime.now(timezone.utc), actor
        self.db.add(ProofConfirmation(proof_id=proof_id, confirmed_by=actor, decision=data.decision, comment=data.comment))
        if data.decision == "confirm":
            owner.status, owner.completed_at = "completed", datetime.now(timezone.utc)
            self.db.flush()
            PointsService(self.db).award_activity_completion_reward(owner.id, commit=False)
            self.settle_activity(activity)
        notify(self.db, owner.user_id, "proof_decision", "Activity evidence reviewed",
               "Your evidence was approved." if data.decision == "confirm" else "Your evidence was declined. You can submit another proof.",
               f"/activities/{activity.id}", proof_id=proof.id, activity_id=activity.id)
        self.db.commit()

    def delete_proof(self, actor, proof_id):
        proof = self.db.get(ProofSubmission, proof_id)
        if not proof:
            raise HTTPException(404, detail={"code": "PROOF_NOT_FOUND", "message": "Evidence not found."})
        owner = self.db.get(ActivityParticipant, proof.participant_id)
        if not owner or owner.user_id != actor:
            raise HTTPException(403, detail={"code": "PROOF_ACCESS_DENIED", "message": "You cannot delete another member's evidence."})
        queue_photo(self.db, proof.storage_key)
        if proof.proof_type == "photo":
            self.db.add(ConsentRecord(user_id=actor, purpose="activity_photo", policy_version="2026-11-07", granted=False))
        self.db.delete(proof)
        self.db.commit()
