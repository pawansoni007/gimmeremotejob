"""Live smoke check against your real local Ollama.

    cd service && uv run python -m openharness_runner.smoke

Needs Ollama running with the configured model available (`ollama list`).
Streams the drafted answers for a canned Wellfound job to stdout.
"""

from __future__ import annotations

import asyncio
import sys

from .models import CompanyPayload, JobPayload, QuestionPayload
from .runner import build_query_engine, draft_answers, event_to_dict

CANNED_JOB = JobPayload(
    job_id="4230970",
    job_url="https://wellfound.com/jobs/4230970-ai-native-fullstack-sde",
    title="AI-Native Fullstack SDE",
    company=CompanyPayload(
        name="Bullwhip",
        slug="bullwhip-tech",
        url="https://wellfound.com/company/bullwhip-tech",
        tagline="Analytics, yield optimization & revenue growth SaaS for top commerce publishers",
    ),
    compensation="₹15L – ₹22.5L",
    location="Remote (India)",
    experience="2 years of exp",
    job_type="Full Time",
    fields={"Remote Work Policy": "Remote only", "Visa Sponsorship": "Not Available"},
    skills=[
        "Python",
        "Node.js",
        "PostgreSQL",
        "TypeScript",
        "Google Cloud Platform (GCP)",
        "Claude Code",
    ],
    description=(
        "We're looking for an AI-Native Fullstack SDE. Backend Python/Django, "
        "frontend TypeScript/Vue, GCP infrastructure. AI-assisted development "
        "(Claude Code, Cursor) is a core part of how you work."
    ),
    questions=[
        QuestionPayload(
            id="263701",
            question="What interests you about working for this company?",
            kind="textarea",
            field_name="customQuestionAnswers[263701][answer]",
        ),
    ],
)


async def main() -> int:
    engine = build_query_engine()
    print(f"model={engine.model}  endpoint={engine.api_client._client.base_url}", file=sys.stderr)
    print("--- streaming ---", file=sys.stderr)

    got_text = False
    async for event in draft_answers(CANNED_JOB, engine=engine):
        data = event_to_dict(event)
        if data["type"] == "text_delta":
            got_text = True
            print(data["text"], end="", flush=True)
        elif data["type"] == "turn_complete":
            usage = data["usage"]
            tokens = f"{usage['input_tokens']} in / {usage['output_tokens']} out"
            print(f"\n--- turn complete: {tokens} ---", file=sys.stderr)
        else:
            print(f"\n[{data['type']}] {data}", file=sys.stderr)

    print(f"--- messages in engine history: {len(engine.messages)} ---", file=sys.stderr)
    return 0 if got_text else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
