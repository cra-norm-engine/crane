from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MaturityCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    scope: str = Field(min_length=1)
    period_start: date | None = None
    period_end: date | None = None

    @model_validator(mode="after")
    def valid_period(self):
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("period_end must not precede period_start")
        return self


class ResponseUpdate(BaseModel):
    score: int | None = Field(default=None, ge=1, le=5)
    rationale: str | None = None
    confidence: str | None = Field(default=None, pattern="^(low|medium|high)$")
    assessor_notes: str | None = None


class ActionUpdate(BaseModel):
    owner_user_id: UUID | None = None
    due_date: date | None = None
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    status: str | None = Field(default=None, pattern="^(open|in_progress|done|cancelled)$")
    comments: str | None = None
    completion_evidence: str | None = None


class EvidenceCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: UUID
    label: str = Field(min_length=1, max_length=255)


class MaturityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    scope: str
    status: str
    period_start: date | None
    period_end: date | None
    assessor_user_id: UUID
    reviewer_user_id: UUID | None
    submitted_at: datetime | None
    approved_at: datetime | None
    reassessment_due_date: date | None = None
    created_at: datetime


class ActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    question_code: str | None
    domain_code: str
    title: str
    priority: str
    status: str
    owner_user_id: UUID | None
    due_date: date | None
    comments: str | None
    completion_evidence: str | None


class MaturityDetail(MaturityRead):
    catalog: list[dict[str, Any]]
    responses: list[dict[str, Any]]
    actions: list[ActionRead]
    results: dict[str, Any]
    evidence_suggestions: dict[str, list[dict[str, Any]]]
    history: list[dict[str, Any]]
