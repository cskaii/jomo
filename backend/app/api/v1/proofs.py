from uuid import UUID
from fastapi import APIRouter, Request, status
from app.api.dependencies import CurrentUser, DbSession
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.schemas.proof import (
    UploadUrlRequest,
    UploadUrlResponse,
    ProofRegisterRequest,
    ProofResponse,
    ProofConfirmRequest,
)
from app.services.proof_service import ProofService
from app.utils.response import wrap_response

router = APIRouter(tags=["Proofs"])


@router.post("/activities/{activity_id}/proofs/upload-url", response_model=ResponseEnvelope[UploadUrlResponse])
async def get_proof_upload_url(
    request: Request,
    activity_id: UUID,
    payload: UploadUrlRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ProofService(db)
    result = service.generate_upload_url(current_user.id, activity_id, payload)
    return wrap_response(result, request)


@router.post("/activities/{activity_id}/proofs", response_model=ResponseEnvelope[ProofResponse], status_code=status.HTTP_201_CREATED)
async def register_proof(
    request: Request,
    activity_id: UUID,
    payload: ProofRegisterRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ProofService(db)
    result = service.register_proof(current_user.id, activity_id, payload)
    return wrap_response(result, request)


@router.get("/activities/{activity_id}/proofs/me", response_model=ResponseEnvelope[ProofResponse])
async def get_my_proof(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ProofService(db)
    result = service.get_my_proof(current_user.id, activity_id)
    return wrap_response(result, request)


@router.post("/proofs/{proof_id}/confirm", response_model=ResponseEnvelope[SuccessStatus])
async def confirm_proof(
    request: Request,
    proof_id: UUID,
    payload: ProofConfirmRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ProofService(db)
    service.confirm_proof(current_user.id, proof_id, payload)
    return wrap_response(SuccessStatus(success=True, message="Confirmation submitted"), request)


@router.delete("/proofs/{proof_id}", response_model=ResponseEnvelope[SuccessStatus])
async def delete_proof(
    request: Request,
    proof_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ProofService(db)
    service.delete_proof(current_user.id, proof_id)
    return wrap_response(SuccessStatus(success=True, message="Proof removed"), request)
