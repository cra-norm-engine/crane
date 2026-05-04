from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AdvisoryStatus, SecurityUpdateSeverity


class SecurityAdvisoryBase(BaseModel):
    product_release_id: UUID
    advisory_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1)
    summary: str | None = None
    severity: SecurityUpdateSeverity | None = None
    status: AdvisoryStatus = AdvisoryStatus.draft
    cve_ids_json: list[str] = Field(default_factory=list)
    affected_versions_json: list[str] | dict[str, Any] = Field(default_factory=list)
    fixed_in_versions_json: list[str] = Field(default_factory=list)
    workaround: str | None = None
    remediation_steps: str | None = None
    # Gap 7 — embargo end date; advisory stays internal until this date passes.
    embargo_until: datetime | None = None
    published_at: datetime | None = None


class SecurityAdvisoryCreate(SecurityAdvisoryBase):
    pass


class SecurityAdvisoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    summary: str | None = None
    severity: SecurityUpdateSeverity | None = None
    status: AdvisoryStatus | None = None
    cve_ids_json: list[str] | None = None
    affected_versions_json: list[str] | dict[str, Any] | None = None
    fixed_in_versions_json: list[str] | None = None
    workaround: str | None = None
    remediation_steps: str | None = None
    embargo_until: datetime | None = None
    published_at: datetime | None = None


class SecurityAdvisoryRead(SecurityAdvisoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
