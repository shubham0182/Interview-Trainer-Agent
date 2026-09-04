"""Initial schema — all 6 tables.

Revision ID: c66ad9eac7f1
Revises: 
Create Date: 2025-01-01 00:00:00.000000

Tables created:
  - users
  - candidate_profiles
  - interview_sessions
  - questions
  - answers
  - document_embeddings  (requires pgvector extension)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c66ad9eac7f1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── candidate_profiles ────────────────────────────────────────────────────
    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_role", sa.String(255), nullable=True),
        sa.Column("experience_level", sa.String(50), nullable=True),
        sa.Column("skills", postgresql.JSONB(), nullable=True),
        sa.Column("education", postgresql.JSONB(), nullable=True),
        sa.Column("experience", postgresql.JSONB(), nullable=True),
        sa.Column("projects", postgresql.JSONB(), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("resume_filename", sa.String(255), nullable=True),
        sa.Column("resume_parsed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_candidate_profiles_user_id", "candidate_profiles", ["user_id"])

    # ── interview_sessions ────────────────────────────────────────────────────
    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interview_type", sa.String(50), nullable=False),
        sa.Column("job_role", sa.String(255), nullable=False),
        sa.Column("experience_level", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'active'")),
        sa.Column("total_score", sa.Float(), nullable=True),
        sa.Column("question_count", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column(
            "current_question_index", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("pipeline_context", postgresql.JSONB(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_sessions_user_id", "interview_sessions", ["user_id"])

    # ── questions ─────────────────────────────────────────────────────────────
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(50), nullable=False),
        sa.Column("difficulty", sa.String(50), nullable=False),
        sa.Column("model_answer", sa.Text(), nullable=True),
        sa.Column("rag_sources", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questions_session_id", "questions", ["session_id"])

    # ── answers ───────────────────────────────────────────────────────────────
    op.create_table(
        "answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("quick_score", sa.Float(), nullable=True),
        sa.Column("accuracy_score", sa.Float(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("clarity_score", sa.Float(), nullable=True),
        sa.Column("completeness_score", sa.Float(), nullable=True),
        sa.Column("total_score", sa.Float(), nullable=True),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("improvement_tip", sa.Text(), nullable=True),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_answers_question_id", "answers", ["question_id"])
    op.create_index("ix_answers_session_id", "answers", ["session_id"])

    # ── document_embeddings ───────────────────────────────────────────────────
    op.create_table(
        "document_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_file", sa.String(500), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # IVFFlat ANN index on the embedding column (created after data is loaded)
    # NOTE: Run `SET ivfflat.probes = 10;` at query time for better recall.
    # The HNSW alternative is: CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)
    # We defer index creation to after the first RAG ingest (rag_ingest.py) so that
    # IVFFlat has enough rows to set `lists` correctly.


def downgrade() -> None:
    op.drop_table("document_embeddings")
    op.drop_index("ix_answers_session_id", table_name="answers")
    op.drop_index("ix_answers_question_id", table_name="answers")
    op.drop_table("answers")
    op.drop_index("ix_questions_session_id", table_name="questions")
    op.drop_table("questions")
    op.drop_index("ix_interview_sessions_user_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")
    op.drop_index("ix_candidate_profiles_user_id", table_name="candidate_profiles")
    op.drop_table("candidate_profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
