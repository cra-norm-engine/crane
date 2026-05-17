from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.enums import CertificationScheme, CertificationStatus
from app.schemas.common import TimestampedRead


class CertificationRecordCreate(BaseModel):
    product_id: UUID
    certification_scheme: CertificationScheme
    certification_scheme_label: str | None = Field(default=None, max_length=255)
    certification_body_name: str = Field(min_length=1, max_length=255)
    certificate_number: str | None = Field(default=None, max_length=255)
    scope_description: str = Field(min_length=1)
    issued_date: date | None = None
    valid_until_date: date | None = None
    status: CertificationStatus = CertificationStatus.pending
    notes: str | None = None
    recertification_required_by: date | None = None

    @model_validator(mode="after")
    def validate_dates_and_label(self) -> "CertificationRecordCreate":
        if self.issued_date and self.valid_until_date and self.valid_until_date < self.issued_date:
            raise ValueError("valid_until_date must be on or after issued_date")
        if self.certification_scheme.value != "other":
            self.certification_scheme_label = None
        return self


class CertificationRecordUpdate(BaseModel):
    certification_scheme: CertificationScheme | None = None
    certification_scheme_label: str | None = Field(default=None, max_length=255)
    certification_body_name: str | None = Field(default=None, min_length=1, max_length=255)
    certificate_number: str | None = Field(default=None, max_length=255)
    scope_description: str | None = Field(default=None, min_length=1)
    issued_date: date | None = None
    valid_until_date: date | None = None
    status: CertificationStatus | None = None
    notes: str | None = None
    recertification_required_by: date | None = None

    @model_validator(mode="after")
    def validate_dates_and_label(self) -> "CertificationRecordUpdate":
        if self.issued_date and self.valid_until_date and self.valid_until_date < self.issued_date:
            raise ValueError("valid_until_date must be on or after issued_date")
        if self.certification_scheme and self.certification_scheme.value != "other":
            self.certification_scheme_label = None
        return self


class CertificationRecordArtifactLinkRead(BaseModel):
    id: UUID
    artifact_revision: Any
    linked_by_user_id: UUID | None


class CertificationRecordRead(TimestampedRead):
    product_id: UUID
    certification_scheme: CertificationScheme
    certification_scheme_label: str | None
    certification_body_name: str
    certificate_number: str | None
    scope_description: str
    issued_date: date | None
    valid_until_date: date | None
    status: CertificationStatus
    notes: str | None
    recertification_required_by: date | None
    artifact_links: list[CertificationRecordArtifactLinkRead] | None = None
