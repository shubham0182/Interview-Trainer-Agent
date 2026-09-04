"""
Auth Pydantic v2 schemas.

Design rules:
- Request schemas validate/normalize input (email lowercased, password min-length enforced).
- Response schemas are explicit allow-lists — hashed_password is NEVER included.
- UserResponse is the canonical safe representation of a User returned to clients.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ── Request schemas ───────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """POST /api/v1/auth/register"""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Lowercase and strip whitespace so 'User@Example.COM' == 'user@example.com'."""
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Enforce minimal password complexity (at least one non-space character group)."""
        if v.strip() == "":
            raise ValueError("Password must not be blank")
        return v


class LoginRequest(BaseModel):
    """POST /api/v1/auth/login"""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


# ── Response schemas ──────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Safe user representation — never includes hashed_password."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    created_at: datetime


class MeResponse(BaseModel):
    """Response for GET /api/v1/auth/me"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    created_at: datetime
