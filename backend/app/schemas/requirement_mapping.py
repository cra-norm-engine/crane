from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import RequirementImplementationStatus, SdlActivity
from app.schemas.common import ORMBaseModel, TimestampedRead


class RequirementMappingCreate(BaseModel):
    risk_item_id: UUID | None = None
    annex_requirement_id: UUID
    engineering_requirement_ref: str | None = Field(default=None, max_length=255)
    sdl_activity: SdlActivity
    implementation_status: RequirementImplementationStatus = RequirementImplementationStatus.planned
    evidence_summary: str | None = None


class RequirementMappingUpdate(BaseModel):
    risk_item_id: UUID | None = None
    annex_requirement_id: UUID | None = None
    engineering_requirement_ref: str | None = Field(default=None, max_length=255)
    sdl_activity: SdlActivity | None = None
    implementation_status: RequirementImplementationStatus | None = None
    evidence_summary: str | None = None


class RequirementMappingRead(TimestampedRead):
    risk_item_id: UUID | None
    annex_requirement_id: UUID
    engineering_requirement_ref: str | None
    sdl_activity: SdlActivity
    implementation_status: RequirementImplementationStatus
    evidence_summary: str | None


class RequirementMappingSummaryRead(ORMBaseModel):
    id: UUID
    risk_item_id: UUID | None
    annex_requirement_id: UUID
    engineering_requirement_ref: str | None
    sdl_activity: SdlActivity
    implementation_status: RequirementImplementationStatus