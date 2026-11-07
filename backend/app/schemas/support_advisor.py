from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdvisorInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class Remediation(AdvisorInput):
    component_link_id: UUID
    approach: Literal["supplier_extension", "independent_patching", "replacement", "architecture_mitigation"]
    rationale: str = Field(min_length=10, max_length=10000)
    evidence_ids: list[UUID] = Field(min_length=1, max_length=50)


class AssessmentCreate(AdvisorInput):
    context_version: str = Field(pattern=r"^[0-9a-f]{64}$")
    product_release_id: UUID
    support_start: date = Field(le=date(9994, 12, 31))
    support_end: date
    expected_use_end: date
    expected_use_basis: Literal["documented", "assumption", "estimate"] = "assumption"
    rationale: str = Field(min_length=10, max_length=20000)
    evidence_ids: list[UUID] = Field(default_factory=list, max_length=100)
    remediations: list[Remediation] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def dates(self):
        if self.support_end <= self.support_start or self.expected_use_end <= self.support_start:
            raise ValueError("Support and expected-use end must follow support start")
        links = [r.component_link_id for r in self.remediations]
        if len(set(links)) != len(links):
            raise ValueError("Only one remediation per component link")
        return self


class AssessmentReview(AdvisorInput):
    decision: Literal["approved", "returned"]
    reason: str = Field(min_length=10, max_length=20000)
