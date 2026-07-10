"""Full loop through the API: draft -> saved -> history -> detail -> resume.

The resume assertion is the one that matters: the second model call must carry
the stored conversation, not start fresh.
"""

from __future__ import annotations

import json

import httpx
import pytest

from app.config import settings
from app.main import app
from tests.fake_ollama import FakeOllama
from tests.test_api import EXTENSION_PAYLOAD, _collect_sse_events
from tests.test_runner import REPLY_PIECES, VISIBLE_REPLY

pytestmark = pytest.mark.usefixtures("db")

RESUME_PIECES = ["### Answer 1\n", "Shorter: the stack fits and I ship fast."]


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def _draft(client: httpx.AsyncClient) -> tuple[list[dict], str]:
    async with client.stream("POST", "/apply/stream", json=EXTENSION_PAYLOAD) as response:
        events = await _collect_sse_events(response)
    (saved,) = [e for e in events if e["type"] == "saved"]
    return events, saved["conversation_id"]


async def test_draft_then_history_then_resume(monkeypatch: pytest.MonkeyPatch) -> None:
    async with FakeOllama(REPLY_PIECES) as server:
        monkeypatch.setattr(settings, "ollama_base_url", server.base_url)

        async with _client() as client:
            # 1. Draft — stream ends saved -> done.
            events, conversation_id = await _draft(client)
            assert events[-1] == {"type": "done"}

            # 2. History lists it.
            listed = (await client.get("/conversations")).json()
            assert [c["id"] for c in listed] == [conversation_id]
            assert listed[0]["company"] == "Bullwhip"

            # 3. Detail has the answers keyed by question id and the messages.
            detail = (await client.get(f"/conversations/{conversation_id}")).json()
            assert detail["answers"] == {"263701": VISIBLE_REPLY.split("\n", 1)[1]}
            assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]
            assert detail["job"]["title"] == "AI-Native Fullstack SDE"

        # 4. Resume with a follow-up; the fake model now replies the short version.
        server.reply_pieces = RESUME_PIECES
        async with _client() as client:
            async with client.stream(
                "POST",
                f"/conversations/{conversation_id}/messages/stream",
                json={"message": "make answer 1 shorter"},
            ) as response:
                events = await _collect_sse_events(response)
            assert [e["type"] for e in events][-2:] == ["saved", "done"]

            # The model call carried the stored history + the new message.
            resume_request = server.requests[-1]
            roles = [m["role"] for m in resume_request["messages"]]
            assert roles == ["system", "user", "assistant", "user"]
            assert resume_request["messages"][2]["content"] == VISIBLE_REPLY
            assert resume_request["messages"][3]["content"] == "make answer 1 shorter"

            # 5. The stored conversation grew and the answer was re-mapped.
            detail = (await client.get(f"/conversations/{conversation_id}")).json()
            assert len(detail["messages"]) == 4
            assert detail["answers"] == {"263701": "Shorter: the stack fits and I ship fast."}


async def test_resume_unknown_conversation_404s() -> None:
    async with _client() as client:
        response = await client.post(
            "/conversations/00000000-0000-0000-0000-000000000000/messages/stream",
            json={"message": "hi"},
        )
    assert response.status_code == 404


async def test_draft_still_streams_when_database_is_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import persistence

    async with FakeOllama(REPLY_PIECES) as server:
        monkeypatch.setattr(settings, "ollama_base_url", server.base_url)
        # Break persistence AFTER the app started: point it at an unreachable DB.
        persistence.configure("postgresql+psycopg://nobody:nope@127.0.0.1:9/nodb")

        async with _client() as client:
            async with client.stream("POST", "/apply/stream", json=EXTENSION_PAYLOAD) as r:
                events = await _collect_sse_events(r)

    # The draft came through; the save failure is a status note, not an error.
    deltas = "".join(e["text"] for e in events if e["type"] == "text_delta")
    assert deltas == VISIBLE_REPLY
    types = [e["type"] for e in events]
    assert "saved" not in types
    assert types[-2:] == ["status", "done"]
    assert json.dumps(events)  # everything stayed JSON-serializable
