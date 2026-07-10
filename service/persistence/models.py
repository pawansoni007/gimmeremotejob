"""ORM models: jobs, conversations, applications.

JSON columns are JSONB on Postgres and plain JSON elsewhere (tests run on
SQLite), so the schema stays dialect-agnostic.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Job(Base):
    """A Wellfound job we've drafted for at least once."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    wellfound_job_id: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    company_name: Mapped[str] = mapped_column(Text)
    company_slug: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    #: The full JobPayload as the extension sent it (camelCase keys).
    payload: Mapped[dict] = mapped_column(JsonType)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    conversations: Mapped[list[Conversation]] = relationship(back_populates="job")


class Conversation(Base):
    """One OpenHarness conversation — the unit that can be resumed."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), index=True)
    model: Mapped[str] = mapped_column(Text)
    #: Full ConversationMessage list (pydantic model_dump), enough to rebuild
    #: a QueryEngine via load_messages().
    messages: Mapped[list] = mapped_column(JsonType)
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    job: Mapped[Job] = relationship(back_populates="conversations")
    application: Mapped[Application | None] = relationship(back_populates="conversation")


class Application(Base):
    """The drafted answers for one conversation's Apply questions."""

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id"), unique=True)
    #: The questions as asked (QuestionPayload dicts, camelCase).
    questions: Mapped[list] = mapped_column(JsonType)
    #: question id -> drafted answer text.
    answers: Mapped[dict] = mapped_column(JsonType)
    status: Mapped[str] = mapped_column(String(32), default="drafted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    conversation: Mapped[Conversation] = relationship(back_populates="application")
