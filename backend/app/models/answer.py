"""
Answer ORM model.

Table: answers
- quick_score: set immediately when the candidate submits (live session, simple Granite call)
- accuracy/relevance/clarity/completeness scores: set by AnswerEvaluationAgent (full pipeline)
- total_score = sum of 4 dimension scores (0–100)
- feedback_text + improvement_tip: set by FeedbackScoringAgent
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Immediate scoring (set during live session) ────────────────────────────
    quick_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── 4-dimension scores (set by AnswerEvaluationAgent) ─────────────────────
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)     # 0–25
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)    # 0–25
    clarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)      # 0–25
    completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0–25
    total_score: Mapped[float | None] = mapped_column(Float, nullable=True)        # 0–100

    # ── Feedback (set by FeedbackScoringAgent) ─────────────────────────────────
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvement_tip: Mapped[str | None] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Answer id={self.id} question_id={self.question_id} quick_score={self.quick_score}>"
