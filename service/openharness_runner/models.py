"""Payload models — the extension's JobInfo, as the service receives it.

The extension sends camelCase JSON (see extension/src/shared/types.ts); aliases
map it to snake_case here. Everything except the title is optional so a partial
read on Wellfound's side never blocks drafting.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class QuestionPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    question: str
    kind: Literal["textarea", "input"] = "textarea"
    field_name: str = Field("", alias="fieldName")
    current_value: str = Field("", alias="currentValue")


class CompanyPayload(BaseModel):
    name: str = "Unknown company"
    slug: str | None = None
    url: str | None = None
    tagline: str | None = None


class JobPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    job_id: str | None = Field(None, alias="jobId")
    job_url: str | None = Field(None, alias="jobUrl")
    title: str
    company: CompanyPayload = Field(default_factory=CompanyPayload)
    meta_items: list[str] = Field(default_factory=list, alias="metaItems")
    compensation: str | None = None
    location: str | None = None
    experience: str | None = None
    job_type: str | None = Field(None, alias="jobType")
    fields: dict[str, str] = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    description: str = ""
    questions: list[QuestionPayload] = Field(default_factory=list)
