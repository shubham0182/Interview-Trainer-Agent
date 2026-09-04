"""
DocumentEmbedding ORM model (pgvector).

Table: document_embeddings
- embedding column uses pgvector Vector(1536) — dimension matches IBM slate-125m-english-rtrvr
- Changing embedding model requires a DB migration to update Vector dimension
- Table is TRUNCATE-then-INSERT on each ingest run (not upsert)
- metadata JSONB stores role/type/difficulty tags from knowledge_base front-matter
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.core.db import Base

# Embedding dimension — must match GRANITE_EMBEDDING_MODEL output
EMBEDDING_DIM = 1536


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_file: Mapped[str] = mapped_column(String(500), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    # Column named "doc_metadata" in Python; maps to "metadata" column in DB
    doc_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentEmbedding id={self.id} "
            f"source={self.source_file!r} chunk={self.chunk_index}>"
        )
