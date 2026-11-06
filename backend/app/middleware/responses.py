"""Small response helpers shared by early middleware exits and route handlers."""

import uuid
from starlette.responses import JSONResponse


def error_response(scope, status, code, message, details=None, headers=None):
    state = scope.setdefault("state", {})
    state["error_code"] = code
    request_id = state.setdefault("request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details}, "request_id": request_id},
        headers=headers,
    )
