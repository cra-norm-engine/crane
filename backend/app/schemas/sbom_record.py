from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SbomFormat


class SbomRecordBase(BaseModel):
    product_release_id: UUID
    format: SbomFormat = SbomFormat.cyclonedx
    spec_version: str | None = Field(default=None, max_length=50)
    components_json: list[dict[str, Any]] = Field(default_factory=list)
    component_count: int | None = Field(default=None, ge=0)
    file_name: str | None = Field(default=None, max_length=500)
    tool_name: str | None = Field(default=None, max_length=255)
    tool_version: str | None = Field(default=None, max_length=100)
    generated_at: datetime | None = None
    notes: str | None = None
    # Analysis fields — populated by sbom-tools on upload or re-analysis.
    sbom_content: str | None = None
    quality_score: int | None = Field(default=None, ge=0, le=100)
    analysis_findings: dict[str, Any] | None = None


class SbomRecordCreate(SbomRecordBase):
    pass


class SbomRecordUpdate(BaseModel):
    format: SbomFormat | None = None
    spec_version: str | None = Field(default=None, max_length=50)
    components_json: list[dict[str, Any]] | None = None
    component_count: int | None = Field(default=None, ge=0)
    file_name: str | None = Field(default=None, max_length=500)
    tool_name: str | None = Field(default=None, max_length=255)
    tool_version: str | None = Field(default=None, max_length=100)
    generated_at: datetime | None = None
    notes: str | None = None


class SbomRecordRead(SbomRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
