from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import AdvisoryStatus, SecurityUpdateSeverity


class SecurityAdvisory(UUIDTimestampMixin, Base):
    """
    Gap 3 — Annex I Part II §4/§8: manufacturers must publicly disclose fixed
    vulnerability information and issue timely security advisories with remediation guidance.
    Gap 7 — embargo_until tracks the coordinated disclosure embargo period.
    """

    __tablename__ = "security_advisories"

    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Human-readable advisory identifier, e.g. "CRANE-2026-001". Unique per installation.
    advisory_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    severity: Mapped[SecurityUpdateSeverity | None] = mapped_column(nullable=True, index=True)
    status: Mapped[AdvisoryStatus] = mapped_column(
        nullable=False,
        default=AdvisoryStatus.draft,
        index=True,
    )

    cve_ids_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    affected_versions_json: Mapped[list[str] | dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    fixed_in_versions_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    # Mitigation that can be applied before a patch is available.
    workaround: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Step-by-step remediation instructions for end users.
    remediation_steps: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Gap 7 — date until which this advisory is kept under embargo.
    # NULL means no embargo; once past, the advisory may be published.
    embargo_until: Mapped[datetime | None] = mapped_column(nullable=True)

    # Date/time the advisory was made publicly available.
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)

    product_release: Mapped["ProductRelease"] = relationship(
        "ProductRelease",
        back_populates="security_advisories",
    )
