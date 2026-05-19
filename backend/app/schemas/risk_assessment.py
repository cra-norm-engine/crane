from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.enums import RiskAssessmentStatus
from app.schemas.common import TimestampedRead
from app.models.enums import EvidenceType, RiskAssessmentStatus, RiskItemStatus, RiskLevel
from app.schemas.common import ORMBaseModel
class RiskAssessmentBase(BaseModel):
    product_id: UUID
    product_release_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    status: RiskAssessmentStatus = RiskAssessmentStatus.draft
    methodology: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_user_id: UUID
    # User-defined assessment name (optional: "Q2 Assessment", "Annual Review", etc.)
    user_version: str | None = Field(default=None, max_length=100)


class RiskAssessmentCreate(RiskAssessmentBase):
    pass


class RiskAssessmentUpdate(BaseModel):
    product_release_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: RiskAssessmentStatus | None = None
    methodology: str | None = Field(default=None, min_length=1)
    summary: str | None = Field(default=None, min_length=1)
    owner_user_id: UUID | None = None
    approved_at: datetime | None = None
    # Approval workflow fields — set by the reviewer, not by the owner directly.
    reviewer_user_id: UUID | None = None
    rejection_reason: str | None = None


class RiskAssessmentDuplicateVersionRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    user_version: str | None = Field(default=None, max_length=100)
    product_release_id: UUID | None = None
    summary: str | None = Field(default=None, min_length=1)
    owner_user_id: UUID | None = None
    reset_status_to_draft: bool = True
    copy_risk_items: bool = True
    copy_requirement_mappings: bool = True
    copy_evidence_links: bool = False


class RiskAssessmentApproveRequest(BaseModel):
    approved_at: datetime | None = None


class RiskAssessmentRead(RiskAssessmentBase, TimestampedRead):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    system_version: int  # Auto-incremented version number
    approved_at: datetime | None
    # Approval workflow — populated after submit/review cycle.
    reviewer_user_id: UUID | None = None
    rejection_reason: str | None = None

    @computed_field  # type: ignore
    @property
    def system_version_label(self) -> str:
        """Display system version as v1, v2, v3"""
        return f"v{self.system_version}"

    @computed_field  # type: ignore
    @property
    def display_version(self) -> str:
        """
        Smart display:
        - If user_version is set: "Q2 Assessment (v2)"
        - If not set: "v2"
        """
        if self.user_version:
            return f"{self.user_version} ({self.system_version_label})"
        return self.system_version_label


class RiskAssessmentRejectRequest(BaseModel):
    """Payload for the POST /{assessment_id}/reject endpoint."""

    rejection_reason: str = Field(
        min_length=5,
        description="Required explanation for rejection; must be at least 5 characters.",
    )

class RiskItemSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    risk_level: RiskLevel
    status: RiskItemStatus
    owner_user_id: UUID | None
    created_at: datetime
    updated_at: datetime


class EvidenceItemSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    evidence_type: EvidenceType
    file_path: str | None
    external_url: str | None
    uploaded_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class RiskAssessmentDetailRead(RiskAssessmentRead):
    risk_items_count: int = 0
    evidence_items_count: int = 0
    risk_items: list[RiskItemSummaryRead] = []
    evidence_items: list[EvidenceItemSummaryRead] = []