from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ArtifactSourceType, EvidenceType
from app.schemas.user import UserSummaryRead


class ArtifactRevisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    artifact_id: UUID
    revision_number: int
    source_type: ArtifactSourceType
    original_filename: str | None
    content_type: str | None
    file_size_bytes: int | None
    sha256: str | None
    storage_path: str | None
    external_url: str | None
    change_summary: str | None
    uploaded_by_user_id: UUID
    uploaded_by_user: UserSummaryRead | None = None
    created_at: datetime
    updated_at: datetime


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    artifact_type: EvidenceType
    created_by_user_id: UUID
    created_by_user: UserSummaryRead | None = None
    created_at: datetime
    updated_at: datetime
    revisions: list[ArtifactRevisionRead] = []
    linked_product_ids: list[UUID] = []


class ArtifactListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    artifact_type: EvidenceType
    created_by_user_id: UUID
    created_by_user: UserSummaryRead | None = None
    created_at: datetime
    updated_at: datetime
    latest_revision: ArtifactRevisionRead | None = None
    linked_product_ids: list[UUID] = []


class ArtifactCreateLinkRevisionRequest(BaseModel):
    artifact_revision_id: UUID


class ArtifactReviewRequest(BaseModel):
    decision: str
    rationale: str | None = Field(default=None, max_length=4000)
