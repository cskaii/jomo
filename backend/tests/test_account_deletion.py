"""Deletion safeguards. All provider calls are mocked; no real account is deleted."""
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

import httpx
from fastapi import HTTPException
from pydantic import SecretStr, ValidationError

from app.core.auth import AuthenticatedUser
from app.schemas.user import DeleteAccountRequest
from app.services.account_deletion_service import AccountDeletionService


class AccountDeletionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = AuthenticatedUser(id=uuid.uuid4(), email="delete-test@example.invalid")
        self.payload = DeleteAccountRequest(confirmation="DELETE", password="test-password")
        self.db = MagicMock()
        self.db.get_bind.return_value.dialect.name = "postgresql"
        self.db.execute.return_value.scalar_one.return_value = True
        self.settings = SimpleNamespace(AUTH_PROVIDER="supabase", AUTH_PUBLIC_KEY="publishable-test",
            AUTH_ISSUER_URL="https://example.supabase.co/auth/v1", AUTH_TIMEOUT_SECONDS=5,
            SUPABASE_SECRET_KEY=SecretStr("sb_secret_test-only"))
        self.service = AccountDeletionService(self.db)
        self.provider = AsyncMock(return_value={"user": {"id": str(self.user.id)}, "access_token": "verification-token"})
        self.http = AsyncMock()
        self.http.request.return_value = httpx.Response(200)
        self.context = AsyncMock()
        self.context.__aenter__.return_value = self.http
        self.patches = [
            patch("app.services.account_deletion_service.get_settings", return_value=self.settings),
            patch("app.services.account_deletion_service.AuthService.call", self.provider),
            patch("app.services.account_deletion_service.httpx.AsyncClient", return_value=self.context),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    async def test_deletes_only_authenticated_identity_with_server_key(self):
        await self.service.delete(self.user, self.payload)
        args, kwargs = self.http.request.call_args
        self.assertEqual(args, ("DELETE", f"https://example.supabase.co/auth/v1/admin/users/{self.user.id}"))
        self.assertEqual(kwargs["headers"], {"apikey": "sb_secret_test-only"})
        self.assertEqual(kwargs["json"], {"should_soft_delete": False})
        self.db.rollback.assert_called_once()
        self.db.delete.assert_not_called()
        self.db.commit.assert_not_called()
        self.assertEqual(self.provider.await_count, 1)

    async def test_wrong_password_never_calls_admin_api(self):
        self.provider.side_effect = HTTPException(401)
        with self.assertRaises(HTTPException) as caught:
            await self.service.delete(self.user, self.payload)
        self.assertEqual(caught.exception.detail["code"], "PASSWORD_INCORRECT")
        self.http.request.assert_not_called()

    async def test_missing_key_or_cleanup_trigger_blocks_deletion(self):
        self.settings.SUPABASE_SECRET_KEY = SecretStr("")
        with self.assertRaises(HTTPException):
            await self.service.delete(self.user, self.payload)
        self.settings.SUPABASE_SECRET_KEY = SecretStr("sb_secret_test-only")
        self.db.execute.return_value.scalar_one.return_value = False
        with self.assertRaises(HTTPException):
            await self.service.delete(self.user, self.payload)
        self.provider.assert_not_called()
        self.http.request.assert_not_called()

    async def test_mismatched_password_identity_never_deletes_other_user(self):
        self.provider.return_value = {"user": {"id": str(uuid.uuid4())}}
        with self.assertRaises(HTTPException):
            await self.service.delete(self.user, self.payload)
        self.http.request.assert_not_called()

    async def test_admin_failure_is_redacted_and_verification_session_revoked(self):
        self.http.request.return_value = httpx.Response(500, text="private SQL error")
        with self.assertRaises(HTTPException) as caught:
            await self.service.delete(self.user, self.payload)
        self.assertNotIn("private SQL", str(caught.exception.detail))
        self.assertEqual(self.provider.call_args.args, ("POST", "logout"))
        self.db.delete.assert_not_called()
        self.db.commit.assert_not_called()

    async def test_network_failure_revokes_verification_session(self):
        self.http.request.side_effect = httpx.ConnectError("test transport failure")
        with self.assertRaises(HTTPException) as caught:
            await self.service.delete(self.user, self.payload)
        self.assertEqual(caught.exception.status_code, 503)
        self.assertEqual(self.provider.call_args.args, ("POST", "logout"))

    def test_requires_exact_confirmation_and_forbids_target_user_id(self):
        for payload in (
            {"confirmation": "delete", "password": "test"},
            {"confirmation": "DELETE", "password": "test", "user_id": str(uuid.uuid4())},
            {"confirmation": "DELETE", "password": ""},
        ):
            with self.assertRaises(ValidationError):
                DeleteAccountRequest.model_validate(payload)
        self.assertNotIn("test-password", repr(self.payload))

    def test_sql_editor_script_matches_deployed_migration(self):
        root = Path(__file__).resolve().parents[2]
        canonical = (root / "backend/app/db/account_deletion.sql").read_text(encoding="utf-8")
        editor_script = (root / "supabase/account_deletion.sql").read_text(encoding="utf-8")
        assert canonical in editor_script
        assert editor_script.strip().endswith("COMMIT;")


def test_delete_endpoint_requires_authentication(client):
    response = client.request("DELETE", "/api/v1/users/me", json={"confirmation": "DELETE", "password": "test"})
    assert response.status_code == 401


def test_delete_endpoint_rejects_client_selected_identity(client):
    response = client.request("DELETE", "/api/v1/users/me",
        headers={"Authorization": f"Bearer {uuid.uuid4()}"},
        json={"confirmation": "DELETE", "password": "test", "user_id": str(uuid.uuid4())})
    assert response.status_code == 422


def test_unconfigured_deletion_returns_safe_operational_error(client):
    response = client.request("DELETE", "/api/v1/users/me",
        headers={"Authorization": f"Bearer {uuid.uuid4()}"},
        json={"confirmation": "DELETE", "password": "test"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ACCOUNT_DELETION_UNAVAILABLE"
    assert "test-password" not in response.text
