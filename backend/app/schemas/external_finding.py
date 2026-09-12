from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models.enums import SecurityUpdateSeverity, VexStatus

Source = Annotated[str, Field(min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9._-]*$")]
Identifier = Annotated[str, Field(min_length=1, max_length=100)]


class ExternalAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vex_status: VexStatus
    rationale: str = Field(min_length=1, max_length=10000)
    assessed_at: AwareDatetime
    assessed_by: str | None = Field(default=None, max_length=255)
    operational_conditions: str | None = Field(default=None, max_length=10000)


class ExternalFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    external_id: str = Field(min_length=1, max_length=500)
    source_updated_at: AwareDatetime
    component_name: str = Field(min_length=1, max_length=500)
    component_version: str | None = Field(default=None, max_length=200)
    component_purl: str | None = Field(default=None, max_length=1000, pattern=r"^pkg:")
    vulnerability_id: Identifier
    aliases: list[Identifier] = Field(default_factory=list, max_length=50)
    summary: str | None = Field(default=None, max_length=20000)
    severity: SecurityUpdateSeverity | None = None
    cvss_score: float | None = Field(default=None, ge=0, le=10)
    cvss_vector: str | None = Field(default=None, max_length=200)
    epss_score: float | None = Field(default=None, ge=0, le=1)
    epss_percentile: float | None = Field(default=None, ge=0, le=1)
    source_url: HttpUrl | None = None
    suppressed: bool = False
    source_analysis_state: str | None = Field(default=None, max_length=100)
    assessment: ExternalAssessment | None = None


class ExternalFindingsImport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Source
    findings: list[ExternalFinding] = Field(max_length=500)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [item.external_id for item in self.findings]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate external_id in batch")
        return self


class IngestionKeyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    sbom_record_id: UUID
    source: Source
    expires_in_days: int = Field(default=90, ge=1, le=365)


class IngestionKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    sbom_record_id: UUID
    source: str
    expires_at: AwareDatetime
    revoked_at: AwareDatetime | None


class IngestionKeyIssued(IngestionKeyRead):
    token: str


class ImportResult(BaseModel):
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    stale: int = 0
    assessment_conflicts: list[str] = Field(default_factory=list)
