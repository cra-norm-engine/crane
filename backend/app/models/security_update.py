from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import DistributionMechanism


class SecurityUpdate(UUIDTimestampMixin, Base):
    __tablename__ = "security_updates"

    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    cves_addressed_json: Mapped[list[str] | dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    affected_versions_json: Mapped[list[str] | dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    distribution_mechanism: Mapped[DistributionMechanism] = mapped_column(
        nullable=False,
        default=DistributionMechanism.vendor_download,
    )

    available_until: Mapped[datetime | None] = mapped_column(nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(nullable=True)

    product_release: Mapped["ProductRelease"] = relationship(
        "ProductRelease",
        back_populates="security_updates",
    )