# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""
The single, authoritative definition of per-product *compliance readiness*.

Readiness is anchored on **Annex I Part I** essential-requirement coverage for a
product's latest release. "Met" reuses the exact rule the requirement matrix
already enforces (RequirementMappingService._is_finalized via release_matrix()),
so the dashboard number and the requirement matrix can never disagree.

Two numbers are reported per product:
  * assessed_pct — % of Part I requirements with an applicability decision made
  * met_pct      — % fully finalized (the headline / ring value)

Operational signals (open critical vulns, unapproved risk, expired support,
changes needing action) are returned as *informational flags only* — they never
change the coverage percentages.
"""
from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.change import Change
from app.models.enums import (
    AnnexPart,
    ChangeStatus,
    ReleaseStatus,
    RequirementApplicabilityDecision,
    RequirementAssessmentStatus,
    RiskAssessmentStatus,
    SecurityUpdateSeverity,
    VulnerabilityLifecycleStatus,
)
from app.models.product import Product, ProductRelease
from app.models.requirement_assessment import ReleaseRequirementAssessment
from app.models.risk_assessment import RiskAssessment
from app.models.support_period_record import SupportPeriodRecord
from app.models.vulnerability_report import VulnerabilityReport
from app.repositories.product_repository import ProductRepository
from app.schemas.product_readiness import (
    ConformanceSummary,
    ProductReadinessRead,
    ReadinessCoverage,
    ReleaseReadinessRead,
)
from app.services.requirement_mapping_service import RequirementMappingService

# Release statuses that mean the release is on the EU market.
_RELEASED_STATUSES = {ReleaseStatus.placed_on_market, ReleaseStatus.released}

logger = logging.getLogger(__name__)

# Non-terminal vulnerability states that still count as "open".
_VULN_TERMINAL = {
    VulnerabilityLifecycleStatus.disclosed,
    VulnerabilityLifecycleStatus.retired,
}
# Risk assessment states that are NOT yet approved.
_RISK_UNAPPROVED = {RiskAssessmentStatus.draft, RiskAssessmentStatus.in_review}

# Met-percentage thresholds for the derived state label.
_SUBSTANTIALLY_READY_PCT = 80


class ProductReadinessService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.product_repository = ProductRepository(db)
        self.requirement_service = RequirementMappingService(db)

    # ── Coverage ──────────────────────────────────────────────────────────────

    def compute_release_coverage(self, release_id: UUID) -> ReadinessCoverage:
        """
        Annex I Part I coverage for one release.

        Reuses RequirementMappingService.release_matrix() so "met" (finalized)
        follows the same rule the matrix enforces. Only Part I requirements count.
        """
        rows = self.requirement_service.release_matrix(release_id)
        part_i_rows = [
            row for row in rows if row.annex_requirement.annex_part == AnnexPart.part_i
        ]

        total = len(part_i_rows)
        assessed = sum(
            1
            for row in part_i_rows
            if row.applicability_decision != RequirementApplicabilityDecision.undecided
        )
        met = sum(1 for row in part_i_rows if row.finalized)

        return ReadinessCoverage(
            total=total,
            assessed=assessed,
            met=met,
            assessed_pct=round(assessed / total * 100) if total else 0,
            met_pct=round(met / total * 100) if total else 0,
        )

    # ── Per-release readiness (the honest unit) ──────────────────────────────

    def compute_release_readiness(self, release: ProductRelease) -> ReleaseReadinessRead:
        """Readiness of a single release, with its own coverage + approval."""
        coverage = self.compute_release_coverage(release.id)
        return ReleaseReadinessRead(
            release_id=release.id,
            version_label=self._version_label(release),
            system_version=release.system_version,
            release_status=str(release.release_status),
            is_released=release.release_status in _RELEASED_STATUSES,
            coverage=coverage,
            state=self._derive_state(coverage),
            is_approved=self._is_release_approved(release.id),
        )

    def compute_product_readiness(self, product: Product) -> ProductReadinessRead:
        """
        A product grouping each of its releases' readiness.

        Readiness is genuinely per-release, so every release gets its own row.
        The *representative* release (for portfolio roll-ups) is the latest
        released one, falling back to the latest by version.
        """
        # `releases` is pre-sorted ascending by system_version; newest first here.
        releases_desc = list(reversed(product.releases))
        release_rows = [self.compute_release_readiness(r) for r in releases_desc]

        representative = self._representative_release(product)
        representative_id = representative.id if representative else None
        # Conformance only means something for an in-scope product that actually
        # has a released release; otherwise there is no market obligation to meet.
        is_conformant = (
            product.scope_status == "in_scope"
            and representative is not None
            and representative.release_status in _RELEASED_STATUSES
            and self._is_release_approved(representative.id)
        )

        flags = self._secondary_flags(product.id)
        return ProductReadinessRead(
            product_id=product.id,
            product_code=product.product_code,
            name=product.name,
            scope_status=product.scope_status,
            releases=release_rows,
            representative_release_id=representative_id,
            is_conformant=is_conformant,
            **flags,
        )

    @staticmethod
    def _version_label(release: ProductRelease) -> str:
        label = (release.user_version or "").strip()
        return label if label else f"v{release.system_version}"

    def _representative_release(self, product: Product) -> ProductRelease | None:
        """
        The release that represents the product for roll-ups: the latest
        *released* release (highest system_version among on-market ones),
        falling back to the latest release overall.
        """
        if not product.releases:
            return None
        released = [
            r for r in product.releases if r.release_status in _RELEASED_STATUSES
        ]
        pool = released or list(product.releases)
        # releases are ascending by system_version, so max() gives the newest.
        return max(pool, key=lambda r: r.system_version)

    def _is_release_approved(self, release_id: UUID) -> bool:
        """
        Whether a release's requirement assessment is formally approved.

        Mirrors requirement_assessment_service: no row == unapproved draft.
        """
        assessment = self.db.scalar(
            select(ReleaseRequirementAssessment).where(
                ReleaseRequirementAssessment.product_release_id == release_id
            )
        )
        return (
            assessment is not None
            and assessment.status == RequirementAssessmentStatus.approved
        )

    def conformance_summary(self) -> ConformanceSummary:
        """
        Portfolio conformance for the dashboard pie.

        Conformant = in-scope product whose **latest released** release has an
        APPROVED requirement assessment. Products that are out of scope, or have
        nothing released yet, carry no market obligation and are excluded from
        the percentage.
        """
        rows = self.list_product_readiness()
        total = len(rows)

        def has_released(row: ProductReadinessRead) -> bool:
            return any(rel.is_released for rel in row.releases)

        counted = [
            r for r in rows if r.scope_status == "in_scope" and has_released(r)
        ]
        in_scope = len(counted)
        out_of_scope = total - in_scope
        conformant = sum(1 for r in counted if r.is_conformant)
        not_conformant = in_scope - conformant
        return ConformanceSummary(
            total=total,
            in_scope=in_scope,
            out_of_scope=out_of_scope,
            conformant=conformant,
            not_conformant=not_conformant,
            conformant_pct=round(conformant / in_scope * 100) if in_scope else 0,
        )

    def list_product_readiness(self) -> list[ProductReadinessRead]:
        """Readiness for every product, grouped by product (name-sorted)."""
        products = self.product_repository.list_all()
        rows = [self.compute_product_readiness(p) for p in products]
        rows.sort(key=lambda r: r.name.lower())
        return rows

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _derive_state(coverage: ReadinessCoverage) -> str:
        """State label for a single release from its coverage."""
        if coverage.assessed == 0:
            return "not_started"
        if coverage.met_pct >= 100:
            return "ready"
        if coverage.met_pct >= _SUBSTANTIALLY_READY_PCT:
            return "substantially_ready"
        return "in_progress"

    def _secondary_flags(self, product_id: UUID) -> dict[str, object]:
        """
        Operational warning signals for a product, scoped to its releases.

        Informational only — these never alter the coverage percentages. Filters
        mirror the portfolio dashboard's own queries.
        """
        # Open critical vulnerabilities across this product's releases.
        open_critical = (
            self.db.scalar(
                select(func.count())
                .select_from(VulnerabilityReport)
                .join(ProductRelease, VulnerabilityReport.product_release_id == ProductRelease.id)
                .where(
                    ProductRelease.product_id == product_id,
                    VulnerabilityReport.severity == SecurityUpdateSeverity.critical,
                    VulnerabilityReport.status.notin_(_VULN_TERMINAL),
                )
            )
            or 0
        )

        # Any unapproved (draft / in_review) risk assessment for this product.
        risk_unapproved = (
            self.db.scalar(
                select(func.count())
                .select_from(RiskAssessment)
                .where(
                    RiskAssessment.product_id == product_id,
                    RiskAssessment.status.in_(_RISK_UNAPPROVED),
                )
            )
            or 0
        ) > 0

        # Any support period already past its end date.
        support_expired = (
            self.db.scalar(
                select(func.count())
                .select_from(SupportPeriodRecord)
                .where(
                    SupportPeriodRecord.product_id == product_id,
                    SupportPeriodRecord.support_end_date < date.today(),
                )
            )
            or 0
        ) > 0

        # Any change on this product's releases awaiting compliance action.
        change_action = (
            self.db.scalar(
                select(func.count(distinct(Change.id)))
                .join(ProductRelease, Change.product_version_id == ProductRelease.id)
                .where(
                    ProductRelease.product_id == product_id,
                    Change.status == ChangeStatus.action_required,
                )
            )
            or 0
        ) > 0

        return {
            "has_open_critical_vuln": open_critical > 0,
            "open_critical_vuln_count": int(open_critical),
            "risk_unapproved": risk_unapproved,
            "support_expired": support_expired,
            "change_action_required": change_action,
        }
