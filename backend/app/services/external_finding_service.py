"""Atomic external finding batches; never invoke scanners or remove absent findings."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, NotFoundException
from app.models.enums import VexStatus, VulnerabilityLifecycleStatus, VulnerabilitySource
from app.models.product import ProductRelease
from app.models.sbom_record import SbomRecord
from app.models.sbom_vulnerability_finding import SbomVulnerabilityFinding
from app.models.vulnerability_report import VulnerabilityReport
from app.schemas.external_finding import ExternalFindingsImport, ImportResult
from app.services.vulnerability_priority_service import VulnerabilityPriorityService, severity_from_cvss


def assessment_values(assessment: dict | None) -> dict:
    state = assessment["vex_status"] if assessment else None
    return {
        "vex_status": state,
        "is_exploitable": None if state in (None, "under_investigation") else state == "affected",
        "exploitability_rationale": assessment["rationale"] if assessment else None,
        "operational_conditions": assessment.get("operational_conditions") if assessment else None,
    }


def assessment_was_edited(report: VulnerabilityReport, previous: dict | None) -> bool:
    expected = assessment_values(previous)
    timestamp = datetime.fromisoformat(previous["assessed_at"]) if previous else None
    return any(getattr(report, field) != value for field, value in expected.items()) or report.exploitability_assessed_at != timestamp


def import_external_findings(
    db: Session, sbom_id: UUID, payload: ExternalFindingsImport, *, actor_user_id: UUID, commit: bool = True,
) -> ImportResult:
    sbom = db.get(SbomRecord, sbom_id)
    if sbom is None:
        raise NotFoundException("SBOM not found")
    # Serialize imports for all SBOMs of the release, including its aggregate flag.
    release = db.scalar(select(ProductRelease).where(
        ProductRelease.id == sbom.product_release_id,
    ).with_for_update())
    result = ImportResult()
    priority = VulnerabilityPriorityService(db)
    for item in payload.findings:
        incoming = item.model_dump(mode="json")
        finding = db.scalar(select(SbomVulnerabilityFinding).where(
            SbomVulnerabilityFinding.sbom_record_id == sbom_id,
            SbomVulnerabilityFinding.external_source == payload.source,
            SbomVulnerabilityFinding.external_id == item.external_id,
        ).with_for_update())
        previous = finding.external_payload_json if finding else None
        if finding and item.source_updated_at < finding.external_updated_at:
            result.stale += 1
            continue
        if previous == incoming:
            report = db.scalar(select(VulnerabilityReport).where(
                VulnerabilityReport.id == finding.linked_report_id,
            ).with_for_update())
            if report is None:
                raise ConflictException(f"Linked report was deleted: {item.external_id}")
            if incoming.get("assessment") and assessment_was_edited(report, incoming["assessment"]):
                result.assessment_conflicts.append(item.external_id)
            result.unchanged += 1
            continue
        if finding and item.source_updated_at == finding.external_updated_at:
            raise ConflictException(f"Different content for the same source timestamp: {item.external_id}")
        if finding and (finding.vuln_id, finding.component_name, finding.component_version, finding.component_purl) != (
            item.vulnerability_id, item.component_name, item.component_version, item.component_purl,
        ):
            raise ConflictException(f"External identifier reused for another component/vulnerability: {item.external_id}")
        if finding is None:
            finding = SbomVulnerabilityFinding(
                sbom_record_id=sbom_id, external_source=payload.source,
                external_id=item.external_id, vuln_id=item.vulnerability_id,
                component_name=item.component_name, component_version=item.component_version,
                component_purl=item.component_purl, sources_json=[payload.source],
            )
            db.add(finding)
            db.flush()
            report = VulnerabilityReport(
                product_release_id=sbom.product_release_id,
                title=f"{item.vulnerability_id} in {item.component_name}",
                source=VulnerabilitySource.external, sbom_finding_id=finding.id,
            )
            db.add(report)
            db.flush()
            finding.linked_report_id = report.id
            result.created += 1
        else:
            report = db.scalar(select(VulnerabilityReport).where(
                VulnerabilityReport.id == finding.linked_report_id,
            ).with_for_update())
            if report is None:
                raise ConflictException(f"Linked report was deleted: {item.external_id}")
            result.updated += 1

        finding.aliases_json = item.aliases
        finding.summary = item.summary
        finding.cvss_score = item.cvss_score
        finding.cvss_vector = item.cvss_vector
        severity = severity_from_cvss(item.cvss_score) if item.cvss_score is not None else item.severity
        finding.severity = severity.value if severity else None
        finding.epss_score = item.epss_score
        finding.epss_percentile = item.epss_percentile
        report.cvss_score = item.cvss_score
        report.severity = severity
        report.description = item.summary
        report.cve_ids_json = sorted({v for v in [item.vulnerability_id, *item.aliases] if v.startswith("CVE-")})

        assessment = incoming.get("assessment")
        if assessment is not None:
            # Preserve local decisions, including changes with the same VEX status.
            local_edit = assessment_was_edited(report, previous.get("assessment") if previous else None)
            if local_edit:
                result.assessment_conflicts.append(item.external_id)
            else:
                for field, value in assessment_values(assessment).items():
                    setattr(report, field, VexStatus(value) if field == "vex_status" else value)
                report.exploitability_assessed_at = item.assessment.assessed_at
                report.exploitability_assessed_by_id = actor_user_id

        finding.external_updated_at = item.source_updated_at
        finding.external_payload_json = incoming
        db.flush()
        priority.evaluate(report, trigger="external_import", actor_user_id=actor_user_id)
        create_audit_event(
            db, actor_user_id=actor_user_id, action_type="vulnerability_report.external_imported",
            entity_type="vulnerability_report", entity_id=report.id, status="success",
            details_json={"source": payload.source, "external_id": item.external_id,
                          "before": previous, "after": incoming,
                          "assessment_conflict": item.external_id in result.assessment_conflicts},
        )
    db.flush()
    blocking = db.scalars(select(VulnerabilityReport).where(
        VulnerabilityReport.product_release_id == release.id,
        VulnerabilityReport.is_exploitable.is_(True),
        VulnerabilityReport.status.notin_([VulnerabilityLifecycleStatus.fixed, VulnerabilityLifecycleStatus.retired]),
    )).all()
    release.has_known_exploitable_vulnerabilities = bool(blocking)
    release.kev_notes = "; ".join(report.title for report in blocking) or None
    if commit:
        db.commit()
    return result
