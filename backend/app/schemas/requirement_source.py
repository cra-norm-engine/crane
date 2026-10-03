from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from app.schemas.common import TimestampedRead


class RequirementSourceCreate(BaseModel):
    identifier: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    source_type: str = Field(min_length=1, max_length=50)
    edition: str | None = Field(default=None, max_length=100)
    publisher: str | None = Field(default=None, max_length=255)
    reference_url: str | None = Field(default=None, max_length=2048)
    license_note: str | None = None
    organization_wide: bool = False
    product_ids: list[UUID] = []

    @model_validator(mode="after")
    def validate_scope(self):
        if not self.organization_wide and not self.product_ids:
            raise ValueError("Select organization-wide scope or at least one product.")
        return self


class RequirementSourceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    edition: str | None = Field(default=None, max_length=100)
    publisher: str | None = Field(default=None, max_length=255)
    reference_url: str | None = Field(default=None, max_length=2048)
    license_note: str | None = None
    organization_wide: bool | None = None
    product_ids: list[UUID] | None = None


class RequirementSourceRead(TimestampedRead):
    identifier: str
    title: str
    source_type: str
    edition: str | None
    publisher: str | None
    reference_url: str | None
    license_note: str | None
    status: str
    organization_wide: bool
    is_system_managed: bool
    product_ids: list[UUID]
    requirement_count: int = 0


class RequirementSourcePublish(BaseModel):
    status: str = Field(pattern="^(published|retired)$")
