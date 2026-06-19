# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""
Release Compliance Report Service.

Assembles a comprehensive, CRA-aligned compliance dossier for a single product
release and exposes it two ways from ONE data builder:

  * build_report_data(release_id)  -> a JSON-serialisable dict (17 sections plus
    front matter). Consumed by the in-app HTML report view and the PDF template.
  * generate_pdf(release_id)       -> a formal PDF (cover, TOC, glossary,
    introduction, sections) rendered from that dict via Jinja2 + WeasyPrint.

Where a section needs data the tool does not yet capture, the builder emits an
explicit ``placeholder`` marker so the report honestly shows the gap rather than
silently omitting it.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.annex_requirement import AnnexRequirement
from app.models.audit_log_event import AuditLogEvent
from app.models.certification_record import CertificationRecord
from app.models.change import Change, SubstantialModificationAssessment
from app.models.cvd_policy import CvdPolicy
from app.models.incident_report import IncidentReport
from app.models.product import Product, ProductRelease, ProductScopeEvaluation
from app.models.release_gate import ReleaseGate, ReleaseGateItem
from app.models.requirement_mapping import (
    ProductRequirementDecision,
    RequirementMapping,
    RequirementMappingArtifactLink,
)
from app.models.risk_assessment import RiskAssessment
from app.models.sbom_record import SbomRecord
from app.models.sbom_vulnerability_finding import SbomVulnerabilityFinding
from app.models.security_update import SecurityUpdate
from app.models.support_period_record import SupportPeriodRecord
from app.models.user import User
from app.models.vulnerability_report import VulnerabilityReport

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Marker used for fields/sections that require a data model CRANE does not have
# yet (surfaced in the report as an honest "Not recorded in CRANE" placeholder).
_PLACEHOLDER = "__placeholder__"

# Map a per-requirement implementation status to a coverage bucket.
_IMPL_TO_COVERAGE = {
    "verified": "compliant",
    "implemented": "compliant",
    "in_progress": "partial",
    "planned": "gap",
    "not_applicable": "na",
}
_COVERAGE_LABEL = {"compliant": "Compliant", "partial": "Partial", "gap": "Gap", "na": "N/A"}

# Severity ordering for picking the "top" vulnerabilities to surface.
_SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "informational": 0}

# Risk-level ordering + colour bucket for the detailed risk register.
_RISK_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
_RISK_BUCKET = {"critical": "bad", "high": "bad", "medium": "warn", "low": "ok"}

# Vulnerability-finding severity -> colour bucket (mirrors _RISK_BUCKET).
_VULN_SEVERITY_BUCKET = {"critical": "bad", "high": "bad", "medium": "warn", "low": "ok", "informational": "na"}

# Vulnerability lifecycle statuses considered "open" (not yet resolved/retired).
_VULN_OPEN = {"reported", "triaged", "fix_in_progress", "embargo"}


class ReleaseReportService:
    """Builds the compliance-report data and renders the PDF for one release."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_pdf(self, release_id: UUID, generated_by: str | None = None) -> bytes:
        """Render the formal PDF for a release. Raises NotFoundException if missing."""
        data = self.build_report_data(release_id, generated_by=generated_by)
        html = self._render_html(data)
        return self._html_to_pdf(html)

    def generate_filename(self, release_id: UUID) -> str:
        """Return a safe filename for Content-Disposition."""
        release = self._get_release(release_id)
        product = self.db.get(Product, release.product_id)
        product_code = (product.product_code if product else "product").lower().replace(" ", "-")
        return f"cra-report-{product_code}-v{release.system_version}.pdf"

    # ------------------------------------------------------------------
    # Data assembly — one serialisable dict feeding both PDF and HTML view
    # ------------------------------------------------------------------

    def build_report_data(self, release_id: UUID, generated_by: str | None = None) -> dict:
        """Collect every report section as plain JSON-serialisable values."""
        release = self._get_release(release_id)
        product = self.db.get(Product, release.product_id)
        if product is None:
            raise NotFoundException("Product not found for this release")

        annex = self._annex_sections(release_id)
        coverage = self._coverage(annex["part1"] + annex["part2"])

        return {
            "meta": self._meta(product, release, generated_by),
            "product": self._product_section(product, release),
            "remote_processing": self._remote_processing_section(release_id),
            "operators": self._operators_section(product),
            "classification": self._classification_section(product, release),
            "risk": self._risk_section(release_id, product.id),
            "annex_part1": annex["part1"],
            "annex_part2": annex["part2"],
            "coverage": coverage,
            "sbom": self._sbom_section(release_id),
            "vuln": self._vuln_section(release_id, release),
            "conformity": self._conformity_section(release, product.id),
            "doc": self._doc_section(release),
            "techdoc": self._techdoc_section(release, product, release_id),
            "evidence": self._evidence_section(release_id),
            "user_info": self._user_info_section(product),
            "support": self._support_section(release_id, product.id),
            "mods": self._mods_section(release_id),
            "cvd": self._cvd_section(product.id, release_id),
            "audit": self._audit_section(product.id, release_id),
            "signoff": self._signoff_section(release_id),
        }

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _meta(self, product: Product, release: ProductRelease, generated_by: str | None) -> dict:
        now = datetime.now(UTC)
        # Human report id derived from product code + year-month (no formal entity yet).
        rid = f"RPT-{(product.product_code or 'PRODUCT').upper()}-{now:%Y-%m}"
        # Overall status stamp drives the cover badge.
        gate = self._get_gate(release.id)
        if release.placed_on_market_date:
            status = "Placed on market"
        elif gate and str(gate.status) == "approved":
            status = "Conformity declared"
        else:
            status = "In progress — not yet declared"
        return {
            "report_id": rid,
            "version": "1.0",
            "generated_at": now.strftime("%Y-%m-%d %H:%M UTC"),
            "generated_by": generated_by or "—",
            "data_snapshot_at": now.strftime("%Y-%m-%d %H:%M UTC"),
            "tool_name": "CRANE — CRA Norm Engine",
            "status": status,
            "confidentiality": "Confidential — for conformity assessment purposes",
        }

    def _product_section(self, product: Product, release: ProductRelease) -> dict:
        rpe_in_scope = any(
            str(getattr(e, "classification", "")) == "cra_art_3_2_in_scope"
            for e in product.remote_processing_elements
        )
        return {
            "name": product.name,
            "model": product.product_code,
            "hardware_version": release.hardware_version,
            "firmware_version": release.software_version or release.user_version or f"v{release.system_version}",
            "product_type": _fmt_status(product.product_type),
            "intended_use": product.intended_use,
            "is_embedded": _fmt_bool(product.is_embedded_product),
            "is_pre_cra": _fmt_bool(product.is_pre_cra),
            "remote_processing_in_scope": "Yes" if rpe_in_scope else "No / none recorded",
        }

    def _operators_section(self, product: Product) -> dict:
        return {
            "manufacturer": {
                "name": product.manufacturer_name,
                "contact_email": product.security_contact_email,
                "contact_url": product.security_contact_url,
            },
            "authorised_rep": product.authorised_representative or _PLACEHOLDER,
            "importers": product.importers or _PLACEHOLDER,
            "distributors": product.distributors or _PLACEHOLDER,
            "spoc": product.single_point_of_contact or _PLACEHOLDER,
        }

    def _classification_section(self, product: Product, release: ProductRelease) -> dict:
        evaluation = self.db.scalar(
            select(ProductScopeEvaluation)
            .where(ProductScopeEvaluation.product_id == product.id)
            .order_by(ProductScopeEvaluation.created_at.desc())
        )
        classification = _fmt_status(str(product.current_classification))
        is_critical = str(product.current_classification) == "critical"
        return {
            "classification": classification,
            "is_critical": "Yes" if is_critical else "No",
            "scope_status": _fmt_status(product.scope_status),
            "annex_item": product.annex_category or _PLACEHOLDER,
            "rationale": evaluation.rationale if evaluation else None,
            "conformity_route": _fmt_status(str(release.conformity_route_snapshot)),
        }

    def _risk_section(self, release_id: UUID, product_id: UUID) -> dict:
        assessments = self._get_risk_assessments(release_id)
        if not assessments:
            return {"available": False}
        latest = assessments[0]
        approver = self.db.get(User, latest.reviewer_user_id) if latest.reviewer_user_id else None
        # Detailed risk register, ordered most-severe first.
        items = sorted(
            latest.risk_items,
            key=lambda it: _RISK_RANK.get(str(it.risk_level), 0),
            reverse=True,
        )
        item_rows = [
            {
                "title": it.title,
                "threat": it.threat_scenario,
                "asset": it.asset_affected,
                "likelihood": _fmt_status(str(it.likelihood)),
                "impact": _fmt_status(str(it.impact)),
                "risk_level": _fmt_status(str(it.risk_level)),
                "risk_bucket": _RISK_BUCKET.get(str(it.risk_level), "warn"),
                "residual": _fmt_status(str(it.residual_risk_level)) if it.residual_risk_level else "—",
                "residual_bucket": _RISK_BUCKET.get(str(it.residual_risk_level), "na") if it.residual_risk_level else "na",
                "mitigation": it.mitigation_plan,
                "status": _fmt_status(str(it.status)) if it.status else "—",
            }
            for it in items
        ]
        return {
            "available": True,
            "methodology": latest.methodology,
            "summary": latest.summary,
            "status": _fmt_status(str(latest.status)),
            "approved_by": approver.email if approver else None,
            "approved_at": _fmt_date(latest.approved_at),
            "item_count": len(latest.risk_items),
            "title": latest.title,
            "count": len(assessments),
            "items": item_rows,
        }

    def _annex_sections(self, release_id: UUID) -> dict:
        rows = self.db.execute(
            select(RequirementMapping, AnnexRequirement)
            .join(AnnexRequirement, RequirementMapping.annex_requirement_id == AnnexRequirement.id)
            .where(RequirementMapping.product_release_id == release_id)
            .options(selectinload(RequirementMapping.artifact_links).selectinload(
                RequirementMappingArtifactLink.artifact
            ))
            # Natural order (Part I before II, then by trailing number) — length
            # before code keeps 1–9 ahead of 10+.
            .order_by(
                AnnexRequirement.annex_part.asc(),
                func.length(AnnexRequirement.code).asc(),
                AnnexRequirement.code.asc(),
            )
        ).all()
        # Applicability decisions for this release, keyed by annex_requirement_id,
        # so each requirement row can show its applicability + rationale alongside
        # the existing implementation-status coverage.
        decisions = {
            d.annex_requirement_id: d
            for d in self.db.scalars(
                select(ProductRequirementDecision).where(
                    ProductRequirementDecision.product_release_id == release_id
                )
            ).all()
        }
        part1: list[dict] = []
        part2: list[dict] = []
        for mapping, req in rows:
            impl = str(mapping.implementation_status)
            bucket = _IMPL_TO_COVERAGE.get(impl, "partial")
            decision = decisions.get(req.id)
            linked_artifacts = [
                link.artifact.title for link in mapping.artifact_links if link.artifact is not None
            ]
            entry = {
                "code": req.code,
                "title": req.title,
                "status": _COVERAGE_LABEL[bucket],
                "bucket": bucket,
                "evidence": mapping.evidence_summary or "—",
                "applicability": _fmt_status(str(decision.applicability_decision)) if decision else _PLACEHOLDER,
                "rationale": decision.rationale if decision and decision.rationale else _PLACEHOLDER,
                "linked_artifacts": linked_artifacts,
            }
            if str(req.annex_part) == "part_ii":
                part2.append(entry)
            else:
                part1.append(entry)
        return {"part1": part1, "part2": part2}

    def _coverage(self, entries: list[dict]) -> dict:
        total = len(entries)
        counts = {"compliant": 0, "partial": 0, "gap": 0, "na": 0}
        for e in entries:
            counts[e["bucket"]] = counts.get(e["bucket"], 0) + 1
        pct = {k: (round(v / total * 100) if total else 0) for k, v in counts.items()}
        return {"total": total, "counts": counts, "pct": pct, "available": total > 0}

    def _sbom_section(self, release_id: UUID) -> dict:
        records = self._get_sbom_records(release_id)
        if not records:
            return {"available": False}
        sbom = records[0]
        findings = sbom.analysis_findings or {}
        ntia = findings.get("ntia_compliant") if isinstance(findings, dict) else None
        # Top components & known issues — surfaces sbom_vulnerability_findings rows
        # so reviewers can see exactly which dependency/version pairs are flagged.
        vuln_findings = self._get_sbom_vulnerability_findings(sbom.id)
        finding_rows = [
            {
                "component": f.component_name,
                "version": f.component_version or "—",
                "vuln_id": f.vuln_id,
                "severity": _fmt_status(f.severity) if f.severity else "—",
                "severity_bucket": _VULN_SEVERITY_BUCKET.get(str(f.severity), "warn"),
                "cvss_score": f.cvss_score,
                "summary": f.summary or "—",
                "fix_status": _fmt_status(str(f.linked_report.status)) if f.linked_report else "Not yet triaged",
            }
            for f in sorted(
                vuln_findings,
                key=lambda f: _SEVERITY_RANK.get(str(f.severity), 0),
                reverse=True,
            )
        ]
        return {
            "available": True,
            "id": sbom.file_name or str(sbom.id),
            "format": f"{_fmt_status(str(sbom.format))} {sbom.spec_version or ''}".strip(),
            "component_count": sbom.component_count,
            "quality_score": sbom.quality_score,
            "ntia_compliant": _fmt_bool(ntia) if ntia is not None else "—",
            # CycloneDX without a dependency graph lists components flat — report
            # the count honestly rather than a fabricated direct/transitive split.
            "direct_transitive": f"{sbom.component_count or 0} components (flat SBOM — no dependency graph)",
            "findings": finding_rows,
        }

    def _vuln_section(self, release_id: UUID, release: ProductRelease) -> dict:
        reports = self._get_vulnerability_reports(release_id)
        open_crit = sum(
            1 for v in reports
            if str(v.severity) == "critical" and str(v.status) in _VULN_OPEN
        )
        open_high = sum(
            1 for v in reports
            if str(v.severity) == "high" and str(v.status) in _VULN_OPEN
        )
        resolved = [v for v in reports if v.fixed_at is not None]
        # MTTR over resolved reports with a discovered_at (best effort, in days).
        deltas = [
            (v.fixed_at - v.discovered_at).days
            for v in resolved
            if v.discovered_at is not None and v.fixed_at is not None
        ]
        mttr = f"{round(sum(deltas) / len(deltas))} days" if deltas else "—"
        # VEX breakdown.
        vex: dict[str, int] = {}
        for v in reports:
            key = str(v.vex_status) if v.vex_status else "unassessed"
            vex[key] = vex.get(key, 0) + 1
        # Top items by severity (then most recent).
        top = sorted(
            reports,
            key=lambda v: (_SEVERITY_RANK.get(str(v.severity), 0)),
            reverse=True,
        )[:5]
        top_rows = [
            {
                "cve": (v.cve_ids_json[0] if v.cve_ids_json else v.title[:40]),
                "title": v.title,
                "severity": _fmt_status(str(v.severity)) if v.severity else "—",
                "vex": _fmt_status(str(v.vex_status)) if v.vex_status else "—",
            }
            for v in top
        ]
        return {
            "available": bool(reports),
            "total": len(reports),
            "open_critical": open_crit,
            "open_high": open_high,
            "resolved_count": len(resolved),
            "mttr": mttr,
            "vex_breakdown": {_fmt_status(k): n for k, n in vex.items()},
            "kev_flag": bool(release.has_known_exploitable_vulnerabilities),
            "kev_notes": release.kev_notes,
            "top": top_rows,
        }

    def _conformity_section(self, release: ProductRelease, product_id: UUID) -> dict:
        certs = self._get_certification_records(product_id)
        return {
            "route": _fmt_status(str(release.conformity_route_snapshot)),
            "module": release.conformity_module or _PLACEHOLDER,
            "notified_body": release.eu_doc_notified_body
            or (certs[0].certification_body_name if certs else None),
            "nb_number": release.notified_body_number or _PLACEHOLDER,
            "standards": release.standards_applied or _PLACEHOLDER,
            "certifications": [
                {
                    "scheme": c.certification_scheme_label or _fmt_status(str(c.certification_scheme)),
                    "body": c.certification_body_name,
                    "number": c.certificate_number,
                    "status": _fmt_status(str(c.status)),
                    "valid_until": _fmt_date(c.valid_until_date),
                }
                for c in certs
            ],
        }

    def _doc_section(self, release: ProductRelease) -> dict:
        return {
            "reference_no": release.eu_doc_number,
            "date": _fmt_date(release.eu_doc_date),
            "notified_body": release.eu_doc_notified_body,
            "signatory": release.eu_doc_signatory or _PLACEHOLDER,
            "simplified_url": release.eu_doc_url or _PLACEHOLDER,
            "status": release.eu_doc_status or _PLACEHOLDER,
            "ce_marking": release.ce_marking_info or _PLACEHOLDER,
        }

    def _techdoc_section(self, release: ProductRelease, product: Product, release_id: UUID) -> list[dict]:
        gate = self._get_gate(release_id)
        items = self._get_gate_items(gate.id) if gate else []
        accepted = {
            str(i.code) for i in items if str(getattr(i, "status", "")) in ("accepted", "waived") and i.code
        }
        has_risk = bool(self._get_risk_assessments(release_id))
        has_sbom = bool(self._get_sbom_records(release_id))
        support = self._get_support_periods(release_id, product.id)
        has_support_rationale = any((s.justification_text or "").strip() for s in support)
        doc_status = "Present" if release.eu_doc_number else "Draft"
        # Annex VII elements (1–8) with a present/partial/placeholder status.
        return [
            {"n": 1, "name": "General product description, versions, user info", "status": "Present"},
            {"n": 2, "name": "Design/development & vulnerability-handling processes",
             "status": "Present" if ("technical_documentation" in accepted or items) else "Partial"},
            {"n": 3, "name": "Cybersecurity risk assessment", "status": "Present" if has_risk else "Missing"},
            {"n": 4, "name": "Support-period determination rationale",
             "status": "Present" if has_support_rationale else "Partial"},
            {"n": 5, "name": "Standards / specifications applied",
             "status": "Present" if release.standards_applied else _PLACEHOLDER},
            {"n": 6, "name": "Test reports", "status": "Present" if "test_report" in accepted else "Partial"},
            {"n": 7, "name": "Copy of EU declaration of conformity", "status": doc_status},
            {"n": 8, "name": "Software bill of materials", "status": "Present" if has_sbom else "Missing"},
        ]

    def _evidence_section(self, release_id: UUID) -> dict:
        """Summarise integrity + retention of the evidence attached to this release."""
        gate = self._get_gate(release_id)
        items = self._get_gate_items(gate.id) if gate else []
        revisions = {}
        for item in items:
            for link in item.evidence_links:
                rev = link.artifact_revision
                if rev is not None:
                    revisions[rev.id] = rev
        revs = list(revisions.values())
        if not revs:
            return {"available": False}
        artifacts = {r.artifact_id: r.artifact for r in revs if r.artifact is not None}
        retention_dates = [a.retention_until for a in artifacts.values() if a.retention_until]
        return {
            "available": True,
            "total": len(revs),
            "retained": sum(1 for r in revs if str(r.source_type) == "upload" and r.storage_path),
            "external": sum(1 for r in revs if str(r.source_type) == "external_link"),
            "verified": sum(1 for r in revs if r.integrity_status == "verified"),
            "failed": sum(1 for r in revs if r.integrity_status in ("failed", "missing")),
            "legal_holds": sum(1 for a in artifacts.values() if a.legal_hold),
            "earliest_retention": _fmt_date(min(retention_dates)) if retention_dates else "—",
        }

    def _support_section(self, release_id: UUID, product_id: UUID) -> dict:
        records = self._get_support_periods(release_id, product_id)
        active = next((r for r in records if r.is_active), records[0] if records else None)
        if active is None:
            return {"available": False}
        return {
            "available": True,
            "start": _fmt_date(active.support_start_date),
            "end": _fmt_date(active.support_end_date),
            "type": _fmt_status(str(active.support_type)),
            "notify_before_days": active.notify_before_days,
            "justification": active.justification_text,
        }

    def _mods_section(self, release_id: UUID) -> list[dict]:
        changes = self._get_changes(release_id)
        rows = []
        for c in changes:
            assessment = c.assessment
            substantial = bool(assessment and assessment.is_substantial)
            rows.append({
                "date": _fmt_date(c.change_date),
                "description": c.title,
                "type": _fmt_status(str(c.change_type)),
                "outcome": "Substantial" if substantial else "Not substantial",
                "substantial": substantial,
            })
        return rows

    def _cvd_section(self, product_id: UUID, release_id: UUID) -> dict:
        policy = self.db.scalar(
            select(CvdPolicy).where(CvdPolicy.product_id == product_id).order_by(CvdPolicy.created_at.desc())
        )
        incidents = self.db.scalars(
            select(IncidentReport)
            .where(IncidentReport.product_release_id == release_id)
            .order_by(IncidentReport.created_at.desc())
        ).all()
        last = None
        for inc in incidents:
            stamp = inc.enisa_early_warning_sent_at or inc.enisa_initial_report_sent_at
            if stamp:
                last = f"{_fmt_date(stamp)} — {inc.title}"
                break
        return {
            "available": policy is not None or bool(incidents),
            "policy_status": _fmt_status(str(policy.status)) if policy else None,
            "policy_url": policy.policy_url if policy else None,
            "contact": policy.contact_email if policy else None,
            "csirt_coordinator": (policy.coordinator_csirt if policy else None) or _PLACEHOLDER,
            "playbook_ready": any(
                i.enisa_early_warning_sent_at or i.enisa_initial_report_sent_at for i in incidents
            ),
            "last_notification": last,
            "incident_count": len(incidents),
            "safe_harbor": _fmt_bool(policy.safe_harbor) if policy else "—",
            "acknowledgement_offered": _fmt_bool(policy.acknowledgement_offered) if policy else "—",
            "disclosure_window_days": policy.disclosure_window_days if policy else None,
            "response_sla_hours": policy.response_sla_hours if policy else None,
            "scope_description": (policy.scope_description if policy else None) or _PLACEHOLDER,
            "out_of_scope_description": (policy.out_of_scope_description if policy else None) or _PLACEHOLDER,
            "supported_versions": (policy.supported_versions if policy else None) or _PLACEHOLDER,
            "security_txt_url": (policy.security_txt_url if policy else None) or _PLACEHOLDER,
            "pgp_key_url": (policy.pgp_key_url if policy else None) or _PLACEHOLDER,
            "bug_bounty_url": (policy.bug_bounty_url if policy else None) or _PLACEHOLDER,
        }

    def _remote_processing_section(self, release_id: UUID) -> dict:
        """Remote processing solutions (Art. 3(2)) linked to this release, each
        with its in/out-of-scope classification and the rationale behind it."""
        release = self._get_release(release_id)
        elements = sorted(release.release_remote_processing_elements, key=lambda e: e.name)
        bucket_map = {
            "cra_art_3_2_in_scope": "warn",
            "out_of_scope": "ok",
            "third_party_component": "na",
            "requires_legal_assessment": "warn",
            "not_assessed": "na",
        }
        items = [
            {
                "name": e.name,
                "provider": e.provider_name or "—",
                "data_processed": e.data_processed or "—",
                "location": e.geographic_location or "—",
                "criticality": e.criticality or "—",
                "classification": _fmt_status(str(e.classification)),
                "classification_bucket": bucket_map.get(str(e.classification), "na"),
                "rationale": e.classification_rationale or _PLACEHOLDER,
                "necessary": _fmt_bool(e.is_necessary_for_product_function),
                "bidirectional": _fmt_bool(e.has_bidirectional_exchange),
            }
            for e in elements
        ]
        return {"available": bool(items), "items": items}

    def _audit_section(self, product_id: UUID, release_id: UUID) -> list[dict]:
        events = self.db.scalars(
            select(AuditLogEvent)
            .where(or_(AuditLogEvent.entity_id == release_id, AuditLogEvent.entity_id == product_id))
            .order_by(AuditLogEvent.occurred_at.desc())
            .limit(8)
        ).all()
        actor_ids = {e.actor_user_id for e in events if e.actor_user_id}
        actors = {}
        if actor_ids:
            for uid, email in self.db.execute(
                select(User.id, User.email).where(User.id.in_(actor_ids))
            ).all():
                actors[uid] = email
        return [
            {
                "at": e.occurred_at.strftime("%Y-%m-%d %H:%M") if e.occurred_at else "—",
                "actor": actors.get(e.actor_user_id, "system"),
                "action": f"{_fmt_status(e.action_type)} · {_fmt_status(e.entity_type)}",
            }
            for e in events
        ]

    def _signoff_section(self, release_id: UUID) -> dict:
        release = self._get_release(release_id)
        gate = self._get_gate(release_id)
        approver = None
        if gate and gate.approved_by_user_id:
            user = self.db.get(User, gate.approved_by_user_id)
            approver = {
                "email": user.email if user else None,
                "at": _fmt_date(gate.approved_at),
            }
        return {
            "gate_approver": approver,
            "compliance_lead": release.signoff_compliance_lead or _PLACEHOLDER,
            "notified_body_reviewer": release.signoff_notified_body_reviewer or _PLACEHOLDER,
            "executive": release.signoff_executive or _PLACEHOLDER,
        }

    def _user_info_section(self, product: Product) -> dict:
        """Annex II — information & instructions to the user (checklist)."""
        items = product.annex_ii_json or []
        return {"available": bool(items), "items": items}

    # ------------------------------------------------------------------
    # Individual queries
    # ------------------------------------------------------------------

    def _get_release(self, release_id: UUID) -> ProductRelease:
        release = self.db.get(ProductRelease, release_id)
        if release is None:
            raise NotFoundException("Product release not found")
        return release

    def _get_gate(self, release_id: UUID) -> ReleaseGate | None:
        return self.db.scalar(select(ReleaseGate).where(ReleaseGate.product_release_id == release_id))

    def _get_gate_items(self, gate_id: UUID) -> list[ReleaseGateItem]:
        return list(
            self.db.scalars(
                select(ReleaseGateItem)
                .where(ReleaseGateItem.release_gate_id == gate_id)
                .order_by(ReleaseGateItem.sort_order)
            ).all()
        )

    def _get_changes(self, release_id: UUID) -> list[Change]:
        return list(
            self.db.scalars(
                select(Change)
                .where(Change.product_version_id == release_id)
                .options(selectinload(Change.assessment))
                .order_by(Change.change_date.desc())
            ).all()
        )

    def _get_risk_assessments(self, release_id: UUID) -> list[RiskAssessment]:
        return list(
            self.db.scalars(
                select(RiskAssessment)
                .where(RiskAssessment.product_release_id == release_id)
                .options(selectinload(RiskAssessment.risk_items))
                .order_by(RiskAssessment.created_at.desc())
            ).all()
        )

    def _get_sbom_records(self, release_id: UUID) -> list[SbomRecord]:
        return list(
            self.db.scalars(
                select(SbomRecord)
                .where(SbomRecord.product_release_id == release_id)
                .order_by(SbomRecord.created_at.desc())
            ).all()
        )

    def _get_sbom_vulnerability_findings(self, sbom_record_id: UUID) -> list[SbomVulnerabilityFinding]:
        return list(
            self.db.scalars(
                select(SbomVulnerabilityFinding)
                .where(SbomVulnerabilityFinding.sbom_record_id == sbom_record_id)
                .options(selectinload(SbomVulnerabilityFinding.linked_report))
                .order_by(SbomVulnerabilityFinding.created_at.desc())
            ).all()
        )

    def _get_vulnerability_reports(self, release_id: UUID) -> list[VulnerabilityReport]:
        return list(
            self.db.scalars(
                select(VulnerabilityReport)
                .where(VulnerabilityReport.product_release_id == release_id)
                .order_by(VulnerabilityReport.created_at.desc())
            ).all()
        )

    def _get_support_periods(self, release_id: UUID, product_id: UUID) -> list[SupportPeriodRecord]:
        return list(
            self.db.scalars(
                select(SupportPeriodRecord)
                .where(
                    (SupportPeriodRecord.product_release_id == release_id)
                    | (
                        (SupportPeriodRecord.product_id == product_id)
                        & (SupportPeriodRecord.product_release_id.is_(None))
                    )
                )
                .order_by(SupportPeriodRecord.support_start_date.desc())
            ).all()
        )

    def _get_certification_records(self, product_id: UUID) -> list[CertificationRecord]:
        return list(
            self.db.scalars(
                select(CertificationRecord)
                .where(CertificationRecord.product_id == product_id)
                .order_by(CertificationRecord.created_at.desc())
            ).all()
        )

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_html(self, data: dict) -> str:
        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )
        env.filters["fmt_date"] = _fmt_date
        env.filters["fmt_status"] = _fmt_status
        env.filters["fmt_bool"] = _fmt_bool
        # Expose the placeholder sentinel so the template can detect gaps.
        env.globals["PLACEHOLDER"] = _PLACEHOLDER
        template = env.get_template("release_report.html")
        return template.render(**data)

    def _html_to_pdf(self, html: str) -> bytes:
        try:
            from weasyprint import HTML  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "WeasyPrint is not installed. Add 'weasyprint' to requirements.txt."
            ) from exc
        return HTML(string=html).write_pdf()


# ------------------------------------------------------------------
# Template helper functions (also registered as Jinja2 filters)
# ------------------------------------------------------------------

def _fmt_date(value: object) -> str:
    """Format a date/datetime/string as DD Mon YYYY, or '—' if missing."""
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y")
    if isinstance(value, date):
        return value.strftime("%d %b %Y")
    try:
        return date.fromisoformat(str(value)[:10]).strftime("%d %b %Y")
    except ValueError:
        return str(value)


def _fmt_status(value: str | None) -> str:
    """Convert a snake_case enum value to a Title Case label."""
    if not value:
        return "—"
    # Enum reprs arrive as 'EnumClass.member' or plain 'member'; keep the member.
    text = str(value).split(".")[-1]
    return text.replace("_", " ").title()


def _fmt_bool(value: object) -> str:
    """Render a boolean as Yes / No / Unknown."""
    if value is None:
        return "Unknown"
    return "Yes" if value else "No"
