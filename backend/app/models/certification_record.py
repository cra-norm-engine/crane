from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import CertificationScheme, CertificationStatus


class CertificationRecord(UUIDTimestampMixin, Base):
    __tablename__ = "certification_records"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    certification_scheme: Mapped[CertificationScheme] = mapped_column(
        nullable=False,
        index=True,
    )
    certification_scheme_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    certification_body_name: Mapped[str] = mapped_column(String(255), nullable=False)
    certificate_number: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    scope_description: Mapped[str] = mapped_column(Text, nullable=False)

    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[CertificationStatus] = mapped_column(
        nullable=False,
        default=CertificationStatus.pending,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recertification_required_by: Mapped[date | None] = mapped_column(Date, nullable=True)

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="certification_records",
    )
