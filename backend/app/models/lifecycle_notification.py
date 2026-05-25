from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import LifecycleNotificationStatus, LifecycleNotificationType


class LifecycleNotification(UUIDTimestampMixin, Base):
    __tablename__ = "lifecycle_notifications"
    # Two partial unique indexes replace the old single unique constraint:
    # - EOS notifications keyed by support_period_record_id
    # - Security update notifications keyed by security_update_id
    __table_args__ = (
        Index(
            "uq_lifecycle_notif_eos",
            "support_period_record_id",
            "notification_type",
            "recipient_user_id",
            unique=True,
            postgresql_where=text("support_period_record_id IS NOT NULL"),
        ),
        Index(
            "uq_lifecycle_notif_security_update",
            "security_update_id",
            "notification_type",
            "recipient_user_id",
            unique=True,
            postgresql_where=text("security_update_id IS NOT NULL"),
        ),
    )

    # Nullable: set for EOS notifications, NULL for security update notifications.
    support_period_record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("support_period_records.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # Nullable: set for security update notifications, NULL for EOS notifications.
    security_update_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("security_updates.id", ondelete="CASCADE"),
        nullable=True,
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

    support_period_record: Mapped["SupportPeriodRecord | None"] = relationship(
        "SupportPeriodRecord",
        back_populates="lifecycle_notifications",
    )
    security_update: Mapped["SecurityUpdate | None"] = relationship(
        "SecurityUpdate",
    )
    recipient_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[recipient_user_id],
        back_populates="assigned_lifecycle_notifications",
    )
