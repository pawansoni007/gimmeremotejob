# service — the Python wrapper

A thin **FastAPI + SSE** service that drives **OpenHarness** in-process (Ollama-
backed) and mirrors conversations into Postgres. Managed with **uv**.

## Layout

- `app/` — FastAPI app, config, and (Step 5) the SSE endpoint.
- `openharness_runner/` — builds & drives OpenHarness's `QueryEngine` and
  forwards its `StreamEvent`s:
  - `runner.py` — `build_query_engine()` (Ollama-backed, no tools, OH's
    memory machinery off), `draft_answers(job)` (yields `StreamEvent`s),
    `event_to_dict()` (SSE-ready).
  - `prompts.py` — the system prompt (first-person candidate voice, `### Answer
    <n>` output contract, `[FILL: …]` for unknown personal facts) and the user
    prompt built from the job + questions + your profile.
  - `models.py` — `JobPayload`/`QuestionPayload`, mirroring the extension's
    camelCase `JobInfo`.
  - `smoke.py` — live check against your real Ollama (below).
- `persistence/` — conversations/jobs/answers ↔ Postgres. *(Step 6.)*
- `tests/` — pytest suite incl. a **fake Ollama** (real OpenAI-compatible SSE
  server on an ephemeral port), so the whole engine→HTTP→stream path is tested
  without a model.

## Setup

```bash
uv sync                       # create venv + install deps (incl. editable OpenHarness)
uv run pytest                 # test (no Ollama needed — uses the fake server)
uv run ruff check .           # lint
uv run ruff format .          # format
uv run uvicorn app.main:app --reload --port 8756   # the API (SSE lands in Step 5)
```

## Live smoke check (needs your Ollama)

```bash
uv run python -m openharness_runner.smoke
```

Streams drafted answers for a canned Wellfound job through the real
`QueryEngine` → your local Ollama (`minimax-m3:cloud`). Exits 0 if text
streamed. Requires Ollama running and the model available (`ollama list`),
signed in for `:cloud` models.

## Config

Copy `.env.example` → `.env` and adjust. Defaults point at a local Ollama
(`http://localhost:11434/v1`, model `minimax-m3:cloud`) and the Docker Postgres.

For personalized answers, copy `profile.example.md` → `profile.md` (gitignored)
and describe your background — the model may only claim what's in there.
