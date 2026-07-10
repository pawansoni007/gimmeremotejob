"""FastAPI entry point.

POST /apply/stream drafts answers for a job and persists the conversation;
GET /conversations (+/{id}) is the history; POST /conversations/{id}/messages/stream
resumes a stored conversation with a follow-up message.
"""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openharness.engine.messages import ConversationMessage
from openharness.engine.query_engine import QueryEngine
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

import persistence
from openharness_runner import (
    JobPayload,
    answers_by_question_id,
    build_query_engine,
    draft_answers,
    event_to_dict,
    split_answers,
)

from .config import settings

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # A dead database must not block drafting — persistence degrades gracefully.
    try:
        await persistence.create_tables()
    except Exception:
        log.exception("database unavailable at startup — running without persistence")
    yield
    await persistence.dispose()


app = FastAPI(title="gimmeremotejob service", version="0.1.0", lifespan=lifespan)

# The extension (a chrome-extension:// origin) calls us; allow it broadly for local dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": settings.ollama_model}


def _dump_messages(engine: QueryEngine) -> list[dict]:
    return [m.model_dump(mode="json") for m in engine.messages]


def _sse(data: dict) -> dict[str, str]:
    return {"data": json.dumps(data)}


@app.post("/apply/stream")
async def apply_stream(job: JobPayload) -> EventSourceResponse:
    """Draft answers for the job's Apply questions, streamed as SSE.

    Every event's `data` is one JSON object (see openharness_runner.event_to_dict).
    On success a {"type": "saved", "conversation_id": ...} event precedes the
    final {"type": "done"} — unless the database is down, which only costs the
    save, not the draft.
    """

    async def events():
        engine = build_query_engine()
        final_text = ""
        try:
            async for event in draft_answers(job, engine=engine):
                data = event_to_dict(event)
                if data["type"] == "turn_complete":
                    final_text = data["text"]
                yield _sse(data)
        except Exception as exc:  # surface as an event — the SSE status is already 200
            log.exception("drafting failed for job %s", job.job_id)
            yield _sse({"type": "error", "message": str(exc), "recoverable": False})
            return

        if final_text:
            try:
                async with persistence.session_factory()() as session:
                    conversation = await persistence.record_draft_run(
                        session,
                        payload=job,
                        model=engine.model,
                        messages=_dump_messages(engine),
                        input_tokens=engine.total_usage.input_tokens,
                        output_tokens=engine.total_usage.output_tokens,
                        answers=answers_by_question_id(final_text, job),
                    )
                yield _sse({"type": "saved", "conversation_id": str(conversation.id)})
            except Exception as exc:
                log.exception("could not persist draft for job %s", job.job_id)
                yield _sse({"type": "status", "message": f"draft not saved: {exc}"})
        yield _sse({"type": "done"})

    return EventSourceResponse(events())


@app.get("/conversations")
async def conversations_index() -> list[dict]:
    async with persistence.session_factory()() as session:
        return await persistence.list_conversations(session)


@app.get("/conversations/{conversation_id}")
async def conversation_detail(conversation_id: uuid.UUID) -> dict:
    async with persistence.session_factory()() as session:
        conversation = await persistence.get_conversation(session, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="no such conversation")
        application = conversation.application
        return {
            "id": str(conversation.id),
            "model": conversation.model,
            "job": conversation.job.payload,
            "questions": application.questions if application else [],
            "answers": application.answers if application else {},
            "status": application.status if application else "drafted",
            "messages": [
                {"role": m.get("role"), "text": _message_text(m)} for m in conversation.messages
            ],
            "updatedAt": conversation.updated_at.isoformat(),
        }


def _message_text(message: dict) -> str:
    return "".join(
        block.get("text", "")
        for block in message.get("content", [])
        if isinstance(block, dict) and block.get("type") == "text"
    )


class ResumeBody(BaseModel):
    message: str


@app.post("/conversations/{conversation_id}/messages/stream")
async def resume_stream(conversation_id: uuid.UUID, body: ResumeBody) -> EventSourceResponse:
    """Continue a stored conversation: seed a fresh engine with its messages,
    submit the follow-up, stream, and fold the new turns back into the row."""
    async with persistence.session_factory()() as session:
        conversation = await persistence.get_conversation(session, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="no such conversation")
        stored_messages = list(conversation.messages)
        question_payloads = conversation.application.questions if conversation.application else []

    async def events():
        engine = build_query_engine()
        engine.load_messages([ConversationMessage.model_validate(m) for m in stored_messages])
        final_text = ""
        try:
            async for event in engine.submit_message(body.message):
                data = event_to_dict(event)
                if data["type"] == "turn_complete":
                    final_text = data["text"]
                yield _sse(data)
        except Exception as exc:
            log.exception("resume failed for conversation %s", conversation_id)
            yield _sse({"type": "error", "message": str(exc), "recoverable": False})
            return

        if final_text:
            # Only re-map answers when the model actually re-drafted them.
            answers_update: dict[str, str] | None = None
            if question_payloads and "### Answer" in final_text:
                split = split_answers(final_text, len(question_payloads))
                answers_update = {
                    q["id"]: split[i] for i, q in enumerate(question_payloads) if split[i]
                }
            try:
                async with persistence.session_factory()() as session:
                    fresh = await persistence.get_conversation(session, conversation_id)
                    if fresh is not None:
                        await persistence.update_after_resume(
                            session,
                            fresh,
                            messages=_dump_messages(engine),
                            input_tokens=engine.total_usage.input_tokens,
                            output_tokens=engine.total_usage.output_tokens,
                            answers_update=answers_update,
                        )
                yield _sse({"type": "saved", "conversation_id": str(conversation_id)})
            except Exception as exc:
                log.exception("could not persist resume for %s", conversation_id)
                yield _sse({"type": "status", "message": f"turn not saved: {exc}"})
        yield _sse({"type": "done"})

    return EventSourceResponse(events())
