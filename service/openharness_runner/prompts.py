"""Prompt construction for drafting Apply-form answers."""

from __future__ import annotations

from .models import JobPayload

# Keep the description bounded so a bloated JD can't blow up the context.
MAX_DESCRIPTION_CHARS = 6000

SYSTEM_PROMPT = """\
You are Apply Assistant. You draft a job applicant's answers to the screening
questions on a job application, writing AS the candidate, in first person.

Rules:
- Ground every claim in the CANDIDATE PROFILE and the JOB POSTING. Never invent
  experience, employers, numbers, or names. If the profile is missing a fact you
  need, write a bracketed placeholder instead, e.g. [FILL: years of Python].
- Be specific and direct. Mirror the job's own priorities (its stack, its
  product, its stated needs) rather than praising the company generically.
- No clichés ("I'm passionate about...", "I'm a perfect fit"), no flattery
  padding, no restating the question.
- Long answers ("textarea"): one tight paragraph, roughly 60-150 words.
  Short answers ("input"): one or two sentences.
- Write plain text: no markdown emphasis, no bullet lists inside answers.

Output format — exactly this, nothing else:
For each question, in order, output a heading line `### Answer <n>` followed by
the answer text. No preamble, no closing remarks.
"""


def _field_lines(job: JobPayload) -> list[str]:
    lines: list[str] = []
    if job.compensation:
        lines.append(f"Compensation: {job.compensation}")
    if job.location:
        lines.append(f"Location: {job.location}")
    if job.experience:
        lines.append(f"Experience asked: {job.experience}")
    if job.job_type:
        lines.append(f"Type: {job.job_type}")
    for label, value in job.fields.items():
        lines.append(f"{label}: {value}")
    if job.skills:
        lines.append(f"Skills: {', '.join(job.skills)}")
    return lines


def build_prompt(job: JobPayload, *, profile: str | None) -> str:
    """One user message carrying the posting, the profile, and the questions."""
    company = job.company
    header = f"{job.title} at {company.name}"
    if company.tagline:
        header += f" — {company.tagline}"

    description = job.description.strip()
    if len(description) > MAX_DESCRIPTION_CHARS:
        description = description[:MAX_DESCRIPTION_CHARS] + "\n[...description truncated]"

    question_lines = []
    for i, q in enumerate(job.questions, start=1):
        kind = "long answer" if q.kind == "textarea" else "short answer"
        line = f"{i}. [{kind}] {q.question}"
        if q.current_value.strip():
            line += f'\n   (candidate already started: "{q.current_value.strip()}")'
        question_lines.append(line)

    parts = [
        "# JOB POSTING",
        header,
        *_field_lines(job),
        "",
        "## Description",
        description or "(no description captured)",
        "",
        "# CANDIDATE PROFILE",
        profile.strip()
        if profile and profile.strip()
        else "(none provided — use placeholders for personal facts)",
        "",
        f"# SCREENING QUESTIONS ({len(job.questions)})",
        *question_lines,
        "",
        "Draft the answers now, following the output format exactly.",
    ]
    return "\n".join(parts)
