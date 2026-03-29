from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DistributionMechanism


class SecurityUpdateBase(BaseModel):
    product_release_id: UUID
    title: str = Field(min_length=1)
    description: str | None = None
    cves_addressed_json: list[str] | dict[str, object] = Field(default_factory=list)
    affected_versions_json: list[str] | dict[str, object] = Field(default_factory=list)
    distribution_mechanism: DistributionMechanism = DistributionMechanism.vendor_download
    available_until: datetime | None = None
    released_at: datetime | None = None


class SecurityUpdateCreate(SecurityUpdateBase):
    pass


class SecurityUpdateUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    cves_addressed_json: list[str] | dict[str, object] | None = None
    affected_versions_json: list[str] | dict[str, object] | None = None
    distribution_mechanism: DistributionMechanism | None = None
    available_until: datetime | None = None
    released_at: datetime | None = None


class SecurityUpdateRead(SecurityUpdateBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime