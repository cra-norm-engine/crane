from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException
from app.models.enums import AuditStatus, EntityType
from app.models.incident_report import IncidentReport
from app.repositories.product_release_repository import ProductReleaseRepository
from app.schemas.incident_report import (
    IncidentEnisaMarkSentRequest,
    IncidentReportCreate,
    IncidentReportRead,
    IncidentReportUpdate,
)

logger = logging.getLogger(__name__)


class IncidentReportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.release_repository = ProductReleaseRepository(db)

    def _get_or_404(self, report_id: UUID) -> IncidentReport:
        from app.core.exceptions import NotFoundException
        report = self.db.get(IncidentReport, report_id)
        if not report:
            raise NotFoundException(f"Incident report {report_id} not found")
        return report

    def _to_read(self, report: IncidentReport) -> IncidentReportRead:
        return IncidentReportRead.model_validate(report)

    def list_incident_reports(
        self,
        *,
        product_release_id: UUID | None = None,
        product_id: UUID | None = None,
    ) -> list[IncidentReportRead]:
        """Return incident reports, optionally filtered by release or product."""
        query = self.db.query(IncidentReport)
        if product_release_id:
            query = query.filter(IncidentReport.product_release_id == product_release_id)
        elif product_id:
            from app.models.product import ProductRelease
            release_ids = self.db.query(ProductRelease.id).filter(
                ProductRelease.product_id == product_id
            ).subquery()
            query = query.filter(IncidentReport.product_release_id.in_(release_ids))
        reports = query.order_by(IncidentReport.created_at.desc()).all()
        return [self._to_read(r) for r in reports]

    def get_incident_report(self, report_id: UUID) -> IncidentReportRead:
        return self._to_read(self._get_or_404(report_id))

    def create_incident_report(
        self, payload: IncidentReportCreate, actor: object
    ) -> IncidentReportRead:
        release = self.release_repository.get_or_404(payload.product_release_id)
        report = IncidentReport(**payload.model_dump())
        try:
            self.db.add(report)
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="incident_report.created",
                entity_type=EntityType.incident_report,
                entity_id=report.id,
                status=AuditStatus.success,
                details_json={
                    "product_release_id": str(report.product_release_id),
                    "product_id": str(release.product_id),
                    "title": report.title,
                    "suspected_malicious_act": report.suspected_malicious_act,
                },
            )
            self.db.commit()
            self.db.refresh(report)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create incident report") from exc
        return self._to_read(report)

    def update_incident_report(
        self, report_id: UUID, payload: IncidentReportUpdate, actor: object
    ) -> IncidentReportRead:
        report = self._get_or_404(report_id)
        release = self.release_repository.get_or_404(report.product_release_id)
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(report, field, value)
        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="incident_report.updated",
                entity_type=EntityType.incident_report,
                entity_id=report.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(release.product_id),
                    "title": report.title,
                    "status": report.status,
                    "updated_fields": sorted(updates.keys()),
                },
            )
            self.db.commit()
            self.db.refresh(report)
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to update incident report %s", report_id)
            raise ConflictException("Unable to update incident report") from exc
        return self._to_read(report)

    def _mark_enisa_phase_sent(
        self,
        report_id: UUID,
        payload: IncidentEnisaMarkSentRequest,
        actor: object,
        *,
        phase_field: str,
        action_type: str,
    ) -> IncidentReportRead:
        from datetime import UTC, datetime as dt
        report = self._get_or_404(report_id)
        sent_at = payload.sent_at or dt.now(UTC)
        setattr(report, phase_field, sent_at)
        if payload.reference_number:
            report.enisa_reference_number = payload.reference_number
        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type=action_type,
                entity_type=EntityType.incident_report,
                entity_id=report.id,
                status=AuditStatus.success,
                details_json={
                    "sent_at": sent_at.isoformat(),
                    "reference_number": report.enisa_reference_number,
                },
            )
            self.db.commit()
            self.db.refresh(report)
        except Exception:
            self.db.rollback()
            logger.exception("Failed to mark ENISA phase %s for incident %s", phase_field, report_id)
            raise
        return self._to_read(report)

    def mark_enisa_early_warning_sent(
        self, report_id: UUID, payload: IncidentEnisaMarkSentRequest, actor: object
    ) -> IncidentReportRead:
        """Record that the Art. 14 early-warning (24h) notification was submitted to the SRP."""
        return self._mark_enisa_phase_sent(
            report_id, payload, actor,
            phase_field="enisa_early_warning_sent_at",
            action_type="incident_report.enisa_early_warning_sent",
        )

    def mark_enisa_initial_report_sent(
        self, report_id: UUID, payload: IncidentEnisaMarkSentRequest, actor: object
    ) -> IncidentReportRead:
        """Record that the Art. 14 incident notification (72h) was submitted to the SRP."""
        return self._mark_enisa_phase_sent(
            report_id, payload, actor,
            phase_field="enisa_initial_report_sent_at",
            action_type="incident_report.enisa_initial_report_sent",
        )

    def mark_enisa_final_report_sent(
        self, report_id: UUID, payload: IncidentEnisaMarkSentRequest, actor: object
    ) -> IncidentReportRead:
        """Record that the Art. 14 final report (1 month after 72h notification) was submitted."""
        return self._mark_enisa_phase_sent(
            report_id, payload, actor,
            phase_field="enisa_final_report_sent_at",
            action_type="incident_report.enisa_final_report_sent",
        )

    def delete_incident_report(self, report_id: UUID, actor: object) -> None:
        report = self._get_or_404(report_id)
        release = self.release_repository.get_or_404(report.product_release_id)
        self.db.delete(report)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="incident_report.deleted",
            entity_type=EntityType.incident_report,
            entity_id=report_id,
            status=AuditStatus.success,
            details_json={"product_id": str(release.product_id), "title": report.title},
        )
        self.db.commit()
