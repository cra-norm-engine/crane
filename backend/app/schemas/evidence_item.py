# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import EvidenceType
from app.schemas.common import ORMBaseModel, TimestampedRead


class EvidenceItemCreate(BaseModel):
    product_release_id: UUID | None = None
    risk_assessment_id: UUID | None = None
    requirement_mapping_id: UUID | None = None
    supplier_assessment_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    evidence_type: EvidenceType
    file_path: str | None = Field(default=None, max_length=500)
    external_url: str | None = Field(default=None, max_length=2048)
    uploaded_by_user_id: UUID


class EvidenceItemUpdate(BaseModel):
    product_release_id: UUID | None = None
    risk_assessment_id: UUID | None = None
    requirement_mapping_id: UUID | None = None
    supplier_assessment_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    evidence_type: EvidenceType | None = None
    file_path: str | None = Field(default=None, max_length=500)
    external_url: str | None = Field(default=None, max_length=2048)
    uploaded_by_user_id: UUID | None = None


class EvidenceItemRead(TimestampedRead):
    product_release_id: UUID | None
    risk_assessment_id: UUID | None
    requirement_mapping_id: UUID | None
    supplier_assessment_id: UUID | None
    title: str
    description: str | None
    evidence_type: EvidenceType
    file_path: str | None
    external_url: str | None
    uploaded_by_user_id: UUID


class EvidenceItemSummaryRead(ORMBaseModel):
    id: UUID
    title: str
    evidence_type: EvidenceType
    product_release_id: UUID | None
    risk_assessment_id: UUID | None
    requirement_mapping_id: UUID | None
    supplier_assessment_id: UUID | None
