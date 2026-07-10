"""End-to-end test of the OpenHarness wiring, minus the model.

The real QueryEngine and OpenAICompatibleClient stream from a fake
OpenAI-compatible server over real HTTP — the exact dialect Ollama speaks.
"""

from __future__ import annotations

from openharness.engine.stream_events import AssistantTextDelta, AssistantTurnComplete

from openharness_runner import (
    CompanyPayload,
    JobPayload,
    QuestionPayload,
    build_prompt,
    build_query_engine,
    draft_answers,
    event_to_dict,
)
from tests.fake_ollama import FakeOllama

JOB = JobPayload(
    job_id="4230970",
    title="AI-Native Fullstack SDE",
    company=CompanyPayload(name="Bullwhip", tagline="Analytics SaaS"),
    compensation="₹15L – ₹22.5L",
    location="Remote (India)",
    skills=["Python", "TypeScript"],
    description="Backend Python/Django, frontend TypeScript. AI-assisted development daily.",
    questions=[
        QuestionPayload(
            id="263701",
            question="What interests you about working for this company?",
            kind="textarea",
            field_name="customQuestionAnswers[263701][answer]",
            current_value="I started typing this",
        ),
    ],
)

# Includes a <think> block — minimax-m3 is a thinking model, and OpenHarness
# must strip it from the visible stream.
REPLY_PIECES = [
    "<think>mirror the job's stack</think>",
    "### Answer 1\n",
    "Bullwhip's analytics stack matches how I already work",
    " — Python services and TypeScript frontends, with AI tooling in the loop.",
]
VISIBLE_REPLY = "".join(REPLY_PIECES[1:])


async def test_draft_answers_streams_end_to_end() -> None:
    async with FakeOllama(REPLY_PIECES) as server:
        engine = build_query_engine(base_url=server.base_url, model="fake-model", api_key="x")

        events = [
            event
            async for event in draft_answers(JOB, engine=engine, profile="3y fullstack, Python+TS")
        ]

        # The visible text arrives as deltas, with the <think> block stripped.
        streamed = "".join(e.text for e in events if isinstance(e, AssistantTextDelta))
        assert streamed == VISIBLE_REPLY

        # One completed turn, carrying the fake server's usage numbers.
        completes = [e for e in events if isinstance(e, AssistantTurnComplete)]
        assert len(completes) == 1
        assert completes[0].message.text == VISIBLE_REPLY
        assert (completes[0].usage.input_tokens, completes[0].usage.output_tokens) == (12, 34)

        # The engine's history is what Step 6 persists: user prompt + assistant reply.
        assert [m.role for m in engine.messages] == ["user", "assistant"]

        # The wire request actually carried our prompt: job, profile, question,
        # the already-typed draft, and the system prompt as its own message.
        (request,) = server.requests
        assert request["model"] == "fake-model"
        assert request["messages"][0]["role"] == "system"
        assert "writing AS the candidate" in request["messages"][0]["content"]
        user_text = request["messages"][1]["content"]
        assert "AI-Native Fullstack SDE at Bullwhip — Analytics SaaS" in user_text
        assert "3y fullstack, Python+TS" in user_text
        assert "What interests you about working for this company?" in user_text
        assert 'candidate already started: "I started typing this"' in user_text


async def test_event_to_dict_shapes() -> None:
    async with FakeOllama(REPLY_PIECES) as server:
        engine = build_query_engine(base_url=server.base_url, model="fake-model", api_key="x")
        dicts = [event_to_dict(e) async for e in draft_answers(JOB, engine=engine, profile="p")]

    deltas = [d for d in dicts if d["type"] == "text_delta"]
    assert "".join(d["text"] for d in deltas) == VISIBLE_REPLY

    (complete,) = [d for d in dicts if d["type"] == "turn_complete"]
    assert complete["text"] == VISIBLE_REPLY
    assert complete["usage"] == {"input_tokens": 12, "output_tokens": 34}


def test_build_prompt_without_profile_asks_for_placeholders() -> None:
    text = build_prompt(JOB, profile=None)
    assert "(none provided — use placeholders for personal facts)" in text
    assert "# SCREENING QUESTIONS (1)" in text
