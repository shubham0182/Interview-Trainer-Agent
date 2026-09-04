"""
CandidateProfile ORM model.

Table: candidate_profiles
- One profile per user (unique FK)
- skills / education / experience / projects stored as JSONB
- resume_parsed flag gates Granite-based extraction; False = extraction failed or not run
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    job_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # fresher | junior | mid | senior
    skills: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    education: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    experience: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    projects: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_parsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CandidateProfile id={self.id} user_id={self.user_id} role={self.job_role!r}>"
