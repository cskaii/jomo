"""Resolve identity through Supabase Auth; never trust unverified token claims."""

from typing import Optional
from uuid import UUID
from urllib.parse import urlsplit

import httpx
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    id: UUID
    email: Optional[str] = None
    role: str = "authenticated"


def auth_error(code="INVALID_TOKEN", message="Invalid or expired authentication token"):
    return HTTPException(
        status_code=401,
        detail={"code": code, "message": message, "details": None},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def verify_auth_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_dev_user_id: Optional[str] = Header(None, alias="X-Dev-User-Id"),
) -> AuthenticatedUser:
    settings = get_settings()
    authorization = request.headers.get("authorization")
    user = None
    # Explicit opt-in preserves the local demo without a production bypass.
    if settings.dev_auth_allowed and x_dev_user_id:
        try:
            user = AuthenticatedUser(id=UUID(x_dev_user_id), email="dev@jomo.local")
        except ValueError:
            raise auth_error()

    if user is None:
        if not authorization:
            raise auth_error("AUTH_REQUIRED", "Authentication is required")
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer" or len(parts[1]) > 8192:
            raise auth_error()
        token = parts[1]
        if settings.dev_auth_allowed:
            try:
                user = AuthenticatedUser(id=UUID(token.removeprefix("dev-user-")))
            except ValueError:
                pass

        if user is None:
            if token.count(".") != 2:
                raise auth_error()
            issuer = settings.AUTH_ISSUER_URL.rstrip("/")
            url = urlsplit(issuer)
            if (
                settings.AUTH_PROVIDER != "supabase"
                or not settings.AUTH_PUBLIC_KEY
                or not url.hostname
                or url.username or url.password or url.query or url.fragment
                or (url.scheme != "https" and not (
                    settings.APP_ENV in ("development", "test")
                    and url.scheme == "http" and url.hostname in ("localhost", "127.0.0.1")
                ))
            ):
                raise HTTPException(503, detail={"code": "AUTH_UNAVAILABLE", "message": "Authentication is not configured."})
            try:
                # The configured Supabase server validates the token. No service-role key.
                async with httpx.AsyncClient(timeout=settings.AUTH_TIMEOUT_SECONDS, follow_redirects=False) as client:
                    response = await client.get(
                        f"{issuer}/user",
                        headers={"Authorization": f"Bearer {token}", "apikey": settings.AUTH_PUBLIC_KEY},
                    )
            except httpx.RequestError:
                raise HTTPException(503, detail={"code": "AUTH_UNAVAILABLE", "message": "Authentication is temporarily unavailable."}) from None
            if response.status_code in (401, 403):
                raise auth_error()
            if response.status_code != 200:
                raise HTTPException(503, detail={"code": "AUTH_UNAVAILABLE", "message": "Authentication is temporarily unavailable."})
            try:
                data = response.json()
                if data.get("aud") != settings.AUTH_AUDIENCE or data.get("role") != "authenticated":
                    raise auth_error()
                user = AuthenticatedUser(id=data["id"], email=data.get("email"))
            except (ValueError, KeyError, TypeError, AttributeError):
                raise HTTPException(503, detail={"code": "AUTH_UNAVAILABLE", "message": "Authentication returned an invalid response."}) from None

    request.state.actor_id = str(user.id)
    limiter = getattr(request.state, "rate_limiter", None)
    if limiter is not None:
        limiter.enforce_user(request, str(user.id))
    return user
