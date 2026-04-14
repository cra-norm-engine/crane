from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AuditActorRead(BaseModel):
    id: UUID | None
    full_name: str | None
    email: str | None


class AuditEventRead(BaseModel):
    id: UUID
    occurred_at: datetime
    actor: AuditActorRead
    action_type: str
    entity_type: str
    entity_id: UUID | None
    status: str
    summary: str
    entity_label: str | None = None
    product_id: UUID | None = None
    product_release_id: UUID | None = None
    details_json: dict = Field(default_factory=dict)


class AuditEventListRead(BaseModel):
    items: list[AuditEventRead]
    total: int


class AuditIntegrityIssueRead(BaseModel):
    sequence_number: int | None = None
    event_id: UUID | None = None
    reason: str


class AuditIntegrityRead(BaseModel):
    verified: bool
    total_events: int
    verified_events: int
    latest_sequence_number: int | None = None
    issues: list[AuditIntegrityIssueRead] = Field(default_factory=list)
