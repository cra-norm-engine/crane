# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import date, datetime
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
    integrity_status: str | None = None
    last_verified_at: datetime | None = None
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
    retention_until: date | None = None
    legal_hold: bool = False
    legal_hold_reason: str | None = None
    is_retained: bool = False
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
    retention_until: date | None = None
    legal_hold: bool = False
    is_retained: bool = False
    latest_revision: ArtifactRevisionRead | None = None
    linked_product_ids: list[UUID] = []


class ArtifactCreateLinkRevisionRequest(BaseModel):
    artifact_revision_id: UUID


class ArtifactReviewRequest(BaseModel):
    decision: str
    rationale: str | None = Field(default=None, max_length=4000)


class LegalHoldRequest(BaseModel):
    """Place or release a legal hold on an artifact."""

    hold: bool
    reason: str | None = Field(default=None, max_length=2000)


class IntegritySweepResult(BaseModel):
    """Summary returned by the integrity-verification sweep."""

    checked: int
    verified: int = 0
    failed: int = 0
    missing: int = 0
    external: int = 0
    failed_revision_ids: list[str] = []
