"""Pydantic schemas for MarketAction (CRA Art. 35 recall / withdrawal)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MarketActionStatus, MarketActionType


class MarketActionCreate(BaseModel):
    product_release_id: UUID
    action_type: MarketActionType
    reason: str = Field(min_length=10)
    affected_scope: str | None = None
    corrective_action: str | None = None
    authority_reference_number: str | None = Field(default=None, max_length=255)
    user_notice_text: str | None = None
    internal_notes: str | None = None


class MarketActionUpdate(BaseModel):
    action_type: MarketActionType | None = None
    status: MarketActionStatus | None = None
    reason: str | None = Field(default=None, min_length=10)
    affected_scope: str | None = None
    corrective_action: str | None = None
    authority_reference_number: str | None = Field(default=None, max_length=255)
    authority_notified_at: datetime | None = None
    user_notice_text: str | None = None
    internal_notes: str | None = None


class ProductReleaseSummary(BaseModel):
    """Minimal release info embedded in MarketActionRead for display purposes."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    version: str


class MarketActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_release_id: UUID
    action_type: MarketActionType
    status: MarketActionStatus
    reason: str
    affected_scope: str | None
    corrective_action: str | None
    authority_reference_number: str | None
    authority_notified_at: datetime | None
    user_notice_text: str | None
    internal_notes: str | None
    product_release: ProductReleaseSummary | None
    created_at: datetime
    updated_at: datetime
