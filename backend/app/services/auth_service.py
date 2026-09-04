"""
Auth service — user creation, lookup, and authentication.

Keeps business logic out of route handlers.
Route handlers call these functions; they never call SQLAlchemy directly.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


# ── User creation ─────────────────────────────────────────────────────────────

async def create_user(db: AsyncSession, payload: RegisterRequest) -> User:
    """
    Create a new user row.

    Raises ValueError("email_taken") if the email is already registered.
    Normalisation (lower-case) was already applied by the Pydantic schema.
    """
    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    try:
        await db.flush()  # Detect constraint violations before commit
    except IntegrityError:
        await db.rollback()
        raise ValueError("email_taken")
    return user


# ── User lookup ───────────────────────────────────────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Return the User with the given email, or None."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Return the User with the given UUID, or None."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# ── Authentication ────────────────────────────────────────────────────────────

# Pre-computed bcrypt hash used for constant-time dummy verification when email not found.
# Prevents user-enumeration attacks via timing differences.
_DUMMY_HASH = "$2b$12$K2wyDmy.hW0P4WJxRsNwXOj/444prh7B3OMBjCT9W5fTCW4UNpj1K"


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Validate email + password credentials.

    Returns the User on success, None on any failure.
    Deliberately does NOT distinguish "no such email" from "wrong password"
    to avoid user-enumeration attacks.
    """
    user = await get_user_by_email(db, email)
    if user is None:
        # Run dummy verify so unknown-email and wrong-password take similar time.
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ── Token generation ──────────────────────────────────────────────────────────

def generate_token_for_user(user: User) -> str:
    """Create a JWT access token with the user's UUID as subject."""
    return create_access_token({"sub": str(user.id)})
