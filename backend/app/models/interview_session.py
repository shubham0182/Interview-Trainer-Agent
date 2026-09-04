"""
InterviewSession ORM model.

Table: interview_sessions
- status lifecycle: active → processing → complete | failed
- pipeline_context JSONB stores serialized AgentContext for session resumability
- current_question_index tracks progress for mid-session reconnects
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interview_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # technical | hr | behavioral | mixed
    job_role: Mapped[str] = mapped_column(String(255), nullable=False)
    experience_level: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )  # active | processing | complete | failed
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pipeline_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<InterviewSession id={self.id} type={self.interview_type!r} status={self.status!r}>"
        )
