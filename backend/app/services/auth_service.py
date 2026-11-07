"""Supabase Auth gateway. Credentials are never logged or stored in app tables."""
from urllib.parse import urlsplit
import httpx
from fastapi import HTTPException
from app.core.config import get_settings


class AuthService:
    async def call(self, method, path, payload=None, token=None, params=None):
        settings = get_settings()
        issuer = settings.AUTH_ISSUER_URL.rstrip("/")
        url = urlsplit(issuer)
        if (settings.AUTH_PROVIDER != "supabase" or not settings.AUTH_PUBLIC_KEY
                or url.scheme != "https" or not url.hostname or url.username or url.password
                or url.query or url.fragment):
            raise HTTPException(503, detail={"code": "AUTH_UNAVAILABLE", "message": "Supabase authentication is not configured."})
        headers = {"apikey": settings.AUTH_PUBLIC_KEY}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            async with httpx.AsyncClient(timeout=settings.AUTH_TIMEOUT_SECONDS, follow_redirects=False) as client:
                response = await client.request(method, f"{issuer}/{path}", headers=headers, json=payload, params=params)
        except httpx.RequestError:
            raise HTTPException(503, detail={"code": "AUTH_UNAVAILABLE", "message": "Supabase authentication is temporarily unavailable."}) from None
        if response.status_code >= 500:
            raise HTTPException(503, detail={"code": "AUTH_UNAVAILABLE", "message": "Supabase authentication is temporarily unavailable."})
        if response.status_code == 429:
            raise HTTPException(429, detail={"code": "AUTH_RATE_LIMITED", "message": "Too many authentication attempts. Please wait before retrying."})
        if response.status_code >= 400:
            if path in ("signup", "user"):
                try:
                    rejected = response.json()
                except ValueError:
                    rejected = {}
                if isinstance(rejected, dict) and (rejected.get("error_code") == "weak_password" or rejected.get("code") == "weak_password"):
                    raise HTTPException(400, detail={"code": "WEAK_PASSWORD", "message": "This password does not meet the account's password protection settings. Choose another unique password."})
            raise HTTPException(401 if path == "token" else 400, detail={"code": "AUTH_REJECTED", "message": "Sign-in was not accepted. Check your email, password and email confirmation." if path == "token" else "The authentication request was not accepted. Check your details or try again later."})
        if not response.content:
            return {}
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except (ValueError, TypeError):
            raise HTTPException(503, detail={"code": "AUTH_UNAVAILABLE", "message": "Authentication returned an invalid response."}) from None
