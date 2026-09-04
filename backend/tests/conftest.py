"""
Pytest configuration and shared fixtures.

Test DB strategy:
- Uses SQLite in-memory via aiosqlite (no PostgreSQL required to run tests)
- Overrides `get_db` dependency to use the test session
- DocumentEmbedding (pgvector) table is excluded from test DB creation
  because SQLite does not support the vector column type
- PostgreSQL-specific column types (JSONB, UUID) are replaced with
  SQLite-compatible equivalents (JSON, String) for the test schema
- Each test that needs a DB receives a fresh session (function-scoped)

Key fixtures:
  - db_session: fresh AsyncSession backed by in-memory SQLite
  - async_client: HTTPX async test client with DB dependency overridden
  - auth_headers: registers a test user and returns Bearer headers
  - mock_watsonx: patches WatsonxService (no real IBM calls)
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, String, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.core.db import Base, get_db
from app.main import app

# ── Test DB engine (SQLite in-memory) ─────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
_TestSessionLocal = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _build_sqlite_metadata():
    """
    Build a SQLAlchemy MetaData object containing only the tables that are
    SQLite-compatible (excludes document_embeddings with its vector column).
    JSONB → JSON and PostgreSQL UUID → String(36) for SQLite compatibility.
    """
    from sqlalchemy import Column, MetaData, Table, inspect
    from sqlalchemy.dialects.postgresql import JSONB as PGJSONB

    # Trigger model registration
    from app.models.user import User  # noqa: F401
    from app.models.candidate_profile import CandidateProfile  # noqa: F401
    from app.models.interview_session import InterviewSession  # noqa: F401
    from app.models.question import Question  # noqa: F401
    from app.models.answer import Answer  # noqa: F401

    sqlite_meta = MetaData()

    skip_tables = {"document_embeddings"}
    pg_uuid_type = type(None)  # placeholder

    for table_name, pg_table in Base.metadata.tables.items():
        if table_name in skip_tables:
            continue

        cols = []
        for col in pg_table.columns:
            # Replace PG-specific types with SQLite equivalents
            col_type = col.type
            if isinstance(col_type, PGJSONB):
                col_type = JSON()
            elif hasattr(col_type, "__class__") and "UUID" in type(col_type).__name__:
                col_type = String(36)

            new_col = col._copy()
            new_col.type = col_type
            cols.append(new_col)

        constraints = [c for c in pg_table.constraints if c.__class__.__name__ != "CheckConstraint"]

        Table(table_name, sqlite_meta, *cols, *constraints, extend_existing=True)

    return sqlite_meta


@pytest.fixture(scope="session", autouse=True)
def event_loop_policy():
    """Use the default asyncio event loop policy (required for pytest-asyncio)."""
    import asyncio
    policy = asyncio.DefaultEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)


@pytest.fixture(scope="session")
async def setup_test_db():
    """
    Create all compatible tables in the SQLite test DB.
    Runs once per test session.
    """
    sqlite_meta = _build_sqlite_metadata()

    async with _test_engine.begin() as conn:
        await conn.run_sync(sqlite_meta.create_all)

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(sqlite_meta.drop_all)


@pytest.fixture
async def db_session(setup_test_db):
    """
    Provide a fresh AsyncSession for each test.
    Rolls back after each test to keep tests isolated.
    """
    async with _TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def async_client(db_session: AsyncSession):
    """
    HTTPX async client with the `get_db` dependency overridden to use the test DB.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(async_client: AsyncClient) -> dict:
    """
    Register a test user and return Authorization headers.
    Useful for tests that need an authenticated request.
    """
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
        },
    )
    assert resp.status_code == 201, f"auth_headers fixture failed: {resp.json()}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_watsonx(mocker):
    """
    Patches WatsonxService so no real IBM API calls are made in tests.
    """
    mock = mocker.patch("app.services.watsonx_service.WatsonxService")
    instance = mock.return_value
    instance.generate.return_value = "{}"
    instance.embed.return_value = [0.0] * 1536
    return instance
