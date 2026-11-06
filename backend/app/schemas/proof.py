from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.core.enums import ProofType, ProofStatus


class UploadUrlRequest(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=150, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*\.(?:jpg|jpeg|png|webp)$")
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]
    file_size_bytes: int = Field(..., ge=1, le=10 * 1024 * 1024)  # 10MB limit


class UploadUrlResponse(BaseModel):
    upload_url: str
    storage_key: str
    expires_at: datetime


class ProofRegisterRequest(BaseModel):
    proof_type: Literal[ProofType.PHOTO, ProofType.GROUP_CONFIRMATION] = ProofType.PHOTO
    storage_key: Optional[str] = Field(None, max_length=500)


class ProofResponse(BaseModel):
    id: UUID
    activity_id: UUID
    participant_id: UUID
    proof_type: ProofType
    status: ProofStatus
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProofConfirmRequest(BaseModel):
    decision: str = Field(..., pattern="^(confirm|reject)$")
    comment: Optional[str] = Field(None, max_length=300)

