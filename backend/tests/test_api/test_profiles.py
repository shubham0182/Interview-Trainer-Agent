"""
ST-03 Profile API tests.

Covers:
  - GET /profiles/me — creates blank profile if none exists
  - GET /profiles/me — returns existing profile
  - PUT /profiles/me — update job_role, experience_level, skills
  - PUT /profiles/me — update education entries
  - PUT /profiles/me — update experience entries
  - PUT /profiles/me — update projects entries
  - PUT /profiles/me — partial update (only provided fields changed)
  - Unauthorized GET /profiles/me returns 401
  - Unauthorized PUT /profiles/me returns 401
  - User A cannot access User B's profile (isolation)
  - hashed_password never appears in profile responses
  - invalid experience_level returns 422
"""
import pytest
from httpx import AsyncClient


class TestGetProfile:
    async def test_get_profile_without_auth_returns_401(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/profiles/me")
        assert resp.status_code == 401

    async def test_get_profile_creates_blank_profile(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.get("/api/v1/profiles/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_role"] is None
        assert data["experience_level"] is None
        assert data["skills"] == []
        assert data["education"] == []
        assert data["experience"] == []
        assert data["projects"] == []
        assert data["resume_parsed"] is False

    async def test_get_profile_returns_user_id(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        # Get the current user's ID
        me = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = me.json()["id"]

        profile = await async_client.get("/api/v1/profiles/me", headers=auth_headers)
        assert profile.json()["user_id"] == user_id

    async def test_profile_never_exposes_password_hash(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.get("/api/v1/profiles/me", headers=auth_headers)
        raw = resp.text
        assert "hashed_password" not in raw
        assert "$2b$" not in raw


class TestUpdateProfile:
    async def test_update_profile_without_auth_returns_401(self, async_client: AsyncClient):
        resp = await async_client.put(
            "/api/v1/profiles/me",
            json={"job_role": "Software Engineer"},
        )
        assert resp.status_code == 401

    async def test_update_job_role(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.put(
            "/api/v1/profiles/me",
            headers=auth_headers,
            json={"job_role": "Software Engineer"},
        )
        assert resp.status_code == 200
        assert resp.json()["job_role"] == "Software Engineer"

    async def test_update_experience_level_valid(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        for level in ("fresher", "junior", "mid", "senior"):
            resp = await async_client.put(
                "/api/v1/profiles/me",
                headers=auth_headers,
                json={"experience_level": level},
            )
            assert resp.status_code == 200, f"Failed for level={level}: {resp.json()}"
            assert resp.json()["experience_level"] == level

    async def test_update_experience_level_invalid_returns_422(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.put(
            "/api/v1/profiles/me",
            headers=auth_headers,
            json={"experience_level": "expert"},
        )
        assert resp.status_code == 422

    async def test_update_skills(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.put(
            "/api/v1/profiles/me",
            headers=auth_headers,
            json={"skills": ["Python", "FastAPI", "PostgreSQL"]},
        )
        assert resp.status_code == 200
        assert resp.json()["skills"] == ["Python", "FastAPI", "PostgreSQL"]

    async def test_update_education(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.put(
            "/api/v1/profiles/me",
            headers=auth_headers,
            json={
                "education": [
                    {
                        "degree": "B.Tech",
                        "institution": "IIT Delhi",
                        "year": "2025",
                        "field_of_study": "Computer Science",
                    }
                ]
            },
        )
        assert resp.status_code == 200
        edu = resp.json()["education"]
        assert len(edu) == 1
        assert edu[0]["degree"] == "B.Tech"
        assert edu[0]["institution"] == "IIT Delhi"

    async def test_update_experience(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.put(
            "/api/v1/profiles/me",
            headers=auth_headers,
            json={
                "experience": [
                    {
                        "title": "Software Intern",
                        "company": "Acme Corp",
                        "duration": "6 months",
                        "description": "Built REST APIs using FastAPI",
                    }
                ]
            },
        )
        assert resp.status_code == 200
        exp = resp.json()["experience"]
        assert len(exp) == 1
        assert exp[0]["title"] == "Software Intern"

    async def test_update_projects(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.put(
            "/api/v1/profiles/me",
            headers=auth_headers,
            json={
                "projects": [
                    {
                        "name": "InterviewPro AI",
                        "description": "AI interview platform",
                        "technologies": ["Python", "Next.js"],
                        "url": "https://github.com/example/interviewpro",
                    }
                ]
            },
        )
        assert resp.status_code == 200
        projects = resp.json()["projects"]
        assert len(projects) == 1
        assert projects[0]["name"] == "InterviewPro AI"
        assert "Python" in projects[0]["technologies"]

    async def test_partial_update_does_not_clear_other_fields(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """PUT with only job_role must not clear skills set in a prior request."""
        await async_client.put(
            "/api/v1/profiles/me",
            headers=auth_headers,
            json={"skills": ["Python", "Django"]},
        )
        resp = await async_client.put(
            "/api/v1/profiles/me",
            headers=auth_headers,
            json={"job_role": "Backend Developer"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_role"] == "Backend Developer"
        # skills must still be set from previous request
        assert data["skills"] == ["Python", "Django"]

    async def test_get_after_update_returns_updated_data(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        await async_client.put(
            "/api/v1/profiles/me",
            headers=auth_headers,
            json={"job_role": "Data Scientist", "experience_level": "junior"},
        )
        resp = await async_client.get("/api/v1/profiles/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_role"] == "Data Scientist"
        assert data["experience_level"] == "junior"


class TestProfileIsolation:
    async def test_different_users_have_separate_profiles(
        self, async_client: AsyncClient
    ):
        """User A updating their profile must not affect User B's profile."""
        # Register User A
        r_a = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "user_a@example.com", "password": "PassA12345!"},
        )
        headers_a = {"Authorization": f"Bearer {r_a.json()['access_token']}"}

        # Register User B
        r_b = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "user_b@example.com", "password": "PassB12345!"},
        )
        headers_b = {"Authorization": f"Bearer {r_b.json()['access_token']}"}

        # User A updates their profile
        await async_client.put(
            "/api/v1/profiles/me",
            headers=headers_a,
            json={"job_role": "Engineer A"},
        )

        # User B's profile must be unaffected
        resp_b = await async_client.get("/api/v1/profiles/me", headers=headers_b)
        assert resp_b.json()["job_role"] is None

    async def test_profile_user_id_matches_authenticated_user(
        self, async_client: AsyncClient
    ):
        """Profile user_id must always equal the authenticated user's id."""
        reg = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "iso_test@example.com", "password": "IsoPass1!"},
        )
        token = reg.json()["access_token"]
        user_id = reg.json()["user"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        profile = await async_client.get("/api/v1/profiles/me", headers=headers)
        assert profile.json()["user_id"] == user_id
