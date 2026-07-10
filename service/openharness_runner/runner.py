"""Build and drive OpenHarness's QueryEngine against local Ollama.

This is the whole point of vendoring OpenHarness: we construct its QueryEngine
in-process (no CLI, no subprocess) and forward the StreamEvents it yields.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from openharness.api.openai_client import OpenAICompatibleClient
from openharness.config.settings import PermissionSettings
from openharness.engine.query_engine import QueryEngine
from openharness.engine.stream_events import (
    AssistantTextDelta,
    AssistantTurnComplete,
    ErrorEvent,
    StatusEvent,
    StreamEvent,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)
from openharness.permissions.checker import PermissionChecker
from openharness.tools.base import ToolRegistry

from app.config import settings

from .models import JobPayload
from .prompts import SYSTEM_PROMPT, build_prompt


def build_query_engine(
    *,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    max_tokens: int | None = None,
    cwd: str | Path | None = None,
) -> QueryEngine:
    """A QueryEngine wired to Ollama's OpenAI-compatible endpoint.

    Drafting answers is pure text generation, so the tool registry is empty and
    `settings=None` keeps OpenHarness's session-memory/autodream machinery off.
    """
    client = OpenAICompatibleClient(
        api_key=api_key or settings.ollama_api_key,
        base_url=base_url or settings.ollama_base_url,
        timeout=settings.ollama_timeout_seconds,
    )
    return QueryEngine(
        api_client=client,
        tool_registry=ToolRegistry(),
        permission_checker=PermissionChecker(PermissionSettings()),
        cwd=cwd or Path.cwd(),
        model=model or settings.ollama_model,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=max_tokens or settings.ollama_max_tokens,
        max_turns=2,
        settings=None,
    )


def load_profile() -> str | None:
    """The candidate's profile text, if the configured file exists."""
    path = Path(settings.applicant_profile_path)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


async def draft_answers(
    job: JobPayload,
    *,
    engine: QueryEngine | None = None,
    profile: str | None = None,
) -> AsyncIterator[StreamEvent]:
    """Run one drafting conversation for a job; yields the engine's StreamEvents.

    Pass an existing engine to continue a conversation (Step 6 resume); by
    default each call is a fresh one. The engine's `.messages` afterwards is
    what persistence stores.
    """
    engine = engine or build_query_engine()
    prompt = build_prompt(job, profile=profile if profile is not None else load_profile())
    async for event in engine.submit_message(prompt):
        yield event


def event_to_dict(event: StreamEvent) -> dict[str, Any]:
    """Flatten a StreamEvent for the SSE wire (Step 5) and logs."""
    if isinstance(event, AssistantTextDelta):
        return {"type": "text_delta", "text": event.text}
    if isinstance(event, AssistantTurnComplete):
        return {
            "type": "turn_complete",
            "text": event.message.text,
            "usage": {
                "input_tokens": event.usage.input_tokens,
                "output_tokens": event.usage.output_tokens,
            },
        }
    if isinstance(event, ToolExecutionStarted):
        return {"type": "tool_started", "tool": event.tool_name, "input": event.tool_input}
    if isinstance(event, ToolExecutionCompleted):
        return {
            "type": "tool_completed",
            "tool": event.tool_name,
            "output": event.output,
            "is_error": event.is_error,
        }
    if isinstance(event, ErrorEvent):
        return {"type": "error", "message": event.message, "recoverable": event.recoverable}
    if isinstance(event, StatusEvent):
        return {"type": "status", "message": event.message}
    # CompactProgressEvent and anything future — name + best-effort fields.
    return {"type": type(event).__name__, "detail": str(event)}
