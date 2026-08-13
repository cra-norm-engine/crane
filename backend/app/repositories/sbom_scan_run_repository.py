# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sbom_scan_run import SbomScanRun
from app.repositories.base import BaseRepository


class SbomScanRunRepository(BaseRepository[SbomScanRun]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SbomScanRun)

    def list_by_sbom(self, sbom_record_id: UUID) -> list[SbomScanRun]:
        """Recorded scan executions for an SBOM, most recent first."""
        stmt = (
            select(SbomScanRun)
            .where(SbomScanRun.sbom_record_id == sbom_record_id)
            .order_by(SbomScanRun.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def active_for_sbom(self, sbom_record_id: UUID) -> SbomScanRun | None:
        stmt = (
            select(SbomScanRun)
            .where(
                SbomScanRun.sbom_record_id == sbom_record_id,
                SbomScanRun.status.in_(("queued", "running")),
            )
            .order_by(SbomScanRun.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)
