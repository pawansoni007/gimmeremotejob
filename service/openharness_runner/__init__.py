"""Builds and drives OpenHarness's QueryEngine, forwarding its StreamEvents.

Usage (Step 5 wires this behind FastAPI + SSE):

    from openharness_runner import JobPayload, draft_answers, event_to_dict

    async for event in draft_answers(job):
        sse.send(event_to_dict(event))
"""

from .answers import answers_by_question_id, split_answers
from .models import CompanyPayload, JobPayload, QuestionPayload
from .prompts import SYSTEM_PROMPT, build_prompt
from .runner import build_query_engine, draft_answers, event_to_dict, load_profile

__all__ = [
    "CompanyPayload",
    "JobPayload",
    "QuestionPayload",
    "SYSTEM_PROMPT",
    "answers_by_question_id",
    "build_prompt",
    "build_query_engine",
    "draft_answers",
    "event_to_dict",
    "load_profile",
    "split_answers",
]
