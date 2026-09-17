import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
    Computed,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    page_start: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    page_end: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(384),
        nullable=False,
    )

    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', coalesce(content, ''))",
            persisted=True,
        ),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped["Document"] = relationship(
        back_populates="chunks",
    )

    citations: Mapped[list["MessageCitation"]] = relationship(
        back_populates="chunk",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunks_document_index",
        ),
        Index(
            "ix_document_chunks_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
    )
