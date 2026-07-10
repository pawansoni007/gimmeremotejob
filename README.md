# gimmeremotejob — Wellfound Apply Assistant

A Chrome extension that reads the Wellfound job you're viewing and, when you open
the **Apply** form, drafts answers to the screening questions so you copy, paste,
and tweak. The "thinking" is done by **OpenHarness** (a Python port of Claude
Code) running on your **local Ollama** (`minimax-m3:cloud`), wrapped by a small
FastAPI service that streams the agent's steps into a Claude-styled side panel.
A Postgres database remembers your conversations, jobs, and answers.

> Full design & rationale live in the plan the project was built from.

## The three pieces

| Folder | What it is |
| --- | --- |
| `extension/` | Chrome extension (Manifest V3, React + TypeScript 7.0, Radix UI, core-js) |
| `service/` | Thin FastAPI + SSE wrapper that drives OpenHarness and talks to Postgres (managed with **uv**) |
| `third_party/OpenHarness/` | Plain in-repo copy of `HKUDS/OpenHarness` (the brain) — we call its functions |

Plus `docker-compose.yml` for Postgres.

## Status

Built in small steps. **Steps 1–5 are in place** — the core loop works end to
end: open a Wellfound job, the side panel shows the Apply questions and the job
the extension read; hit **Draft answers** and the service drives OpenHarness's
`QueryEngine` (in-process, against your local Ollama) and streams the draft
live into the panel, one answer per question, each with a **Copy** button.
To run it: `docker compose up -d` (not needed until Step 6),
`cd service && uv run uvicorn app.main:app --port 8756`, extension loaded
unpacked, Ollama running. See each folder's README for details.

## Toolchain (locked)

- **Python:** `uv` only (never `pip`). Lint/format with **ruff**.
- **Frontend:** React + **TypeScript 7.0** (native preview), Radix UI, core-js.
- **LLM:** local **Ollama**, model `minimax-m3:cloud` (OpenAI-compatible endpoint).
- **DB:** Postgres in Docker.

## What you'll need (to run it, once wired up)

`uv`, Node + npm, Docker, **Ollama running locally** with `minimax-m3:cloud`
available (signed in for the cloud model), Chrome (load the extension unpacked).

## Quick map of upcoming steps

1. ✅ Skeleton
2. ✅ Extension reads a Wellfound job into the side panel
3. ✅ Extension grabs the Apply questions
4. ✅ Wire up OpenHarness in-process (Ollama-backed)
5. ✅ FastAPI + SSE streaming into the panel
6. Postgres memory (save + resume conversations)
7. Polish
