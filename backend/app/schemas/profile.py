"""
Profile Pydantic v2 schemas.

CandidateProfile request and response schemas.
The response schema is an explicit allow-list that maps directly
onto the CandidateProfile ORM model columns.
"""
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Sub-object schemas ────────────────────────────────────────────────────────

class EducationEntry(BaseModel):
    """A single education entry (degree, institution, year)."""
    degree: str = Field(..., max_length=255)
    institution: str = Field(..., max_length=255)
    year: str | None = Field(default=None, max_length=10)
    field_of_study: str | None = Field(default=None, max_length=255)


class ExperienceEntry(BaseModel):
    """A work or internship experience entry."""
    title: str = Field(..., max_length=255)
    company: str = Field(..., max_length=255)
    duration: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class ProjectEntry(BaseModel):
    """A project entry."""
    name: str = Field(..., max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    technologies: list[str] = Field(default_factory=list)
    url: str | None = Field(default=None, max_length=500)


# ── Request schemas ───────────────────────────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    """
    PUT /api/v1/profiles/me

    All fields optional so the client can do partial updates.
    """
    job_role: str | None = Field(default=None, max_length=255)
    experience_level: str | None = Field(
        default=None,
        pattern="^(fresher|junior|mid|senior)$",
    )
    skills: list[str] | None = Field(default=None)
    education: list[EducationEntry] | None = Field(default=None)
    experience: list[ExperienceEntry] | None = Field(default=None)
    projects: list[ProjectEntry] | None = Field(default=None)


# ── Response schemas ──────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    """
    Safe profile representation returned to the client.
    Maps onto CandidateProfile ORM columns.
    JSONB columns may be None in the DB when newly created — coerced to [] here.
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_role: str | None
    experience_level: str | None
    skills: list[Any] = []
    education: list[Any] = []
    experience: list[Any] = []
    projects: list[Any] = []
    resume_filename: str | None
    resume_parsed: bool
    updated_at: datetime

    @field_validator("skills", "education", "experience", "projects", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v: Any) -> list:
        """JSONB columns can be None in DB if never set — return empty list."""
        return v if v is not None else []
