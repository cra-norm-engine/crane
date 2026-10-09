# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import AnnexPart
from app.schemas.common import ORMBaseModel, TimestampedRead


class RequirementContributionRead(ORMBaseModel):
    essential_requirement_id: UUID
    contribution: str = Field(min_length=1)

    @field_validator("contribution")
    @classmethod
    def nonblank_contribution(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Explain which aspect of the CRA requirement this supports.")
        return value.strip()


class AnnexRequirementCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    annex_part: AnnexPart = AnnexPart.part_i
    is_active: bool = True
    source_id: UUID | None = None
    clause_reference: str | None = Field(default=None, max_length=100)
    applicability_guidance: str | None = None
    verification_guidance: str | None = None
    expected_evidence: str | None = None
    is_mandatory: bool = False
    acceptance_criteria: str | None = None
    contributions: list[RequirementContributionRead] = Field(default_factory=list, max_length=22)


class AnnexRequirementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    annex_part: AnnexPart | None = None
    is_active: bool | None = None
    clause_reference: str | None = Field(default=None, max_length=100)
    applicability_guidance: str | None = None
    verification_guidance: str | None = None
    expected_evidence: str | None = None
    is_mandatory: bool | None = None
    acceptance_criteria: str | None = None
    contributions: list[RequirementContributionRead] | None = Field(default=None, max_length=22)


class AnnexRequirementRead(TimestampedRead):
    code: str
    title: str
    description: str
    annex_part: AnnexPart
    is_active: bool
    source_id: UUID | None
    source_identifier: str
    source_title: str
    source_edition: str = ""
    clause_reference: str | None
    applicability_guidance: str | None
    verification_guidance: str | None
    expected_evidence: str | None
    revision: int
    status: str
    is_mandatory: bool
    kind: str = "essential"
    acceptance_criteria: str | None = None
    contributions: list[RequirementContributionRead] = []


class AnnexRequirementSummaryRead(ORMBaseModel):
    id: UUID
    code: str
    title: str
    annex_part: AnnexPart
    is_active: bool
