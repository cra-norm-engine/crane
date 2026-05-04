from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CvdPolicyStatus


class CvdPolicyBase(BaseModel):
    product_id: UUID
    status: CvdPolicyStatus = CvdPolicyStatus.draft
    policy_url: str | None = Field(default=None, max_length=2048)
    disclosure_window_days: int = Field(default=90, ge=1, le=365)
    contact_email: str | None = Field(default=None, max_length=320)
    policy_text: str | None = None


class CvdPolicyCreate(CvdPolicyBase):
    pass


class CvdPolicyUpdate(BaseModel):
    status: CvdPolicyStatus | None = None
    policy_url: str | None = Field(default=None, max_length=2048)
    disclosure_window_days: int | None = Field(default=None, ge=1, le=365)
    contact_email: str | None = Field(default=None, max_length=320)
    policy_text: str | None = None


class CvdPolicyRead(CvdPolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
