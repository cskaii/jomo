"""Delete only the authenticated account, through Supabase's server admin API.

The database trigger removes application data in the same transaction as Auth.
Never delete public.users first: a failed Auth request would leave a usable login.
"""
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser
from app.core.config import get_settings
from app.schemas.user import DeleteAccountRequest
from app.services.auth_service import AuthService


def unavailable(message="Account deletion is temporarily unavailable. Please try again later."):
    return HTTPException(503, detail={"code": "ACCOUNT_DELETION_UNAVAILABLE", "message": message})


class AccountDeletionService:
    def __init__(self, db: Session):
        self.db = db

    def ensure_ready(self):
        settings = get_settings()
        issuer = urlsplit(settings.AUTH_ISSUER_URL.rstrip("/"))
        if (settings.AUTH_PROVIDER != "supabase" or not settings.AUTH_PUBLIC_KEY
                or not settings.SUPABASE_SECRET_KEY.get_secret_value().startswith("sb_secret_")
                or issuer.scheme != "https" or not issuer.hostname
                or issuer.username or issuer.password or issuer.query or issuer.fragment):
            raise unavailable("Account deletion has not been configured yet. Please contact the JOMO team.")
        if self.db.get_bind().dialect.name != "postgresql":
            raise unavailable("Account deletion requires the Supabase database setup.")
        installed = self.db.execute(text("""
            SELECT count(*) = 2 FROM pg_trigger
            WHERE NOT tgisinternal AND tgenabled IN ('O', 'A') AND (
              (tgrelid = to_regclass('auth.users') AND tgname = 'jomo_delete_app_account')
              OR (tgrelid = to_regclass('public.users') AND tgname = 'jomo_prepare_account_deletion')
            )
        """)).scalar_one()
        # Do not hold a database transaction while waiting for Auth's transaction.
        self.db.rollback()
        if not installed:
            raise unavailable("Account deletion database setup is incomplete. Please contact the JOMO team.")

    async def delete(self, user: AuthenticatedUser, payload: DeleteAccountRequest):
        self.ensure_ready()
        if not user.email:
            raise HTTPException(400, detail={"code": "REAUTHENTICATION_REQUIRED",
                "message": "Sign in with your email and password before deleting your account."})
        try:
            session = await AuthService().call("POST", "token", {
                "email": user.email, "password": payload.password.get_secret_value(),
            }, params={"grant_type": "password"})
        except HTTPException as exc:
            if exc.status_code in (400, 401):
                raise HTTPException(400, detail={"code": "PASSWORD_INCORRECT",
                    "message": "Your current password was not accepted. Please try again."}) from None
            raise
        identity = session.get("user")
        if not isinstance(identity, dict) or identity.get("id") != str(user.id):
            raise unavailable()
        settings = get_settings()
        key = settings.SUPABASE_SECRET_KEY.get_secret_value()
        response = None
        try:
            async with httpx.AsyncClient(timeout=settings.AUTH_TIMEOUT_SECONDS, follow_redirects=False) as client:
                response = await client.request(
                    "DELETE",
                    f"{settings.AUTH_ISSUER_URL.rstrip('/')}/admin/users/{user.id}",
                    headers={"apikey": key},
                    json={"should_soft_delete": False},
                )
        except httpx.RequestError:
            raise unavailable() from None
        finally:
            # Password verification creates a session. Revoke it even if deletion
            # failed; never return or persist its access/refresh tokens.
            if (response is None or response.status_code not in (200, 204)) and session.get("access_token"):
                try:
                    await AuthService().call("POST", "logout", token=session["access_token"], params={"scope": "local"})
                except HTTPException:
                    pass
        if response.status_code not in (200, 204):
            # Provider bodies can include database details; never forward/log them.
            raise unavailable()
