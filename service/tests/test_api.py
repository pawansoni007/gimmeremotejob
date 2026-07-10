"""SSE endpoint test: extension-shaped JSON in, streamed events out.

Runs the real FastAPI app over ASGI with the fake Ollama behind it — the same
bytes the panel will parse.
"""

from __future__ import annotations

import json

import httpx
import pytest

from app.config import settings
from app.main import app
from tests.fake_ollama import FakeOllama
from tests.test_runner import REPLY_PIECES, VISIBLE_REPLY

# What the extension actually POSTs: camelCase, straight from JobInfo.
EXTENSION_PAYLOAD = {
    "jobId": "4230970",
    "jobUrl": "https://wellfound.com/jobs/4230970-ai-native-fullstack-sde",
    "title": "AI-Native Fullstack SDE",
    "company": {"name": "Bullwhip", "slug": "bullwhip-tech", "tagline": "Analytics SaaS"},
    "metaItems": ["₹15L – ₹22.5L", "Remote (India)"],
    "compensation": "₹15L – ₹22.5L",
    "location": "Remote (India)",
    "jobType": "Full Time",
    "fields": {"Remote Work Policy": "Remote only"},
    "skills": ["Python", "TypeScript"],
    "description": "Backend Python/Django, frontend TypeScript.",
    "questions": [
        {
            "id": "263701",
            "question": "What interests you about working for this company?",
            "kind": "textarea",
            "fieldName": "customQuestionAnswers[263701][answer]",
            "currentValue": "",
        }
    ],
}


async def _collect_sse_events(response: httpx.Response) -> list[dict]:
    events = []
    async for line in response.aiter_lines():
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:") :].strip()))
    return events


async def test_apply_stream_speaks_sse(monkeypatch: pytest.MonkeyPatch) -> None:
    async with FakeOllama(REPLY_PIECES) as server:
        monkeypatch.setattr(settings, "ollama_base_url", server.base_url)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            async with client.stream("POST", "/apply/stream", json=EXTENSION_PAYLOAD) as response:
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("text/event-stream")
                events = await _collect_sse_events(response)

    deltas = [e["text"] for e in events if e["type"] == "text_delta"]
    assert "".join(deltas) == VISIBLE_REPLY

    (complete,) = [e for e in events if e["type"] == "turn_complete"]
    assert complete["text"] == VISIBLE_REPLY

    assert events[-1] == {"type": "done"}

    # The fake model was really asked about this job.
    (request,) = server.requests
    assert "What interests you about working for this company?" in str(request["messages"])


async def test_apply_stream_surfaces_failure_as_error_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Nothing listens on this port. OpenHarness catches the connection failure
    # itself and yields an ErrorEvent, so the wire shows error -> done.
    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:9/v1")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("POST", "/apply/stream", json=EXTENSION_PAYLOAD) as response:
            events = await _collect_sse_events(response)

    assert [e["type"] for e in events] == ["error", "done"]
    assert "error" in events[0]["message"].lower()


async def test_health() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
