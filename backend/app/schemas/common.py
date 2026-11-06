from typing import Generic, Optional, TypeVar, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ResponseEnvelope(BaseModel, Generic[T]):
    data: T
    request_id: str = Field(default="00000000-0000-0000-0000-000000000000")


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
    request_id: str = Field(default="00000000-0000-0000-0000-000000000000")


class SuccessStatus(BaseModel):
    success: bool = True
    message: Optional[str] = None
