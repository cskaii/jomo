from typing import TypeVar, Any
from starlette.requests import Request
from app.schemas.common import ResponseEnvelope

T = TypeVar("T")


def wrap_response(data: T, request: Request) -> ResponseEnvelope[T]:
    request_id = getattr(request.state, "request_id", "00000000-0000-0000-0000-000000000000")
    return ResponseEnvelope[T](data=data, request_id=request_id)
