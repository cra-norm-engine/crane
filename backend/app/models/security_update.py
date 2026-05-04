from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import DistributionMechanism, SecurityUpdateSeverity


class SecurityUpdate(UUIDTimestampMixin, Base):
    __tablename__ = "security_updates"

    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    severity: Mapped[SecurityUpdateSeverity | None] = mapped_column(nullable=True, index=True)
    is_security_only: Mapped[bool] = mapped_column(nullable=False, default=True)
    integrity_info: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    update_channels_json: Mapped[list[str]] = mapped_column(
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

    # Gap 5 — Annex I Part II §3/§4: numeric CVSS score and vector string for severity disclosure.
    cvss_score: Mapped[float | None] = mapped_column(nullable=True)
    cvss_vector: Mapped[str | None] = mapped_column(Text, nullable=True)
    # External CVE database links (NVD, MITRE, vendor advisories).
    cve_links_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    # Gap 8 — Annex I Part II §2/§8: "without delay" SLA tracking.
    # vulnerability_discovered_at anchors the remediation clock.
    # remediation_deadline is auto-set or manually overridden.
    vulnerability_discovered_at: Mapped[datetime | None] = mapped_column(nullable=True)
    remediation_deadline: Mapped[datetime | None] = mapped_column(nullable=True)

    # Gap 9 — Annex I Part II §8: security updates must be free of charge.
    # Defaults to True; a False value triggers a compliance warning in the UI.
    is_free_of_charge: Mapped[bool] = mapped_column(nullable=False, default=True)

    product_release: Mapped["ProductRelease"] = relationship(
        "ProductRelease",
        back_populates="security_updates",
    )