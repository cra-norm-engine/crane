from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import SupportType


class SupportPeriodRecord(UUIDTimestampMixin, Base):
    __tablename__ = "support_period_records"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Gap 1 — Per-version support period (CRA guidance §117).
    # When set, this record applies to a specific placed release rather than the
    # entire product. NULL is kept for backwards compatibility with existing records
    # that were created at the product level before this field existed.
    product_release_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_releases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    support_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    support_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    notify_before_days: Mapped[int] = mapped_column(Integer, nullable=False, default=180)

    support_type: Mapped[SupportType] = mapped_column(
        nullable=False,
        default=SupportType.standard,
    )

    justification_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_use_time_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    comparable_products_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    third_party_support_constraints_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_facing_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    packaging_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    eos_notification_sent_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # lifecycle versioning
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("support_period_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="support_period_records",
    )

    # Optional relationship to the specific release this support period covers.
    # Navigated when building per-version support timelines.
    product_release: Mapped["ProductRelease | None"] = relationship(
        "ProductRelease",
        foreign_keys="[SupportPeriodRecord.product_release_id]",
    )

    superseded_by: Mapped["SupportPeriodRecord | None"] = relationship(
        "SupportPeriodRecord",
        remote_side="SupportPeriodRecord.id",
        passive_deletes=True,
    )

    lifecycle_notifications: Mapped[list["LifecycleNotification"]] = relationship(
        "LifecycleNotification",
        back_populates="support_period_record",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(LifecycleNotification.created_at)",
    )

    notification_recipients: Mapped[list["SupportPeriodNotificationRecipient"]] = relationship(
        "SupportPeriodNotificationRecipient",
        back_populates="support_period_record",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SupportPeriodNotificationRecipient.created_at.asc()",
    )


class SupportPeriodNotificationRecipient(UUIDTimestampMixin, Base):
    __tablename__ = "support_period_notification_recipients"
    __table_args__ = (
        UniqueConstraint(
            "support_period_record_id",
            "user_id",
            name="uq_support_period_notification_recipients_record_user",
        ),
    )

    support_period_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("support_period_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    support_period_record: Mapped["SupportPeriodRecord"] = relationship(
        "SupportPeriodRecord",
        back_populates="notification_recipients",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="support_period_notification_assignments",
    )
