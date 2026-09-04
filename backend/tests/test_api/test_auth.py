"""
ST-03 Authentication API tests.

Covers:
  - successful registration (201 + token)
  - duplicate email registration (409)
  - invalid registration payloads (422)
  - password is hashed + not exposed in response
  - successful login (200 + token)
  - wrong password (401)
  - unknown email (401)
  - malformed credentials (422)
  - GET /auth/me with valid JWT (200)
  - GET /auth/me without token (401)
  - GET /auth/me with invalid token (401)
  - GET /auth/me with expired token (401)
  - hashed_password never appears in any response body
"""
import json
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import settings


# ── Registration ──────────────────────────────────────────────────────────────

class TestRegister:
    async def test_successful_registration_returns_201(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "alice@example.com", "password": "SecurePass1!"},
        )
        assert resp.status_code == 201

    async def test_successful_registration_returns_token(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "alice2@example.com", "password": "SecurePass1!"},
        )
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    async def test_registration_response_contains_user(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "bob@example.com",
                "password": "SecurePass1!",
                "full_name": "Bob Smith",
            },
        )
        data = resp.json()
        user = data["user"]
        assert user["email"] == "bob@example.com"
        assert user["full_name"] == "Bob Smith"
        assert "id" in user
        assert "created_at" in user

    async def test_registration_never_exposes_password_hash(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "nohash@example.com", "password": "SecurePass1!"},
        )
        raw = resp.text
        # hashed_password should never appear in any response body
        assert "hashed_password" not in raw
        assert "$2b$" not in raw  # bcrypt prefix

    async def test_email_normalized_to_lowercase(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "UPPER@EXAMPLE.COM", "password": "SecurePass1!"},
        )
        assert resp.status_code == 201
        assert resp.json()["user"]["email"] == "upper@example.com"

    async def test_duplicate_email_returns_409(self, async_client: AsyncClient):
        payload = {"email": "dup@example.com", "password": "SecurePass1!"}
        r1 = await async_client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201
        r2 = await async_client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409
        assert "already exists" in r2.json()["detail"].lower()

    async def test_duplicate_email_case_insensitive(self, async_client: AsyncClient):
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "case@example.com", "password": "SecurePass1!"},
        )
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "CASE@EXAMPLE.COM", "password": "SecurePass1!"},
        )
        assert resp.status_code == 409

    async def test_missing_email_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"password": "SecurePass1!"},
        )
        assert resp.status_code == 422

    async def test_invalid_email_format_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "SecurePass1!"},
        )
        assert resp.status_code == 422

    async def test_password_too_short_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "short@example.com", "password": "abc"},
        )
        assert resp.status_code == 422

    async def test_missing_password_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "nopwd@example.com"},
        )
        assert resp.status_code == 422

    async def test_empty_body_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 422

    async def test_token_sub_is_user_id(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "subtest@example.com", "password": "SecurePass1!"},
        )
        token = resp.json()["access_token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = resp.json()["user"]["id"]
        assert payload["sub"] == user_id


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    @pytest.fixture(autouse=True)
    async def register_user(self, async_client: AsyncClient):
        """Register a fresh user before each login test."""
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "LoginPass1!"},
        )

    async def test_successful_login_returns_200(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "LoginPass1!"},
        )
        assert resp.status_code == 200

    async def test_successful_login_returns_token(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "LoginPass1!"},
        )
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_never_exposes_password_hash(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "LoginPass1!"},
        )
        raw = resp.text
        assert "hashed_password" not in raw
        assert "$2b$" not in raw

    async def test_wrong_password_returns_401(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "WrongPassword!"},
        )
        assert resp.status_code == 401

    async def test_unknown_email_returns_401(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "LoginPass1!"},
        )
        assert resp.status_code == 401

    async def test_unknown_email_same_error_as_wrong_password(self, async_client: AsyncClient):
        """Must not reveal whether the email exists — both 401 errors must look the same."""
        wrong_pwd = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "WrongPassword!"},
        )
        no_email = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "LoginPass1!"},
        )
        assert wrong_pwd.status_code == no_email.status_code == 401
        assert wrong_pwd.json()["detail"] == no_email.json()["detail"]

    async def test_missing_email_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"password": "LoginPass1!"},
        )
        assert resp.status_code == 422

    async def test_missing_password_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com"},
        )
        assert resp.status_code == 422

    async def test_empty_body_returns_422(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422

    async def test_login_email_case_insensitive(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "LOGIN@EXAMPLE.COM", "password": "LoginPass1!"},
        )
        assert resp.status_code == 200


# ── /auth/me ──────────────────────────────────────────────────────────────────

class TestMe:
    async def test_me_with_valid_token_returns_200(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200

    async def test_me_returns_correct_user(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        data = resp.json()
        assert data["email"] == "testuser@example.com"
        assert data["full_name"] == "Test User"
        assert "id" in data
        assert "created_at" in data

    async def test_me_never_exposes_password_hash(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        raw = resp.text
        assert "hashed_password" not in raw
        assert "$2b$" not in raw

    async def test_me_without_token_returns_401(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_with_invalid_token_returns_401(self, async_client: AsyncClient):
        resp = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.not.valid"},
        )
        assert resp.status_code == 401

    async def test_me_with_expired_token_returns_401(self, async_client: AsyncClient):
        from app.core.security import create_access_token
        from datetime import UTC, datetime, timedelta
        import uuid

        # Manually craft an already-expired token
        expired_token = jwt.encode(
            {"sub": str(uuid.uuid4()), "exp": datetime.now(UTC) - timedelta(hours=1)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        resp = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    async def test_me_with_malformed_bearer_returns_401(self, async_client: AsyncClient):
        resp = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "NotBearer token123"},
        )
        assert resp.status_code == 401
