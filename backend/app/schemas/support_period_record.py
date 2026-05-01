from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import SupportType
from app.schemas.common import ORMBaseModel


class SupportPeriodNotificationRecipientRead(ORMBaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    email: str


class SupportPeriodNotificationRecipientOptionRead(ORMBaseModel):
    id: UUID
    email: str
    full_name: str
    roles: list[str]


class SupportPeriodRecordBase(BaseModel):
    product_id: UUID

    # Gap 1 — Per-version support period linkage (CRA guidance §117).
    # If set, this record applies to a specific placed release rather than
    # the entire product. NULL for backwards-compatible product-level records.
    product_release_id: UUID | None = None

    support_start_date: date
    support_end_date: date
    notify_before_days: int = Field(default=180, ge=1, le=3650)
    support_type: SupportType = SupportType.standard
    recipient_user_ids: list[UUID] = Field(default_factory=list)

    justification_text: str = Field(min_length=1)
    expected_use_time_text: str | None = None
    comparable_products_text: str | None = None
    third_party_support_constraints_text: str | None = None

    user_facing_summary: str | None = None
    packaging_summary: str | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "SupportPeriodRecordBase":
        if self.support_end_date < self.support_start_date:
            raise ValueError("support_end_date must be on or after support_start_date")
        return self


class SupportPeriodRecordCreate(SupportPeriodRecordBase):
    pass


class SupportPeriodRecordUpdate(BaseModel):
    support_start_date: date | None = None
    support_end_date: date | None = None
    notify_before_days: int | None = Field(default=None, ge=1, le=3650)
    support_type: SupportType | None = None
    recipient_user_ids: list[UUID] | None = None

    justification_text: str | None = Field(default=None, min_length=1)
    expected_use_time_text: str | None = None
    comparable_products_text: str | None = None
    third_party_support_constraints_text: str | None = None

    user_facing_summary: str | None = None
    packaging_summary: str | None = None

    @model_validator(mode="after")
    def validate_date_range_if_both_present(self) -> "SupportPeriodRecordUpdate":
        if (
            self.support_start_date is not None
            and self.support_end_date is not None
            and self.support_end_date < self.support_start_date
        ):
            raise ValueError("support_end_date must be on or after support_start_date")
        return self


class SupportPeriodRecordRead(SupportPeriodRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    eos_notification_sent_at: datetime | None
    is_active: bool
    superseded_by_id: UUID | None
    recipients: list[SupportPeriodNotificationRecipientRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SupportPeriodSnippetGenerateRequest(BaseModel):
    product_id: UUID
    support_start_date: date
    support_end_date: date
    support_type: SupportType = SupportType.standard

    justification_text: str = Field(min_length=1)
    expected_use_time_text: str | None = None
    comparable_products_text: str | None = None
    third_party_support_constraints_text: str | None = None


class SupportPeriodSnippetRead(BaseModel):
    user_facing_summary: str
    packaging_summary: str


class SupportPeriodRecordHistoryRead(BaseModel):
    product_id: UUID
    records: list[SupportPeriodRecordRead]
