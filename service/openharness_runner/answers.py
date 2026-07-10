"""Split drafted text into per-question answers — the `### Answer <n>` contract.

Python twin of extension/src/shared/answers.ts::splitAnswers; keep the
semantics in sync (the extension splits for display, we split for storage).
"""

from __future__ import annotations

import re

from .models import JobPayload

_HEADING = re.compile(r"^###\s*Answer\s+(\d+)\s*$", re.IGNORECASE | re.MULTILINE)


def split_answers(text: str, question_count: int) -> list[str]:
    """One entry per question; missing sections stay empty. With no headings at
    all, the whole text becomes answer 1 (model drift on a single question
    shouldn't lose the draft)."""
    answers = [""] * question_count
    headings = list(_HEADING.finditer(text))

    if not headings:
        if question_count > 0:
            answers[0] = text.strip()
        return answers

    for i, match in enumerate(headings):
        n = int(match.group(1))
        if n < 1 or n > question_count:
            continue
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        answers[n - 1] = text[start:end].strip()

    return answers


def answers_by_question_id(text: str, job: JobPayload) -> dict[str, str]:
    """Map drafted text onto the job's question ids, for storage."""
    split = split_answers(text, len(job.questions))
    return {q.id: split[i] for i, q in enumerate(job.questions)}
