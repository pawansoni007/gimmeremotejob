"""The persistence operations the service actually performs."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from openharness_runner import JobPayload

from .models import Application, Conversation, Job


async def upsert_job(session: AsyncSession, payload: JobPayload) -> Job:
    """Find the job by its Wellfound id (fallback: url) or create it."""
    job: Job | None = None
    if payload.job_id:
        job = await session.scalar(select(Job).where(Job.wellfound_job_id == payload.job_id))
    if job is None and payload.job_url:
        job = await session.scalar(select(Job).where(Job.url == payload.job_url))

    dumped = payload.model_dump(mode="json", by_alias=True)
    if job is None:
        job = Job(
            wellfound_job_id=payload.job_id,
            title=payload.title,
            company_name=payload.company.name,
            company_slug=payload.company.slug,
            url=payload.job_url,
            payload=dumped,
        )
        session.add(job)
    else:
        # Refresh what may have changed on Wellfound's side.
        job.title = payload.title
        job.company_name = payload.company.name
        job.company_slug = payload.company.slug
        job.payload = dumped
        from .models import _now

        job.last_seen_at = _now()
    await session.flush()
    return job


async def record_draft_run(
    session: AsyncSession,
    *,
    payload: JobPayload,
    model: str,
    messages: list[dict[str, Any]],
    input_tokens: int,
    output_tokens: int,
    answers: dict[str, str],
) -> Conversation:
    """Persist one finished drafting run: job + conversation + application."""
    job = await upsert_job(session, payload)
    conversation = Conversation(
        job_id=job.id,
        model=model,
        messages=messages,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    session.add(conversation)
    await session.flush()
    session.add(
        Application(
            job_id=job.id,
            conversation_id=conversation.id,
            questions=[q.model_dump(mode="json", by_alias=True) for q in payload.questions],
            answers=answers,
        )
    )
    await session.commit()
    return conversation


async def list_conversations(session: AsyncSession) -> list[dict[str, Any]]:
    """Newest-first history for the panel's list view."""
    rows = await session.scalars(
        select(Conversation)
        .options(selectinload(Conversation.job), selectinload(Conversation.application))
        .order_by(Conversation.updated_at.desc())
    )
    return [
        {
            "id": str(c.id),
            "title": c.job.title,
            "company": c.job.company_name,
            "jobUrl": c.job.url,
            "status": c.application.status if c.application else "drafted",
            "questionCount": len(c.application.questions) if c.application else 0,
            "updatedAt": c.updated_at.isoformat(),
        }
        for c in rows
    ]


async def get_conversation(
    session: AsyncSession, conversation_id: uuid.UUID
) -> Conversation | None:
    return await session.scalar(
        select(Conversation)
        .options(selectinload(Conversation.job), selectinload(Conversation.application))
        .where(Conversation.id == conversation_id)
    )


async def update_after_resume(
    session: AsyncSession,
    conversation: Conversation,
    *,
    messages: list[dict[str, Any]],
    input_tokens: int,
    output_tokens: int,
    answers_update: dict[str, str] | None,
) -> None:
    """Fold a resumed turn back into the stored conversation."""
    conversation.messages = messages
    conversation.input_tokens += input_tokens
    conversation.output_tokens += output_tokens
    if answers_update and conversation.application:
        conversation.application.answers = {
            **conversation.application.answers,
            **answers_update,
        }
    await session.commit()
