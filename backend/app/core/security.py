"""
Security utilities: password hashing and JWT creation/verification.

Token delivery:
- Primary: httpOnly cookie named 'access_token' (set by backend on login/register)
- Fallback: Authorization: Bearer <token> header (for API clients and tests)

Usage in route handlers:
    current_user: User = Depends(get_current_user)
"""
from datetime import UTC, datetime, timedelta
from typing import Any
import uuid

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db

# ── Password hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────
# oauth2_scheme is kept for OpenAPI docs and test Bearer-header fallback
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

AUTH_COOKIE_NAME = "access_token"


def create_access_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises HTTPException 401 on failure."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


def _extract_token(request: Request, bearer_token: str | None) -> str | None:
    """
    Extract JWT from the request.

    Priority:
    1. httpOnly cookie 'access_token'  (browser flow)
    2. Authorization: Bearer header    (API clients / tests)
    """
    # 1. Cookie (primary)
    cookie_token = request.cookies.get(AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    # 2. Bearer header (fallback)
    return bearer_token


# ── Dependency: get_current_user ──────────────────────────────────────────────
async def get_current_user(
    request: Request,
    bearer_token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    FastAPI dependency — validates JWT (cookie or Bearer) and returns the User.

    Reads the token from:
      1. httpOnly cookie 'access_token' (browser)
      2. Authorization: Bearer header  (API clients, tests)

    Raises 401 if no token is present or token is invalid/expired.
    """
    from app.models.user import User  # local import avoids circular dependency

    token = _extract_token(request, bearer_token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    user_id_str: str = payload["sub"]

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
