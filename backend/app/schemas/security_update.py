from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DistributionMechanism, SecurityUpdateSeverity


class SecurityUpdateBase(BaseModel):
    product_release_id: UUID
    title: str = Field(min_length=1)
    description: str | None = None
    severity: SecurityUpdateSeverity | None = None
    is_security_only: bool = True
    integrity_info: str | None = Field(default=None, max_length=2000)
    cves_addressed_json: list[str] | dict[str, object] = Field(default_factory=list)
    affected_versions_json: list[str] | dict[str, object] = Field(default_factory=list)
    update_channels_json: list[str] = Field(default_factory=list)
    distribution_mechanism: DistributionMechanism = DistributionMechanism.vendor_download
    available_until: datetime | None = None
    released_at: datetime | None = None


class SecurityUpdateCreate(SecurityUpdateBase):
    pass


class SecurityUpdateUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    severity: SecurityUpdateSeverity | None = None
    is_security_only: bool | None = None
    integrity_info: str | None = Field(default=None, max_length=2000)
    cves_addressed_json: list[str] | dict[str, object] | None = None
    affected_versions_json: list[str] | dict[str, object] | None = None
    update_channels_json: list[str] | None = None
    distribution_mechanism: DistributionMechanism | None = None
    available_until: datetime | None = None
    released_at: datetime | None = None


class SecurityUpdateRead(SecurityUpdateBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime