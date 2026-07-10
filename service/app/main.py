"""FastAPI entry point.

POST /apply/stream is the one real endpoint: the extension sends the job it
read (with the Apply questions) and gets the agent's StreamEvents back as SSE.
"""

from __future__ import annotations

import json
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from openharness_runner import JobPayload, build_query_engine, draft_answers, event_to_dict

from .config import settings

log = logging.getLogger(__name__)

app = FastAPI(title="gimmeremotejob service", version="0.1.0")

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


@app.post("/apply/stream")
async def apply_stream(job: JobPayload) -> EventSourceResponse:
    """Draft answers for the job's Apply questions, streamed as SSE.

    Every event's `data` is one JSON object (see openharness_runner.event_to_dict);
    the stream ends with {"type": "done"} unless a fatal error was sent instead.
    """

    async def events():
        engine = build_query_engine()
        try:
            async for event in draft_answers(job, engine=engine):
                yield {"data": json.dumps(event_to_dict(event))}
        except Exception as exc:  # surface as an event — the SSE status is already 200
            log.exception("drafting failed for job %s", job.job_id)
            yield {"data": json.dumps({"type": "error", "message": str(exc), "recoverable": False})}
        else:
            yield {"data": json.dumps({"type": "done"})}
        # TODO(Step 6): persist engine.messages (the full conversation) to Postgres here.

    return EventSourceResponse(events())
