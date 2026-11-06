from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, SecretStr
from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.schemas.common import ResponseEnvelope, SuccessStatus
from app.services.auth_service import AuthService
from app.utils.response import wrap_response
from uuid import uuid4

router = APIRouter(prefix="/auth", tags=["Auth"])

class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: SecretStr = Field(min_length=1, max_length=1024)

class Registration(Credentials):
    password: SecretStr = Field(min_length=8, max_length=1024)

class RefreshInput(BaseModel):
    refresh_token: SecretStr = Field(min_length=1, max_length=8192)

class EmailInput(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

class PasswordInput(BaseModel):
    password: SecretStr = Field(min_length=8, max_length=1024)

class SessionResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"

class RegistrationResponse(BaseModel):
    session: Optional[SessionResponse] = None
    message: str

def session_response(data):
    try:
        result = SessionResponse.model_validate(data)
        if not result.access_token or not result.refresh_token or result.expires_in <= 0:
            raise ValueError()
        return result
    except ValueError:
        raise HTTPException(503, detail={"code": "AUTH_UNAVAILABLE", "message": "Authentication returned an invalid session."}) from None


@router.post("/dev-session", response_model=ResponseEnvelope[SessionResponse])
async def dev_session(request: Request):
    settings = get_settings()
    if not settings.dev_auth_allowed or not settings.DATABASE_URL.startswith("sqlite"):
        raise HTTPException(404, detail="Not found")
    # An explicit local-only action creates a fresh identity, never sample rows.
    return wrap_response(SessionResponse(access_token=f"dev-user-{uuid4()}",
        refresh_token="local-preview", expires_in=86400), request)

@router.post("/login", response_model=ResponseEnvelope[SessionResponse])
async def login(request: Request, payload: Credentials):
    data = await AuthService().call("POST", "token", {"email": payload.email, "password": payload.password.get_secret_value()}, params={"grant_type": "password"})
    return wrap_response(session_response(data), request)

@router.post("/register", response_model=ResponseEnvelope[RegistrationResponse])
async def register(request: Request, payload: Registration):
    data = await AuthService().call("POST", "signup", {"email": payload.email, "password": payload.password.get_secret_value()}, params={"redirect_to": f"{get_settings().FRONTEND_URL.rstrip('/')}/login"})
    return wrap_response(RegistrationResponse(session=session_response(data) if data.get("access_token") else None, message="Check your email to confirm your account, then sign in."), request)

@router.post("/refresh", response_model=ResponseEnvelope[SessionResponse])
async def refresh(request: Request, payload: RefreshInput):
    data = await AuthService().call("POST", "token", {"refresh_token": payload.refresh_token.get_secret_value()}, params={"grant_type": "refresh_token"})
    return wrap_response(session_response(data), request)

@router.post("/logout", response_model=ResponseEnvelope[SuccessStatus])
async def logout(request: Request, current_user: CurrentUser):
    await AuthService().call("POST", "logout", token=request.headers["authorization"].split()[1], params={"scope": "local"})
    return wrap_response(SuccessStatus(message="Signed out."), request)

@router.post("/recover", response_model=ResponseEnvelope[SuccessStatus])
async def recover(request: Request, payload: EmailInput):
    try:
        await AuthService().call("POST", "recover", {"email": payload.email}, params={"redirect_to": f"{get_settings().FRONTEND_URL.rstrip('/')}/reset-password"})
    except HTTPException as exc:
        if exc.status_code != 400: raise
    return wrap_response(SuccessStatus(message="If this email can receive recovery messages, a reset link has been sent."), request)

@router.post("/password", response_model=ResponseEnvelope[SuccessStatus])
async def password(request: Request, payload: PasswordInput, current_user: CurrentUser):
    await AuthService().call("PUT", "user", {"password": payload.password.get_secret_value()}, token=request.headers["authorization"].split()[1])
    return wrap_response(SuccessStatus(message="Password updated. You can sign in now."), request)
