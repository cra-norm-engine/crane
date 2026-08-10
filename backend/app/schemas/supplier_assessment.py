from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (AssessmentResponseDecision, ComponentCriticality, ComponentType,
    EvidenceReviewStatus, RiskLevel, SupplierAssessmentStatus, SupplierFindingStatus, SupplierStatus, SupplierType)
from app.schemas.common import TimestampedRead


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    supplier_type: SupplierType
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    security_contact: str | None = Field(default=None, max_length=320)
    website: str | None = Field(default=None, max_length=2048)
    status: SupplierStatus = SupplierStatus.active
    owner_user_id: UUID | None = None
    notes: str | None = None


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    supplier_type: SupplierType | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    security_contact: str | None = Field(default=None, max_length=320)
    website: str | None = Field(default=None, max_length=2048)
    status: SupplierStatus | None = None
    owner_user_id: UUID | None = None
    notes: str | None = None


class SupplierRead(TimestampedRead):
    name: str; supplier_type: str; country_code: str | None; security_contact: str | None
    website: str | None; status: str; owner_user_id: UUID | None; notes: str | None


class ComponentCreate(BaseModel):
    supplier_id: UUID
    name: str = Field(min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=100)
    component_type: ComponentType
    purl: str | None = Field(default=None, max_length=1024)
    cpe: str | None = Field(default=None, max_length=1024)
    part_number: str | None = Field(default=None, max_length=255)
    support_end_date: date | None = None
    update_channel: str | None = Field(default=None, max_length=2048)
    notes: str | None = None


class ComponentRead(TimestampedRead):
    supplier_id: UUID; name: str; version: str | None; component_type: str; purl: str | None
    cpe: str | None; part_number: str | None; support_end_date: date | None; update_channel: str | None; notes: str | None


class ComponentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=100)
    component_type: ComponentType | None = None
    purl: str | None = Field(default=None, max_length=1024)
    cpe: str | None = Field(default=None, max_length=1024)
    part_number: str | None = Field(default=None, max_length=255)
    support_end_date: date | None = None
    update_channel: str | None = Field(default=None, max_length=2048)
    notes: str | None = None


class ComponentLinkCreate(BaseModel):
    product_release_id: UUID; component_id: UUID; sbom_record_id: UUID | None = None
    is_direct: bool = True; is_core_function: bool = False
    criticality: ComponentCriticality; criticality_rationale: str = Field(min_length=1); usage_context: str | None = None


class ComponentLinkUpdate(BaseModel):
    product_release_id: UUID | None = None; component_id: UUID | None = None; sbom_record_id: UUID | None = None
    is_direct: bool | None = None; is_core_function: bool | None = None
    criticality: ComponentCriticality | None = None
    criticality_rationale: str | None = Field(default=None, min_length=1)
    usage_context: str | None = None


class ComponentLinkRead(TimestampedRead):
    product_release_id: UUID; component_id: UUID; sbom_record_id: UUID | None
    is_direct: bool; is_core_function: bool; criticality: str; criticality_rationale: str; usage_context: str | None


class ComponentTraceabilityRead(ComponentLinkRead):
    supplier_id: UUID; supplier_name: str; component_name: str; component_version: str | None
    product_id: UUID; product_name: str; product_code: str; release_version: str
    sbom_file_name: str | None; assessment_id: UUID | None; assessment_status: str | None
    assessment_valid_until: date | None; reassessment_required: bool
    maintainer_notification_count: int


class ComponentVulnerabilityTraceRead(BaseModel):
    finding_id: UUID; vulnerability_report_id: UUID | None; component_id: UUID
    vulnerability_id: str; aliases: list[str]; title: str; severity: str | None
    status: str | None; cvss_score: float | None; is_known_exploited: bool
    fixed_versions: list; source_sbom_id: UUID; detected_release_id: UUID
    affected_releases: list[dict]


class AssessmentCreate(BaseModel):
    supplier_id: UUID; component_id: UUID | None = None; product_release_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255); assessment_tier: ComponentCriticality
    tier_rationale: str = Field(min_length=1); methodology: str = Field(min_length=1)
    valid_until: date | None = None


class AssessmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    assessment_tier: ComponentCriticality | None = None; tier_rationale: str | None = Field(default=None, min_length=1)
    methodology: str | None = Field(default=None, min_length=1); conclusion: str | None = None; valid_until: date | None = None


class ResponseUpsert(BaseModel):
    criterion_key: str = Field(min_length=1, max_length=100); criterion_title: str = Field(min_length=1, max_length=255)
    decision: AssessmentResponseDecision; rationale: str = Field(min_length=1)


class ResponseRead(TimestampedRead):
    assessment_id: UUID; criterion_key: str; criterion_title: str; decision: str; rationale: str


class EvidenceLinkCreate(BaseModel):
    evidence_item_id: UUID; response_id: UUID | None = None; issued_at: date | None = None; valid_until: date | None = None
    @model_validator(mode="after")
    def dates_valid(self):
        if self.issued_at and self.valid_until and self.valid_until < self.issued_at: raise ValueError("valid_until must be on or after issued_at")
        return self


class EvidenceReview(BaseModel):
    review_status: EvidenceReviewStatus; review_notes: str | None = None


class EvidenceLinkRead(TimestampedRead):
    assessment_id: UUID; response_id: UUID | None; evidence_item_id: UUID; issued_at: date | None
    valid_until: date | None; review_status: str; reviewed_by_user_id: UUID | None; reviewed_at: datetime | None; review_notes: str | None


class FindingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255); description: str = Field(min_length=1)
    severity: RiskLevel; mitigation_plan: str = Field(min_length=1); owner_user_id: UUID | None = None
    due_date: date | None = None; risk_item_id: UUID | None = None


class FindingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255); description: str | None = Field(default=None, min_length=1)
    severity: RiskLevel | None = None; mitigation_plan: str | None = Field(default=None, min_length=1)
    status: SupplierFindingStatus | None = None; owner_user_id: UUID | None = None; due_date: date | None = None; risk_item_id: UUID | None = None


class FindingRead(TimestampedRead):
    assessment_id: UUID; title: str; description: str; severity: str; mitigation_plan: str
    status: str; owner_user_id: UUID | None; due_date: date | None; risk_item_id: UUID | None


class AssessmentDecision(BaseModel):
    decision: SupplierAssessmentStatus
    conclusion: str = Field(min_length=1)
    rejection_reason: str | None = None
    valid_until: date | None = None

    @model_validator(mode="after")
    def terminal_decision(self):
        allowed = {SupplierAssessmentStatus.approved, SupplierAssessmentStatus.approved_with_conditions, SupplierAssessmentStatus.rejected}
        if self.decision not in allowed: raise ValueError("decision must be approved, approved_with_conditions, or rejected")
        if self.decision == SupplierAssessmentStatus.rejected and not self.rejection_reason: raise ValueError("rejection_reason is required")
        return self


class AssessmentRead(TimestampedRead):
    supplier_id: UUID; component_id: UUID | None; product_release_id: UUID | None; system_version: int
    title: str; assessment_tier: str; tier_rationale: str; methodology: str; status: str
    conclusion: str | None; valid_until: date | None; owner_user_id: UUID; reviewer_user_id: UUID | None
    submitted_at: datetime | None; reviewed_at: datetime | None; rejection_reason: str | None
    reassessment_required: bool; reassessment_reason: str | None; reassessment_triggered_at: datetime | None; reassessment_due_date: date | None
    responses: list[ResponseRead] = []; evidence_links: list[EvidenceLinkRead] = []; findings: list[FindingRead] = []


class SbomMatchRead(BaseModel):
    sbom_record_id: UUID
    product_release_id: UUID
    matched: int
    linked: int
    unmatched: list[dict]


class MaintainerNotificationCreate(BaseModel):
    vulnerability_report_id: UUID
    component_id: UUID
    recipient: str = Field(min_length=1, max_length=320)
    notification_method: str = Field(min_length=1, max_length=50)
    information_shared: str = Field(min_length=1)
    fix_shared: bool = False
    fix_reference: str | None = Field(default=None, max_length=2048)
    assigned_to_user_id: UUID | None = None
    due_date: date | None = None


class MaintainerNotificationUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(draft|sent|acknowledged|closed)$")
    information_shared: str | None = Field(default=None, min_length=1)
    fix_shared: bool | None = None
    fix_reference: str | None = Field(default=None, max_length=2048)
    maintainer_response: str | None = None
    assigned_to_user_id: UUID | None = None
    due_date: date | None = None


class MaintainerNotificationRead(TimestampedRead):
    vulnerability_report_id: UUID; component_id: UUID; status: str; recipient: str
    notification_method: str; information_shared: str; fix_shared: bool; fix_reference: str | None
    notified_at: datetime | None; acknowledged_at: datetime | None; maintainer_response: str | None
    assigned_to_user_id: UUID | None; due_date: date | None; created_by_user_id: UUID
