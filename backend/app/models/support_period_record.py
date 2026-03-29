from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Text
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

    support_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    support_end_date: Mapped[date] = mapped_column(Date, nullable=False)

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