# backend/app/models/__init__.py
# Import all models so Alembic autogenerate detects them and
# so callers can do: from app.models import User, CandidateProfile, ...
from app.models.user import User  # noqa: F401
from app.models.candidate_profile import CandidateProfile  # noqa: F401
from app.models.interview_session import InterviewSession  # noqa: F401
from app.models.question import Question  # noqa: F401
from app.models.answer import Answer  # noqa: F401
from app.models.document_embedding import DocumentEmbedding  # noqa: F401
