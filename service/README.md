# service — the Python wrapper

A thin **FastAPI + SSE** service that drives **OpenHarness** in-process (Ollama-
backed) and mirrors conversations into Postgres. Managed with **uv**.

## Layout

- `app/` — FastAPI app, config, and (later) the SSE endpoint.
- `openharness_runner/` — builds & drives OpenHarness's `QueryEngine`, forwards
  its `StreamEvent`s. *(Wired up in Step 4–5.)*
- `persistence/` — conversations/jobs/answers ↔ Postgres. *(Step 6.)*

## Setup (once OpenHarness is cloned into `../third_party/OpenHarness`)

```bash
uv sync                       # create venv + install deps (incl. editable OpenHarness)
uv run uvicorn app.main:app --reload --port 8756
uv run ruff check .           # lint
uv run ruff format .          # format
```

## Config

Copy `.env.example` → `.env` and adjust. Defaults point at a local Ollama
(`http://localhost:11434/v1`, model `minimax-m3:cloud`) and the Docker Postgres.
