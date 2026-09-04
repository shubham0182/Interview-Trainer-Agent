"""
Auth API routes.

Endpoints:
  POST /api/v1/auth/register  — create account, set httpOnly cookie, return user
  POST /api/v1/auth/login     — authenticate, set httpOnly cookie, return user
  GET  /api/v1/auth/me        — return authenticated user info (cookie or Bearer)
  POST /api/v1/auth/logout    — clear httpOnly cookie

Cookie-based authentication:
- Login/register set an httpOnly, SameSite=lax cookie named 'access_token'
- Cookie is NOT accessible to JavaScript (httpOnly)
- Logout clears the cookie server-side
- Bearer header fallback is supported for API clients and test suites

Route handlers are thin: validate input → call service → set cookie → return schema.
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import AUTH_COOKIE_NAME, get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_user,
    generate_token_for_user,
)

router = APIRouter()

# Cookie lifetime in seconds — matches ACCESS_TOKEN_EXPIRE_MINUTES
_COOKIE_MAX_AGE = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def _set_auth_cookie(response: Response, token: str) -> None:
    """Set the httpOnly access_token cookie on the response."""
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,                       # not accessible via document.cookie
        secure=settings.COOKIE_SECURE,       # True in production (HTTPS)
        samesite=settings.COOKIE_SAMESITE,   # "lax" prevents CSRF for most cases
        domain=settings.COOKIE_DOMAIN,       # None = browser default
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clear the httpOnly access_token cookie."""
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Create a new user, set httpOnly auth cookie, return user info.

    - Email is normalized (lowercased) by the schema.
    - Password is bcrypt-hashed; the hash is never returned.
    - Duplicate email returns 409.
    - Sets 'access_token' httpOnly cookie in response.
    """
    try:
        user = await create_user(db, payload)
    except ValueError as exc:
        if "email_taken" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )
        raise

    token = generate_token_for_user(user)
    _set_auth_cookie(response, token)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and set auth cookie",
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Validate credentials, set httpOnly auth cookie, return user info.

    - Invalid credentials always return 401 without revealing whether email exists.
    - Sets 'access_token' httpOnly cookie in response.
    """
    user = await authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = generate_token_for_user(user)
    _set_auth_cookie(response, token)
    return UserResponse.model_validate(user)


@router.get(
    "/me",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
    summary="Return the authenticated user's information",
)
async def me(
    current_user: User = Depends(get_current_user),
) -> MeResponse:
    """
    Return safe user info for the currently authenticated user.
    Reads token from httpOnly cookie or Authorization: Bearer header.
    Password hash is never included in the response.
    """
    return MeResponse.model_validate(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout — clear the auth cookie",
)
async def logout(response: Response) -> None:
    """
    Clear the httpOnly auth cookie.
    Returns 204 No Content.
    """
    _clear_auth_cookie(response)
    return None
