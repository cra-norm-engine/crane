from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ArtifactReviewDecision, ReleaseGateItemCode, ReleaseGateWorkflowStatus
from app.schemas.artifact import ArtifactRevisionRead
from app.schemas.product_release import ProductReleaseRead
from app.schemas.user import UserSummaryRead


class ReleaseGateEvidenceLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    decision: ArtifactReviewDecision
    rationale: str | None
    linked_by_user_id: UUID
    linked_by_user: UserSummaryRead | None = None
    reviewed_by_user_id: UUID | None
    reviewed_by_user: UserSummaryRead | None = None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    artifact_revision: ArtifactRevisionRead


class ReleaseGateItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: ReleaseGateItemCode | None = None
    title: str
    description: str | None
    is_required: bool
    sort_order: int
    status: ArtifactReviewDecision
    assigned_to_user_id: UUID | None = None
    due_date: datetime | None = None
    evidence_links: list[ReleaseGateEvidenceLinkRead] = []


class ReleaseGateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_release_id: UUID
    status: ReleaseGateWorkflowStatus
    submitted_at: datetime | None
    submitted_by_user_id: UUID | None
    submitted_by_user: UserSummaryRead | None = None
    approved_at: datetime | None
    approved_by_user_id: UUID | None
    approved_by_user: UserSummaryRead | None = None
    bundle_sha256: str | None = None
    bundle_generated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    items: list[ReleaseGateItemRead] = []
    required_items_count: int = 0
    accepted_items_count: int = 0
    pending_items_count: int = 0


class ReleaseGateDetailRead(BaseModel):
    release: ProductReleaseRead
    gate: ReleaseGateRead


class ReleaseGateReviewRequest(BaseModel):
    decision: ArtifactReviewDecision
    rationale: str | None = Field(default=None, max_length=4000)


class GateItemCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
