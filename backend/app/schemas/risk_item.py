from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import RiskItemStatus, RiskLevel
from app.schemas.common import ORMBaseModel, TimestampedRead


class RiskItemCreate(BaseModel):
    risk_assessment_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    threat_scenario: str = Field(min_length=1)
    asset_affected: str = Field(min_length=1, max_length=255)
    likelihood: RiskLevel
    impact: RiskLevel
    risk_level: RiskLevel
    mitigation_plan: str = Field(min_length=1)
    residual_risk_level: RiskLevel | None = None
    status: RiskItemStatus = RiskItemStatus.open
    owner_user_id: UUID | None = None
    due_date: date | None = None


class RiskItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    threat_scenario: str | None = Field(default=None, min_length=1)
    asset_affected: str | None = Field(default=None, min_length=1, max_length=255)
    likelihood: RiskLevel | None = None
    impact: RiskLevel | None = None
    risk_level: RiskLevel | None = None
    mitigation_plan: str | None = Field(default=None, min_length=1)
    residual_risk_level: RiskLevel | None = None
    status: RiskItemStatus | None = None
    owner_user_id: UUID | None = None
    due_date: date | None = None


class RiskItemRead(TimestampedRead):
    risk_assessment_id: UUID
    title: str
    description: str
    threat_scenario: str
    asset_affected: str
    likelihood: RiskLevel
    impact: RiskLevel
    risk_level: RiskLevel
    mitigation_plan: str
    residual_risk_level: RiskLevel | None
    status: RiskItemStatus
    owner_user_id: UUID | None
    due_date: date | None


class RiskItemSummaryRead(ORMBaseModel):
    id: UUID
    risk_assessment_id: UUID
    title: str
    risk_level: RiskLevel
    residual_risk_level: RiskLevel | None
    status: RiskItemStatus