from uuid import UUID
from fastapi import APIRouter, Request, status, Query, HTTPException
from starlette.concurrency import run_in_threadpool
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


@router.post("/activities/{activity_id}/proofs/photo", response_model=ResponseEnvelope[ProofResponse])
async def upload_photo(request: Request, activity_id: UUID, current_user: CurrentUser, db: DbSession, consent: bool = Query(False)):
    content = await request.body()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(413, detail={"code": "PHOTO_TOO_LARGE", "message": "Photos must be 2 MB or smaller."})
    result = await run_in_threadpool(ProofService(db).upload_photo, current_user.id, activity_id,
                                   content, request.headers.get("content-type", "").split(";")[0], consent)
    return wrap_response(result, request)


@router.get("/activities/{activity_id}/proofs/review", response_model=ResponseEnvelope[list[ProofResponse]])
def list_review(request: Request, activity_id: UUID, current_user: CurrentUser, db: DbSession):
    return wrap_response(ProofService(db).list_for_review(current_user.id, activity_id), request)


@router.get("/proofs/{proof_id}/preview")
async def preview_photo(request: Request, proof_id: UUID, current_user: CurrentUser, db: DbSession):
    result = await run_in_threadpool(ProofService(db).preview, current_user.id, proof_id)
    return wrap_response(result, request)


@router.post("/activities/{activity_id}/proofs/upload-url", response_model=ResponseEnvelope[UploadUrlResponse])
def get_proof_upload_url(
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
def register_proof(
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
def get_my_proof(
    request: Request,
    activity_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ProofService(db)
    result = service.get_my_proof(current_user.id, activity_id)
    return wrap_response(result, request)


@router.post("/proofs/{proof_id}/confirm", response_model=ResponseEnvelope[SuccessStatus])
def confirm_proof(
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
def delete_proof(
    request: Request,
    proof_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    service = ProofService(db)
    service.delete_proof(current_user.id, proof_id)
    return wrap_response(SuccessStatus(success=True, message="Proof removed"), request)
