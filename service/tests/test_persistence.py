"""Persistence flow: save a draft run, list it, reload it, resume-update it.

Also proves the critical roundtrip — stored messages rebuild real
ConversationMessages that a QueryEngine accepts via load_messages().
"""

from __future__ import annotations

import uuid

import pytest
from openharness.engine.messages import ConversationMessage

import persistence
from openharness_runner import split_answers
from tests.test_runner import JOB

pytestmark = pytest.mark.usefixtures("db")

MESSAGES = [
    ConversationMessage.from_user_text("draft my answers please"),
    ConversationMessage(
        role="assistant",
        content=[{"type": "text", "text": "### Answer 1\nBecause the stack fits."}],
    ),
]


def _dump(messages: list[ConversationMessage]) -> list[dict]:
    return [m.model_dump(mode="json") for m in messages]


async def _record() -> str:
    async with persistence.session_factory()() as session:
        conversation = await persistence.record_draft_run(
            session,
            payload=JOB,
            model="fake-model",
            messages=_dump(MESSAGES),
            input_tokens=12,
            output_tokens=34,
            answers={"263701": "Because the stack fits."},
        )
        return str(conversation.id)


async def test_record_list_get_roundtrip() -> None:
    conversation_id = await _record()

    async with persistence.session_factory()() as session:
        listed = await persistence.list_conversations(session)
        assert [c["id"] for c in listed] == [conversation_id]
        assert listed[0]["title"] == "AI-Native Fullstack SDE"
        assert listed[0]["company"] == "Bullwhip"
        assert listed[0]["status"] == "drafted"
        assert listed[0]["questionCount"] == 1

        conversation = await persistence.get_conversation(session, uuid.UUID(conversation_id))
        assert conversation is not None
        assert conversation.application.answers == {"263701": "Because the stack fits."}
        assert conversation.job.wellfound_job_id == "4230970"

        # The roundtrip that resume depends on: stored dicts -> real messages.
        restored = [ConversationMessage.model_validate(m) for m in conversation.messages]
        assert [m.role for m in restored] == ["user", "assistant"]
        assert restored[1].text == "### Answer 1\nBecause the stack fits."


async def test_same_job_twice_reuses_the_job_row() -> None:
    await _record()
    await _record()

    async with persistence.session_factory()() as session:
        listed = await persistence.list_conversations(session)
        assert len(listed) == 2

        from sqlalchemy import func, select

        from persistence.models import Job

        job_count = await session.scalar(select(func.count()).select_from(Job))
        assert job_count == 1


async def test_update_after_resume_merges_answers_and_usage() -> None:
    conversation_id = await _record()

    new_messages = _dump(
        MESSAGES
        + [
            ConversationMessage.from_user_text("make it shorter"),
            ConversationMessage(
                role="assistant",
                content=[{"type": "text", "text": "### Answer 1\nStack fits; I ship."}],
            ),
        ]
    )

    async with persistence.session_factory()() as session:
        conversation = await persistence.get_conversation(session, uuid.UUID(conversation_id))
        await persistence.update_after_resume(
            session,
            conversation,
            messages=new_messages,
            input_tokens=5,
            output_tokens=7,
            answers_update={"263701": "Stack fits; I ship."},
        )

    async with persistence.session_factory()() as session:
        conversation = await persistence.get_conversation(session, uuid.UUID(conversation_id))
        assert len(conversation.messages) == 4
        assert conversation.input_tokens == 12 + 5
        assert conversation.output_tokens == 34 + 7
        assert conversation.application.answers == {"263701": "Stack fits; I ship."}


def test_split_answers_python_twin() -> None:
    text = "### Answer 1\nFirst.\n\n### answer 2\nSecond."
    assert split_answers(text, 2) == ["First.", "Second."]
    assert split_answers("no headings here", 1) == ["no headings here"]
    assert split_answers("### Answer 9\nnope", 2) == ["", ""]
    assert split_answers("### Answer 2\nonly", 2) == ["", "only"]
