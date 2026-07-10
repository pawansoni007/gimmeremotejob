"""FastAPI entry point.

Step 1: only a health check + CORS so the extension can reach us. The streaming
apply endpoint (Step 5) and persistence (Step 6) are stubbed below.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

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


# TODO(Step 5): POST /apply/stream — accept {job, questions}, build the OpenHarness
# QueryEngine (Ollama-backed), and stream StreamEvents back as SSE.
# TODO(Step 6): persist the conversation to Postgres and support resume.
