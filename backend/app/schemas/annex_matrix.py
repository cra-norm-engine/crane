# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    RequirementApplicabilityDecision,
    RequirementImplementationStatus,
    RequirementProgressStatus,
    SdlActivity,
)
from app.schemas.annex_requirement import AnnexRequirementRead
from app.schemas.artifact import ArtifactListRead
from app.schemas.requirement_mapping import RequirementMappingRead
from app.schemas.risk_item import RiskItemSummaryRead


class RequirementMatrixMappingRead(RequirementMappingRead):
    model_config = ConfigDict(from_attributes=True)

    risk_item: RiskItemSummaryRead | None = None
    artifacts: list[ArtifactListRead] = []


class ProductRequirementMatrixRowRead(BaseModel):
    annex_requirement: AnnexRequirementRead
    artifact_traceability_available: bool = True
    applicability_decision: RequirementApplicabilityDecision
    applicability_rationale: str | None = None
    mapping_ids: list[UUID]
    trace_records: list[RequirementMatrixMappingRead]
    risk_items: list[RiskItemSummaryRead]
    artifacts: list[ArtifactListRead]
    engineering_requirement_refs: list[str]
    sdl_activities: list[SdlActivity]
    notes: list[str]
    overall_status: RequirementImplementationStatus | None = None
    applicability: str
    traceability_strength: str
    # Per-requirement implementation progress (planned/implemented/validated).
    implementation_status: RequirementProgressStatus
    # True when the requirement is fully handled for this release (see finalize rule).
    finalized: bool


class ProductRequirementDecisionUpdate(BaseModel):
    applicability_decision: RequirementApplicabilityDecision
    rationale: str | None = None


class RequirementImplementationStatusUpdate(BaseModel):
    implementation_status: RequirementProgressStatus
