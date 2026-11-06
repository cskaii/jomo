from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import logger
from app.middleware.responses import error_response


def internal_error(scope):
    # Exception strings/tracebacks can contain SQL parameters or screened content.
    logger.error("Unhandled application error [request_id=%s]", scope.get("state", {}).get("request_id"))
    return error_response(scope, 500, "INTERNAL_SERVER_ERROR", "An unexpected error occurred. Please try again later.")


class SafeExceptionMiddleware:
    """Catch failures before response start, inside CORS/security/request-ID wrappers."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started = False

        async def capture(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, capture)
        except Exception:
            if started:
                scope.setdefault("state", {})["error_code"] = "RESPONSE_INTERRUPTED"
                # A streaming response cannot be replaced after headers were sent.
                raise
            await internal_error(scope)(scope, receive, send)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        first = errors[0].get("loc", []) if errors else []
        details = {
            "field": str(first[-1]) if first else None,
            "errors": [
                {"loc": [str(v) for v in err.get("loc", [])],
                 "msg": "Invalid value." if err.get("type") == "value_error" else err.get("msg", "Invalid value.")}
                for err in errors
            ],
        }
        return error_response(request.scope, 422, "VALIDATION_ERROR", "The request is invalid.", details)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code >= 500:
            # Preserve only intentional safe operational failures, never arbitrary details.
            safe_messages = {
                "AUTH_UNAVAILABLE": "Authentication is temporarily unavailable.",
                "STORAGE_NOT_CONFIGURED": "Photo uploads are not available yet.",
                "RATE_LIMIT_UNAVAILABLE": "Request limiting is temporarily unavailable.",
            }
            code = exc.detail.get("code") if isinstance(exc.detail, dict) else None
            if code in safe_messages:
                return error_response(request.scope, exc.status_code, code, safe_messages[code], headers=exc.headers)
            return internal_error(request.scope)
        if isinstance(exc.detail, dict):
            code = exc.detail.get("code", "HTTP_ERROR")
            message = exc.detail.get("message", "An error occurred.")
            details = exc.detail.get("details")
        else:
            code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
            message = str(exc.detail) if exc.detail else "An error occurred."
            details = None
        return error_response(request.scope, exc.status_code, code, message, details, exc.headers)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return internal_error(request.scope)
