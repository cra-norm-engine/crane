from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import LifecycleNotificationStatus, LifecycleNotificationType


class LifecycleNotification(UUIDTimestampMixin, Base):
    __tablename__ = "lifecycle_notifications"
    __table_args__ = (
        UniqueConstraint(
            "support_period_record_id",
            "notification_type",
            "recipient_user_id",
            name="uq_lifecycle_notifications_record_type_recipient",
        ),
    )

    support_period_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("support_period_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    notification_type: Mapped[LifecycleNotificationType] = mapped_column(
        nullable=False,
        default=LifecycleNotificationType.end_of_support_upcoming,
    )
    status: Mapped[LifecycleNotificationStatus] = mapped_column(
        nullable=False,
        default=LifecycleNotificationStatus.pending,
    )

    scheduled_for: Mapped[datetime] = mapped_column(nullable=False, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    support_period_record: Mapped["SupportPeriodRecord"] = relationship(
        "SupportPeriodRecord",
        back_populates="lifecycle_notifications",
    )
    recipient_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[recipient_user_id],
        back_populates="assigned_lifecycle_notifications",
    )
