import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.proof import ProofSubmission, ProofConfirmation
from app.models.activity import Activity, ActivityParticipant
from app.schemas.proof import UploadUrlRequest, UploadUrlResponse, ProofRegisterRequest, ProofConfirmRequest
from app.services.points_service import PointsService
from app.services.activity_service import ActivityService
from app.models.group import GroupMember
from app.core.enums import ProofType, ProofStatus, ParticipantStatus


class ProofService:
    def __init__(self, db: Session):
        self.db = db

    def generate_upload_url(
        self,
        user_id: uuid.UUID,
        activity_id: uuid.UUID,
        data: UploadUrlRequest,
    ) -> UploadUrlResponse:
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PARTICIPANT_NOT_FOUND", "message": "Participant not found."},
            )

        # Never issue a pretend signed URL or accept unverified photo evidence.
        # The backend/storage owner must supply real private storage integration.
        raise HTTPException(501, detail={"code": "STORAGE_NOT_CONFIGURED", "message": "Photo uploads are not available yet."})

    def register_proof(
        self,
        user_id: uuid.UUID,
        activity_id: uuid.UUID,
        data: ProofRegisterRequest,
    ) -> ProofSubmission:
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PARTICIPANT_NOT_FOUND", "message": "Participant not found."},
            )

        activity = ActivityService(self.db).get_activity(user_id, activity_id)
        if participant.status != ParticipantStatus.AWAITING_PROOF.value or not participant.ended_at:
            raise HTTPException(409, detail={"code": "INVALID_STATE", "message": "End participation before submitting proof."})
        if data.proof_type == ProofType.PHOTO:
            raise HTTPException(501, detail={"code": "STORAGE_NOT_CONFIGURED", "message": "Photo uploads are not available yet."})
        if not activity.group_id or activity.proof_requirement not in ("group_confirmation", "photo_or_group_confirmation"):
            raise HTTPException(422, detail={"code": "INVALID_PROOF_TYPE", "message": "Group confirmation is not allowed for this activity."})

        proof = ProofSubmission(
            activity_id=activity_id,
            participant_id=participant.id,
            proof_type=data.proof_type.value,
            storage_key=None,
            status=ProofStatus.PENDING.value,
            submitted_at=datetime.now(timezone.utc),
        )
        self.db.add(proof)

        self.db.commit()
        self.db.refresh(proof)
        return proof

    def get_my_proof(self, user_id: uuid.UUID, activity_id: uuid.UUID) -> ProofSubmission:
        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.activity_id == activity_id, ActivityParticipant.user_id == user_id)
            .first()
        )
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PARTICIPANT_NOT_FOUND", "message": "Participant not found."},
            )

        proof = (
            self.db.query(ProofSubmission)
            .filter(ProofSubmission.participant_id == participant.id)
            .order_by(ProofSubmission.submitted_at.desc())
            .first()
        )
        if not proof:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PROOF_NOT_FOUND", "message": "No proof registered."},
            )
        return proof

    def confirm_proof(
        self,
        confirmer_id: uuid.UUID,
        proof_id: uuid.UUID,
        data: ProofConfirmRequest,
    ) -> None:
        proof = self.db.query(ProofSubmission).filter(ProofSubmission.id == proof_id).first()
        if not proof:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PROOF_NOT_FOUND", "message": "Proof submission not found."},
            )

        participant = (
            self.db.query(ActivityParticipant)
            .filter(ActivityParticipant.id == proof.participant_id)
            .first()
        )
        # Cannot confirm self proof: Section 7.3 Table 13
        if participant and participant.user_id == confirmer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CANNOT_CONFIRM_SELF", "message": "You cannot confirm your own activity proof."},
            )

        activity = self.db.query(Activity).filter(Activity.id == proof.activity_id).first()
        member = self.db.query(GroupMember).filter(
            GroupMember.group_id == activity.group_id,
            GroupMember.user_id == confirmer_id,
            GroupMember.status == "active",
        ).first() if activity and activity.group_id else None
        peer = self.db.query(ActivityParticipant).filter(
            ActivityParticipant.activity_id == proof.activity_id,
            ActivityParticipant.user_id == confirmer_id,
            ActivityParticipant.status.in_(["active", "awaiting_proof", "completed"]),
        ).first()
        if not member or not peer:
            raise HTTPException(403, detail={"code": "PROOF_REVIEW_DENIED", "message": "Only eligible group participants can review this proof."})
        if proof.status != ProofStatus.PENDING.value:
            raise HTTPException(409, detail={"code": "INVALID_STATE", "message": "This proof has already been reviewed."})

        # Check existing confirmation
        existing = (
            self.db.query(ProofConfirmation)
            .filter(ProofConfirmation.proof_id == proof_id, ProofConfirmation.confirmed_by == confirmer_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ALREADY_CONFIRMED", "message": "You have already confirmed or reviewed this proof."},
            )

        confirmation = ProofConfirmation(
            proof_id=proof_id,
            confirmed_by=confirmer_id,
            decision=data.decision,
            comment=data.comment,
        )
        self.db.add(confirmation)

        if data.decision == "confirm":
            proof.status = ProofStatus.ACCEPTED.value
            proof.reviewed_at = datetime.now(timezone.utc)
            proof.reviewed_by = confirmer_id
            if participant:
                participant.status = ParticipantStatus.COMPLETED.value
                participant.completed_at = datetime.now(timezone.utc)
                self.db.flush()
                PointsService(self.db).award_activity_completion_reward(participant.id)
        else:
            proof.status = ProofStatus.REJECTED.value
            proof.reviewed_at = datetime.now(timezone.utc)
            proof.reviewed_by = confirmer_id

        self.db.commit()

    def delete_proof(self, user_id: uuid.UUID, proof_id: uuid.UUID) -> None:
        proof = self.db.query(ProofSubmission).filter(ProofSubmission.id == proof_id).first()
        if not proof:
            raise HTTPException(404, detail={"code": "PROOF_NOT_FOUND", "message": "Proof submission not found."})
        participant = self.db.query(ActivityParticipant).filter(
            ActivityParticipant.id == proof.participant_id,
            ActivityParticipant.user_id == user_id,
        ).first()
        if not participant:
            raise HTTPException(403, detail={"code": "PROOF_ACCESS_DENIED", "message": "You cannot delete this proof."})
        self.db.delete(proof)
        self.db.commit()

