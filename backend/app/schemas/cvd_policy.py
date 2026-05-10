from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CvdPolicyStatus


class CvdPolicyBase(BaseModel):
    product_id: UUID
    status: CvdPolicyStatus = CvdPolicyStatus.draft

    # Contact & reporting channels
    contact_email: str | None = Field(default=None, max_length=320)
    pgp_key_url: str | None = Field(default=None, max_length=2048)
    security_txt_url: str | None = Field(default=None, max_length=2048)
    bug_bounty_url: str | None = Field(default=None, max_length=2048)

    # Timelines
    response_sla_hours: int = Field(default=48, ge=1, le=8760)
    disclosure_window_days: int = Field(default=90, ge=1, le=365)

    # Legal & researcher relations
    safe_harbor: bool = False
    acknowledgement_offered: bool = False

    # Scope
    scope_description: str | None = None
    out_of_scope_description: str | None = None
    supported_versions: str | None = None

    # Policy document
    policy_url: str | None = Field(default=None, max_length=2048)
    policy_text: str | None = None


class CvdPolicyCreate(CvdPolicyBase):
    pass


class CvdPolicyUpdate(BaseModel):
    status: CvdPolicyStatus | None = None

    contact_email: str | None = Field(default=None, max_length=320)
    pgp_key_url: str | None = Field(default=None, max_length=2048)
    security_txt_url: str | None = Field(default=None, max_length=2048)
    bug_bounty_url: str | None = Field(default=None, max_length=2048)

    response_sla_hours: int | None = Field(default=None, ge=1, le=8760)
    disclosure_window_days: int | None = Field(default=None, ge=1, le=365)

    safe_harbor: bool | None = None
    acknowledgement_offered: bool | None = None

    scope_description: str | None = None
    out_of_scope_description: str | None = None
    supported_versions: str | None = None

    policy_url: str | None = Field(default=None, max_length=2048)
    policy_text: str | None = None


class CvdPolicyRead(CvdPolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
