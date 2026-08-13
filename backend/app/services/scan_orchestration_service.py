# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""
Orchestration layer for automated vulnerability scanning.

This is the single entry point that automation (the nightly scheduler and the
on-upload background task) calls. It wraps the existing
``SbomVulnerabilityScanner.scan()`` — which does all the real OSV/Trivy/NVD/EPSS
work, dedup, auto-report creation and audit logging — and records one
``SbomScanRun`` row per execution so degraded/failed runs are visible and the
"new findings" delta is queryable.

It never lets a scan failure propagate to the scheduler: a broken run is
recorded as ``failed``/``degraded`` and the next cycle retries.
"""
from __future__ import annotations

import logging
import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.sbom_record import SbomRecord
from app.models.sbom_scan_run import SbomScanRun
from app.services.sbom_vulnerability_scanner import SbomVulnerabilityScanner

logger = logging.getLogger(__name__)

# Politeness delay between SBOMs during a sweep so the external APIs (OSV/NVD/
# EPSS) are not hammered. The scanner already paces its own per-request calls;
# this just adds breathing room between whole SBOMs.
_INTER_SBOM_DELAY_SECONDS = 2.0


class ScanOrchestrationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_scan(
        self,
        sbom_record_id: UUID,
        *,
        trigger: str,
        actor: object = None,
    ) -> SbomScanRun:
        """
        Run one scan and record an SbomScanRun row.

        Reuses SbomVulnerabilityScanner.scan(); translates its stats dict into a
        run record. Reachability drives the status: any unreachable source →
        "degraded"; an exception → "failed" (never re-raised, so a scheduled
        sweep keeps going).
        """
        started = time.monotonic()
        try:
            result = SbomVulnerabilityScanner(self.db).scan(
                sbom_record_id, actor=actor, trigger=trigger
            )
        except Exception as exc:  # noqa: BLE001 — a bad scan must not break the sweep
            logger.exception("Scan failed for SBOM %s (trigger=%s)", sbom_record_id, trigger)
            run = SbomScanRun(
                sbom_record_id=sbom_record_id,
                trigger=trigger,
                status="failed",
                error=str(exc)[:2000],
                duration_ms=int((time.monotonic() - started) * 1000),
            )
            self.db.add(run)
            self.db.commit()
            self.db.refresh(run)
            return run

        osv_reachable = bool(result.get("osv_reachable", True))
        scan_successful = bool(result.get("scan_successful", True))
        run = SbomScanRun(
            sbom_record_id=sbom_record_id,
            trigger=trigger,
            # "degraded" when the primary source could not be reached, so the run
            # is visibly incomplete and gets retried next cycle.
            status="failed" if not scan_successful else ("completed" if osv_reachable else "degraded"),
            findings_created=int(result.get("findings_created", 0)),
            reports_created=int(result.get("reports_created", 0)),
            components_scanned=int(result.get("components_scanned", 0)),
            nvd_enrichments=int(result.get("nvd_enrichments", 0)),
            epss_enrichments=int(result.get("epss_enrichments", 0)),
            osv_reachable=osv_reachable,
            trivy_available=bool(result.get("trivy_available", False)),
            error=result.get("guidance") if not scan_successful else None,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run


def run_scheduled_sweep() -> list[SbomScanRun]:
    """
    Re-scan every SBOM that has stored content, one per its own DB session.

    Called by the scheduler. Opens a session per SBOM so a failure on one record
    can't poison the others, paces external calls, and logs a summary. Returns
    the run records (mostly for tests / manual invocation).
    """
    # Enumerate target SBOM ids up front in a short-lived session.
    with SessionLocal() as db:
        sbom_ids = list(
            db.scalars(
                select(SbomRecord.id).where(SbomRecord.sbom_content.is_not(None))
            ).all()
        )

    logger.info("Scheduled vulnerability sweep starting: %d SBOM(s) with content", len(sbom_ids))
    runs: list[SbomScanRun] = []
    new_findings = 0
    degraded = 0

    for index, sbom_id in enumerate(sbom_ids):
        with SessionLocal() as db:
            run = ScanOrchestrationService(db).run_scan(
                sbom_id, trigger="scheduled", actor=None
            )
            runs.append(run)
            new_findings += run.findings_created
            if run.status != "completed":
                degraded += 1
        # Be polite to external APIs between SBOMs (skip after the last one).
        if index < len(sbom_ids) - 1:
            time.sleep(_INTER_SBOM_DELAY_SECONDS)

    logger.info(
        "Scheduled vulnerability sweep finished: %d SBOM(s), %d new finding(s), %d degraded/failed",
        len(runs),
        new_findings,
        degraded,
    )
    return runs
