"""Postgres persistence: jobs, conversations (resumable), drafted answers."""

from .db import configure, create_tables, dispose, session_factory
from .models import Application, Conversation, Job
from .repository import (
    get_conversation,
    list_conversations,
    record_draft_run,
    update_after_resume,
    upsert_job,
)

__all__ = [
    "Application",
    "Conversation",
    "Job",
    "configure",
    "create_tables",
    "dispose",
    "get_conversation",
    "list_conversations",
    "record_draft_run",
    "session_factory",
    "update_after_resume",
    "upsert_job",
]
