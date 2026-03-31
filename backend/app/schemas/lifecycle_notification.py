from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import LifecycleNotificationStatus, LifecycleNotificationType
from app.schemas.common import ORMBaseModel


class LifecycleNotificationRecipientRead(ORMBaseModel):
    id: UUID
    full_name: str
    email: str


class LifecycleNotificationBase(BaseModel):
    support_period_record_id: UUID
    recipient_user_id: UUID | None = None
    notification_type: LifecycleNotificationType
    status: LifecycleNotificationStatus
    scheduled_for: datetime
    sent_at: datetime | None = None
    dismissed_at: datetime | None = None
    title: str
    message: str


class LifecycleNotificationRead(LifecycleNotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipient_user: LifecycleNotificationRecipientRead | None = None
    created_at: datetime
    updated_at: datetime


class LifecycleNotificationMarkSentRequest(BaseModel):
    sent_at: datetime | None = None


class LifecycleNotificationDismissRequest(BaseModel):
    dismissed_at: datetime | None = None
