"""
Question ORM model.

Table: questions
- sequence_number: 1–10 within a session
- model_answer: Granite-generated ideal answer (shown in final report, NOT during session)
- rag_sources: JSONB list of document_embedding chunk IDs used in generation (auditability)
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–10
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # technical | hr | behavioral
    difficulty: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # easy | medium | hard
    model_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    rag_sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Question id={self.id} seq={self.sequence_number} "
            f"type={self.question_type!r} difficulty={self.difficulty!r}>"
        )
