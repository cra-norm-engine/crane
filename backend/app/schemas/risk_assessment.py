from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RiskAssessmentStatus
from app.schemas.common import TimestampedRead
from app.models.enums import EvidenceType, RiskAssessmentStatus, RiskItemStatus, RiskLevel
from app.schemas.common import ORMBaseModel
class RiskAssessmentBase(BaseModel):
    product_id: UUID
    product_release_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    version_label: str = Field(min_length=1, max_length=100)
    status: RiskAssessmentStatus = RiskAssessmentStatus.draft
    methodology: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_user_id: UUID


class RiskAssessmentCreate(RiskAssessmentBase):
    pass


class RiskAssessmentUpdate(BaseModel):
    product_release_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    version_label: str | None = Field(default=None, min_length=1, max_length=100)
    status: RiskAssessmentStatus | None = None
    methodology: str | None = Field(default=None, min_length=1)
    summary: str | None = Field(default=None, min_length=1)
    owner_user_id: UUID | None = None
    approved_at: datetime | None = None


class RiskAssessmentDuplicateVersionRequest(BaseModel):
    version_label: str = Field(min_length=1, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=255)
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
    approved_at: datetime | None

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