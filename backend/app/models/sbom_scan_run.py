# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class SbomScanRun(UUIDTimestampMixin, Base):
    """
    One record of an SBOM vulnerability scan execution.

    Automated scans (nightly sweep, on-upload) leave a trail here so that a
    scan which ran with an unreachable source (e.g. OSV offline) is visible as
    "degraded" and gets retried on the next cycle, and so the "new findings"
    delta of each run is queryable. The actual scan/matching/report-creation
    still lives in SbomVulnerabilityScanner.scan(); this table only records the
    outcome. `created_at` (from the mixin) is the run timestamp.
    """

    __tablename__ = "sbom_scan_runs"

    # The SBOM record that was scanned. Cascades so runs disappear with the SBOM.
    sbom_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sbom_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # What kicked off the scan: "manual" | "scheduled" | "on_upload".
    trigger: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Outcome: "completed" (all sources reachable) | "degraded" (a source was
    # skipped/unreachable) | "failed" (the scan raised).
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Scan statistics (mirrors the SbomVulnerabilityScanner.scan() result dict).
    findings_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reports_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    components_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nvd_enrichments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    epss_enrichments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Per-source reachability at scan time (drives the "degraded" status/UI note).
    osv_reachable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    trivy_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Populated only when status == "failed".
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Wall-clock duration of the scan in milliseconds (best-effort).
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sbom_record = relationship("SbomRecord")
