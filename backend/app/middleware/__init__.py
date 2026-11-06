"""Single registration point for the JOMO HTTP boundary."""

from fastapi import FastAPI
from app.middleware.cors import ApiCORSMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.exception_handler import register_exception_handlers, SafeExceptionMiddleware
from app.middleware.body_limit import BodyLimitMiddleware
from app.middleware.audit import AuditMiddleware


def setup_middleware(app: FastAPI, cors_origins=None, max_requests_per_minute=120,
                     user_requests_per_minute=120, max_body_bytes=1024 * 1024,
                     api_prefix="/api/v1") -> None:
    """Incoming: ID -> security -> audit -> CORS -> safe errors -> rate -> body -> routes.

    Reverse registration is intentional. Early exits and errors pass through all
    response wrappers, while valid CORS preflight does not spend a rate allowance.
    """
    if getattr(app.state, "middleware_configured", False):
        raise RuntimeError("JOMO middleware is already configured")
    origins = cors_origins if cors_origins is not None else ["http://localhost:3000", "http://127.0.0.1:3000"]
    if "*" in origins:
        raise ValueError("Credentialed CORS requires explicit origins")
    register_exception_handlers(app)
    app.add_middleware(BodyLimitMiddleware, max_body_bytes=max_body_bytes)
    app.add_middleware(RateLimitMiddleware, max_requests_per_minute=max_requests_per_minute,
                       user_requests_per_minute=user_requests_per_minute, api_prefix=api_prefix)
    app.add_middleware(SafeExceptionMiddleware)
    app.add_middleware(ApiCORSMiddleware, allow_origins=origins, allow_credentials=True,
                       allow_methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                       allow_headers=["Authorization", "Content-Type", "X-Request-Id", "X-Dev-User-Id", "X-Screening-Consent"],
                       expose_headers=["X-Request-Id", "Retry-After", "WWW-Authenticate"])
    app.add_middleware(AuditMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.state.middleware_configured = True


# Retain the existing import used by prototypes and tests.
setup_prototype_middleware = setup_middleware

__all__ = ["RequestIdMiddleware", "SecurityHeadersMiddleware", "RateLimitMiddleware",
           "register_exception_handlers", "setup_middleware", "setup_prototype_middleware"]
