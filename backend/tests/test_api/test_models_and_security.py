"""
ST-02 tests — ORM models, DB utilities, and security functions.

These tests do NOT require a live database; they verify:
1. All 6 models import and register their tables with SQLAlchemy metadata
2. Every expected column is present with the correct name
3. Password hashing and verification work correctly
4. JWT creation and decoding round-trip correctly
5. Malformed JWTs raise 401
"""
import uuid

import pytest
from fastapi import HTTPException
from jose import jwt

from app.core.config import settings
from app.core.db import Base
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import (
    Answer,
    CandidateProfile,
    DocumentEmbedding,
    InterviewSession,
    Question,
    User,
)


# ── Model registration ────────────────────────────────────────────────────────

class TestModelRegistration:
    def test_all_six_tables_registered(self):
        tables = set(Base.metadata.tables.keys())
        expected = {
            "users",
            "candidate_profiles",
            "interview_sessions",
            "questions",
            "answers",
            "document_embeddings",
        }
        assert expected == tables

    def test_users_columns(self):
        cols = {c.name for c in Base.metadata.tables["users"].columns}
        assert cols == {"id", "email", "hashed_password", "full_name", "created_at"}

    def test_candidate_profiles_columns(self):
        cols = {c.name for c in Base.metadata.tables["candidate_profiles"].columns}
        assert cols == {
            "id", "user_id", "job_role", "experience_level",
            "skills", "education", "experience", "projects",
            "resume_text", "resume_filename", "resume_parsed", "updated_at",
        }

    def test_interview_sessions_columns(self):
        cols = {c.name for c in Base.metadata.tables["interview_sessions"].columns}
        assert cols == {
            "id", "user_id", "interview_type", "job_role", "experience_level",
            "status", "total_score", "question_count", "current_question_index",
            "pipeline_context", "started_at", "completed_at",
        }

    def test_questions_columns(self):
        cols = {c.name for c in Base.metadata.tables["questions"].columns}
        assert cols == {
            "id", "session_id", "sequence_number", "question_text",
            "question_type", "difficulty", "model_answer", "rag_sources", "created_at",
        }

    def test_answers_columns(self):
        cols = {c.name for c in Base.metadata.tables["answers"].columns}
        assert cols == {
            "id", "question_id", "session_id", "answer_text",
            "quick_score", "accuracy_score", "relevance_score",
            "clarity_score", "completeness_score", "total_score",
            "feedback_text", "improvement_tip", "submitted_at",
        }

    def test_document_embeddings_columns(self):
        cols = {c.name for c in Base.metadata.tables["document_embeddings"].columns}
        assert cols == {
            "id", "source_file", "chunk_index", "chunk_text",
            "embedding", "metadata", "created_at",
        }

    def test_users_email_unique_constraint(self):
        """SQLAlchemy declares unique via column-level unique=True, which creates a
        UniqueConstraint with the same name as the index. Check either the constraint
        set or the index set for uniqueness on 'email'."""
        table = Base.metadata.tables["users"]
        # column-level unique=True creates an implicit UniqueConstraint
        email_col = table.c["email"]
        assert email_col.unique is True

    def test_candidate_profiles_user_id_unique(self):
        table = Base.metadata.tables["candidate_profiles"]
        user_id_col = table.c["user_id"]
        assert user_id_col.unique is True

    def test_document_embedding_vector_dimension(self):
        from app.models.document_embedding import EMBEDDING_DIM
        assert EMBEDDING_DIM == 1536

    def test_model_repr_user(self):
        """Test repr by inspecting the format string directly."""
        import re
        repr_str = User.__repr__
        # Verify the repr template references id and email
        source = repr_str.__code__.co_consts
        assert any("email" in str(s) for s in source if s is not None)

    def test_model_repr_document_embedding(self):
        repr_str = DocumentEmbedding.__repr__
        source = repr_str.__code__.co_consts
        assert any("source" in str(s) for s in source if s is not None)


# ── Password hashing ──────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mysecret")
        assert hashed != "mysecret"
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("correct-horse-battery-staple", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct-horse-battery-staple")
        assert verify_password("wrong-password", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses random salt — same input must not produce same hash."""
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2


# ── JWT ───────────────────────────────────────────────────────────────────────

class TestJWT:
    def test_token_round_trip(self):
        user_id = str(uuid.uuid4())
        token = create_access_token({"sub": user_id})
        payload = decode_token(token)
        assert payload["sub"] == user_id

    def test_token_contains_expiry(self):
        token = create_access_token({"sub": "user-123"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_token("not-a-valid-token")
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises_401(self):
        token = create_access_token({"sub": "user-abc"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException) as exc_info:
            decode_token(tampered)
        assert exc_info.value.status_code == 401

    def test_token_missing_sub_raises_401(self):
        # Craft a token with no 'sub' field
        token = jwt.encode({"data": "no-sub"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401
