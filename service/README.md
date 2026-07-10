# service — the Python wrapper

A thin **FastAPI + SSE** service that drives **OpenHarness** in-process (Ollama-
backed) and mirrors conversations into Postgres. Managed with **uv**.

## Layout

- `app/` — FastAPI app + config. `POST /apply/stream` takes the extension's
  `JobInfo` JSON and streams the drafting run back as SSE (each event's `data`
  is one JSON object; a `{"type": "saved", "conversation_id": …}` precedes the
  final `{"type": "done"}` when persistence succeeded). `GET /conversations`
  (+`/{id}`) is the history; `POST /conversations/{id}/messages/stream` resumes
  a stored conversation with a follow-up message.
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
- `persistence/` — SQLAlchemy (async) models + repository: `jobs` (one row per
  Wellfound job, upserted), `conversations` (the full OpenHarness message list
  as JSONB — the resumable unit), `applications` (questions + answers keyed by
  question id, status). Resume = load messages → `engine.load_messages()` →
  continue. A dead database never blocks drafting — the save is skipped with a
  status event.
- `tests/` — pytest suite incl. a **fake Ollama** (real OpenAI-compatible SSE
  server on an ephemeral port), so the whole engine→HTTP→stream path is tested
  without a model; persistence tests run on throwaway SQLite files.

## Setup

```bash
docker compose up -d          # Postgres (from the repo root)
uv sync                       # create venv + install deps (incl. editable OpenHarness)
uv run pytest                 # test (no Ollama/Postgres needed — fakes + SQLite)
uv run ruff check .           # lint
uv run ruff format .          # format
uv run uvicorn app.main:app --reload --port 8756   # the API
```

Tables are created automatically on startup.

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
