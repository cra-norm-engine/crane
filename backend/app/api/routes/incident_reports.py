# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.incident_report import (
    IncidentEnisaMarkSentRequest,
    IncidentReportCreate,
    IncidentReportRead,
    IncidentReportUpdate,
)
from app.services.incident_report_service import IncidentReportService

router = APIRouter()


@router.get("/", response_model=list[IncidentReportRead])
def list_incident_reports(
    product_release_id: UUID | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.enisa_report_read)),
) -> list[IncidentReportRead]:
    return IncidentReportService(db).list_incident_reports(
        product_release_id=product_release_id,
        product_id=product_id,
    )


@router.post("/", response_model=IncidentReportRead, status_code=status.HTTP_201_CREATED)
def create_incident_report(
    payload: IncidentReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.enisa_report_write)),
) -> IncidentReportRead:
    return IncidentReportService(db).create_incident_report(payload, actor=current_user)


@router.get("/{report_id}", response_model=IncidentReportRead)
def get_incident_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.enisa_report_read)),
) -> IncidentReportRead:
    return IncidentReportService(db).get_incident_report(report_id)


@router.put("/{report_id}", response_model=IncidentReportRead)
def update_incident_report(
    report_id: UUID,
    payload: IncidentReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.enisa_report_write)),
) -> IncidentReportRead:
    return IncidentReportService(db).update_incident_report(report_id, payload, actor=current_user)


@router.post("/{report_id}/enisa/mark-early-warning-sent", response_model=IncidentReportRead)
def mark_enisa_early_warning_sent(
    report_id: UUID,
    payload: IncidentEnisaMarkSentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.enisa_report_write)),
) -> IncidentReportRead:
    """Record that the Art. 14 early-warning (24h) was submitted to the ENISA SRP."""
    return IncidentReportService(db).mark_enisa_early_warning_sent(report_id, payload, actor=current_user)


@router.post("/{report_id}/enisa/mark-initial-report-sent", response_model=IncidentReportRead)
def mark_enisa_initial_report_sent(
    report_id: UUID,
    payload: IncidentEnisaMarkSentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.enisa_report_write)),
) -> IncidentReportRead:
    """Record that the Art. 14 incident notification (72h) was submitted to the ENISA SRP."""
    return IncidentReportService(db).mark_enisa_initial_report_sent(report_id, payload, actor=current_user)


@router.post("/{report_id}/enisa/mark-final-report-sent", response_model=IncidentReportRead)
def mark_enisa_final_report_sent(
    report_id: UUID,
    payload: IncidentEnisaMarkSentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.enisa_report_write)),
) -> IncidentReportRead:
    """Record that the Art. 14 final report (1 month after 72h notification) was submitted."""
    return IncidentReportService(db).mark_enisa_final_report_sent(report_id, payload, actor=current_user)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_incident_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.enisa_report_write)),
) -> Response:
    IncidentReportService(db).delete_incident_report(report_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
