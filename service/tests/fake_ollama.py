"""A fake Ollama: a minimal OpenAI-compatible /chat/completions SSE server.

Speaks exactly the dialect Ollama's OpenAI endpoint speaks, so the full real
path — QueryEngine -> OpenAICompatibleClient (AsyncOpenAI) -> HTTP -> SSE
chunks -> StreamEvents — is exercised without a model.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse


def _chunk(delta: dict[str, Any], finish_reason: str | None = None) -> str:
    payload = {
        "id": "chatcmpl-fake",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": "fake",
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }
    return f"data: {json.dumps(payload)}\n\n"


def _usage_chunk(prompt_tokens: int, completion_tokens: int) -> str:
    payload = {
        "id": "chatcmpl-fake",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": "fake",
        "choices": [],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
    return f"data: {json.dumps(payload)}\n\n"


class FakeOllama:
    """Serves scripted completion chunks; records every request it gets."""

    def __init__(self, reply_pieces: list[str], usage: tuple[int, int] = (12, 34)) -> None:
        self.reply_pieces = reply_pieces
        self.usage = usage
        self.requests: list[dict[str, Any]] = []
        self._server: uvicorn.Server | None = None
        self._task: asyncio.Task | None = None
        self.port: int | None = None

        app = FastAPI()

        @app.post("/v1/chat/completions")
        async def completions(request: Request) -> StreamingResponse:
            self.requests.append(await request.json())

            async def stream():
                yield _chunk({"role": "assistant"})
                for piece in self.reply_pieces:
                    yield _chunk({"content": piece})
                yield _chunk({}, finish_reason="stop")
                yield _usage_chunk(*self.usage)
                yield "data: [DONE]\n\n"

            return StreamingResponse(stream(), media_type="text/event-stream")

        self._app = app

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/v1"

    async def __aenter__(self) -> FakeOllama:
        config = uvicorn.Config(self._app, host="127.0.0.1", port=0, log_level="error")
        self._server = uvicorn.Server(config)
        self._task = asyncio.create_task(self._server.serve())
        while not self._server.started:
            await asyncio.sleep(0.01)
        self.port = self._server.servers[0].sockets[0].getsockname()[1]
        return self

    async def __aexit__(self, *exc: object) -> None:
        assert self._server is not None and self._task is not None
        self._server.should_exit = True
        await self._task
