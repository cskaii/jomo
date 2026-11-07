"""Private Supabase Storage. Credentials and provider error bodies never leave the server."""
from urllib.parse import urlsplit
import re
import httpx
from fastapi import HTTPException
from app.core.config import get_settings


class StorageService:
    def __init__(self):
        self.settings = get_settings()

    def call(self, method, path, **kwargs):
        issuer = self.settings.AUTH_ISSUER_URL.rstrip("/")
        parsed = urlsplit(issuer)
        key = self.settings.SUPABASE_SECRET_KEY.get_secret_value()
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment or not issuer.endswith("/auth/v1")
                or not key.startswith("sb_secret_")
                or not re.fullmatch(r"[a-z0-9-]{1,63}", self.settings.STORAGE_BUCKET)):
            raise HTTPException(503, detail={"code": "STORAGE_UNAVAILABLE", "message": "Private photo storage has not been configured."})
        headers = kwargs.pop("headers", {})
        headers["apikey"] = key
        try:
            with httpx.Client(timeout=self.settings.STORAGE_TIMEOUT_SECONDS, follow_redirects=False) as client:
                response = client.request(method, issuer[:-len('/auth/v1')] + "/storage/v1/" + path,
                                          headers=headers, **kwargs)
        except httpx.RequestError:
            raise HTTPException(503, detail={"code": "STORAGE_UNAVAILABLE", "message": "Private photo storage is temporarily unavailable."}) from None
        if response.status_code >= 400:
            raise HTTPException(503, detail={"code": "STORAGE_UNAVAILABLE", "message": "Private photo storage is unavailable. Check the bucket configuration."})
        return response

    def upload(self, key, content, mime):
        self.call("POST", f"object/{self.settings.STORAGE_BUCKET}/{key}", content=content,
                  headers={"Content-Type": mime, "x-upsert": "false"})

    def delete(self, key):
        # Supabase's bulk remove operation is idempotent for absent objects.
        self.call("DELETE", f"object/{self.settings.STORAGE_BUCKET}", json={"prefixes": [key]})

    def signed_url(self, key):
        data = self.call("POST", f"object/sign/{self.settings.STORAGE_BUCKET}/{key}", json={"expiresIn": 60}).json()
        path = data.get("signedURL", "")
        if not path.startswith("/object/sign/"):
            raise HTTPException(503, detail={"code": "STORAGE_UNAVAILABLE", "message": "Photo preview is temporarily unavailable."})
        return self.settings.AUTH_ISSUER_URL.rstrip("/")[:-len('/auth/v1')] + "/storage/v1" + path
