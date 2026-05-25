"""
Release Compliance Report Service.

Assembles all CRA-relevant data for a product release and renders it as a
PDF document using a Jinja2 HTML template and WeasyPrint.

Usage:
    from app.services.release_report_service import ReleaseReportService
    pdf_bytes = ReleaseReportService(db).generate_pdf(release_id)
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.certification_record import CertificationRecord
from app.models.change import Change, SubstantialModificationAssessment
from app.models.product import Product, ProductRelease
from app.models.release_gate import ReleaseGate, ReleaseGateItem
from app.models.risk_assessment import RiskAssessment
from app.models.risk_item import RiskItem
from app.models.sbom_record import SbomRecord
from app.models.security_update import SecurityUpdate
from app.models.support_period_record import SupportPeriodRecord
from app.models.vulnerability_report import VulnerabilityReport

logger = logging.getLogger(__name__)

# Path to the Jinja2 templates directory (one level up from this file → app/templates/)
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class ReleaseReportService:
    """Generates a PDF compliance report for a single product release."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_pdf(self, release_id: UUID) -> bytes:
        """
        Return the rendered PDF as raw bytes.
        Raises NotFoundException if the release does not exist.
        Raises RuntimeError if WeasyPrint is unavailable.
        """
        data = self._build_report_data(release_id)
        html = self._render_html(data)
        return self._html_to_pdf(html)

    def generate_filename(self, release_id: UUID) -> str:
        """Return a safe filename for Content-Disposition."""
        release = self._get_release(release_id)
        product = self.db.get(Product, release.product_id)
        product_code = (product.product_code if product else "product").lower().replace(" ", "-")
        version = f"v{release.system_version}"
        return f"cra-report-{product_code}-{version}.pdf"

    # ------------------------------------------------------------------
    # Data assembly
    # ------------------------------------------------------------------

    def _build_report_data(self, release_id: UUID) -> dict:
        """Collect all report data in a single dict passed to the template."""
        release = self._get_release(release_id)
        product = self.db.get(Product, release.product_id)
        if product is None:
            raise NotFoundException("Product not found for this release")

        gate = self._get_gate(release_id)
        gate_items = self._get_gate_items(gate.id) if gate else []
        changes = self._get_changes(release_id)
        risk_assessments = self._get_risk_assessments(release_id, product.id)
        sbom_records = self._get_sbom_records(release_id)
        security_updates = self._get_security_updates(release_id)
        vuln_reports = self._get_vulnerability_reports(release_id)
        support_periods = self._get_support_periods(release_id, product.id)
        cert_records = self._get_certification_records(product.id)
        substantiality_analysis = self._get_substantiality_analysis(release.substantiality_analysis_id)

        # Gate item grouped by decision for quick status overview
        gate_summary = _gate_summary(gate_items)

        # Security update stats
        max_cvss = max((u.cvss_score for u in security_updates if u.cvss_score is not None), default=None)

        # Vulnerability report open count
        open_vulns = [v for v in vuln_reports if getattr(v, "status", None) not in ("closed", "resolved")]

        return {
            "product": product,
            "release": release,
            "gate": gate,
            "gate_items": gate_items,
            "gate_summary": gate_summary,
            "changes": changes,
            "substantiality_analysis": substantiality_analysis,
            "risk_assessments": risk_assessments,
            "sbom_records": sbom_records,
            "security_updates": security_updates,
            "max_cvss": max_cvss,
            "vuln_reports": vuln_reports,
            "open_vuln_count": len(open_vulns),
            "support_periods": support_periods,
            "cert_records": cert_records,
            "generated_at": date.today().isoformat(),
            "tool_name": "CRA Compliance Tool",
        }

    # ------------------------------------------------------------------
    # Individual queries (each isolated for clarity and testability)
    # ------------------------------------------------------------------

    def _get_release(self, release_id: UUID) -> ProductRelease:
        release = self.db.get(ProductRelease, release_id)
        if release is None:
            raise NotFoundException("Product release not found")
        return release

    def _get_gate(self, release_id: UUID) -> ReleaseGate | None:
        return self.db.scalar(
            select(ReleaseGate).where(ReleaseGate.product_release_id == release_id)
        )

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

    def _get_risk_assessments(self, release_id: UUID, product_id: UUID) -> list[RiskAssessment]:
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

    def _get_security_updates(self, release_id: UUID) -> list[SecurityUpdate]:
        return list(
            self.db.scalars(
                select(SecurityUpdate)
                .where(SecurityUpdate.product_release_id == release_id)
                .order_by(SecurityUpdate.created_at.desc())
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
        # Include both release-specific and product-level support period records
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

    def _get_substantiality_analysis(
        self, analysis_id: UUID | None
    ) -> SubstantialModificationAssessment | None:
        if analysis_id is None:
            return None
        return self.db.get(SubstantialModificationAssessment, analysis_id)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_html(self, data: dict) -> str:
        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )
        # Register helper filters
        env.filters["fmt_date"] = _fmt_date
        env.filters["fmt_status"] = _fmt_status
        env.filters["fmt_bool"] = _fmt_bool

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
# Template helper functions (registered as Jinja2 filters)
# ------------------------------------------------------------------

def _fmt_date(value: object) -> str:
    """Format a date/string as DD MMM YYYY, or '—' if missing."""
    if value is None:
        return "—"
    if isinstance(value, date):
        return value.strftime("%-d %b %Y")
    try:
        return date.fromisoformat(str(value)).strftime("%-d %b %Y")
    except ValueError:
        return str(value)


def _fmt_status(value: str | None) -> str:
    """Convert snake_case enum value to Title Case label."""
    if not value:
        return "—"
    return value.replace("_", " ").title()


def _fmt_bool(value: bool | None) -> str:
    """Render a boolean as Yes / No / Unknown."""
    if value is None:
        return "Unknown"
    return "Yes" if value else "No"


def _gate_summary(items: list[ReleaseGateItem]) -> dict:
    """Tally gate item decisions for the overview row."""
    total = len(items)
    accepted = sum(1 for i in items if str(getattr(i, "status", "")) == "accepted")
    rejected = sum(1 for i in items if str(getattr(i, "status", "")) == "rejected")
    pending = sum(1 for i in items if str(getattr(i, "status", "")) in ("pending_review", "needs_update"))
    waived = sum(1 for i in items if str(getattr(i, "status", "")) == "waived")
    return {
        "total": total,
        "accepted": accepted,
        "rejected": rejected,
        "pending": pending,
        "waived": waived,
    }
