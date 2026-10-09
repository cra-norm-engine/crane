# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""Product readiness uses the release matrix's reviewed essential requirements.

Approval snapshots and inherited technical evidence use the same rules as the
assessment screen. Operational flags are informational and do not alter coverage.
"""
from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from sqlalchemy import distinct, func, or_, select
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
from app.models.supplier_assessment import (
    ProductComponentLink,
    SupplierAssessment,
    ThirdPartyComponent,
)
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

    # ── Batched inputs ────────────────────────────────────────────────────────

    def _approved_release_ids(self) -> set[UUID]:
        """Release ids whose requirement assessment is formally approved.

        One query for the whole portfolio, replacing the old per-release
        ``_is_release_approved`` lookup. No row == unapproved (same as before).
        """
        rows = self.db.execute(
            select(ReleaseRequirementAssessment.product_release_id).where(
                ReleaseRequirementAssessment.status
                == RequirementAssessmentStatus.approved
            )
        ).all()
        return {row[0] for row in rows}

    def _secondary_flags_by_product(self) -> dict[UUID, dict[str, object]]:
        """Operational warning signals for every product in four grouped queries.

        Same filters as the previous per-product implementation — just grouped by
        product id instead of one COUNT per product. Informational only; they
        never alter any coverage percentage.
        """
        # Open critical vulnerabilities per product (across its releases).
        vuln_rows = self.db.execute(
            select(
                ProductRelease.product_id,
                func.count().label("cnt"),
            )
            .select_from(VulnerabilityReport)
            .join(
                ProductRelease,
                VulnerabilityReport.product_release_id == ProductRelease.id,
            )
            .where(
                VulnerabilityReport.severity == SecurityUpdateSeverity.critical,
                VulnerabilityReport.status.notin_(_VULN_TERMINAL),
            )
            .group_by(ProductRelease.product_id)
        ).all()
        open_critical_by_product = {row.product_id: int(row.cnt) for row in vuln_rows}

        # Products with any unapproved (draft / in_review) risk assessment.
        risk_rows = self.db.execute(
            select(distinct(RiskAssessment.product_id)).where(
                RiskAssessment.status.in_(_RISK_UNAPPROVED),
            )
        ).all()
        risk_unapproved_products = {row[0] for row in risk_rows}

        # Products with any support period already past its end date.
        support_rows = self.db.execute(
            select(distinct(SupportPeriodRecord.product_id)).where(
                SupportPeriodRecord.support_end_date < date.today(),
            )
        ).all()
        support_expired_products = {row[0] for row in support_rows}

        # Products with any change on their releases awaiting compliance action.
        change_rows = self.db.execute(
            select(distinct(ProductRelease.product_id))
            .select_from(Change)
            .join(ProductRelease, Change.product_version_id == ProductRelease.id)
            .where(Change.status == ChangeStatus.action_required)
        ).all()
        change_action_products = {row[0] for row in change_rows}

        supplier_gap_products: set[UUID] = set()
        active_support_rows = self.db.execute(
            select(
                SupportPeriodRecord.product_id,
                SupportPeriodRecord.product_release_id,
                SupportPeriodRecord.support_end_date,
            ).where(SupportPeriodRecord.is_active.is_(True))
        ).all()
        support_by_release = {
            release_id: end_date
            for _, release_id, end_date in active_support_rows
            if release_id is not None
        }
        support_by_product = {
            product_id: end_date
            for product_id, release_id, end_date in active_support_rows
            if release_id is None
        }
        due_rows = self.db.execute(
            select(ProductRelease.product_id, ProductRelease.id, ProductComponentLink.component_id, ThirdPartyComponent.supplier_id, ThirdPartyComponent.support_end_date)
            .join(ProductComponentLink, ProductComponentLink.product_release_id == ProductRelease.id)
            .join(ThirdPartyComponent, ThirdPartyComponent.id == ProductComponentLink.component_id)
            .where(or_(ProductComponentLink.criticality.in_(["medium", "high"]), ProductComponentLink.is_core_function.is_(True)))
        ).all()
        today = date.today()
        for product_id, release_id, component_id, supplier_id, component_support_end in due_rows:
            product_support_end = support_by_release.get(release_id) or support_by_product.get(product_id)
            if product_support_end and (component_support_end is None or component_support_end < product_support_end):
                supplier_gap_products.add(product_id)
            approved = self.db.scalar(select(SupplierAssessment.id).where(
                SupplierAssessment.supplier_id == supplier_id,
                (SupplierAssessment.component_id.is_(None)) | (SupplierAssessment.component_id == component_id),
                SupplierAssessment.status.in_(["approved", "approved_with_conditions"]),
                SupplierAssessment.reassessment_required.is_(False),
                (SupplierAssessment.valid_until.is_(None)) | (SupplierAssessment.valid_until >= today),
            ).limit(1))
            if approved is None: supplier_gap_products.add(product_id)

        # Union of every product id that appears in any signal, so callers can
        # fetch a complete flag dict by product id.
        product_ids: set[UUID] = (
            set(open_critical_by_product)
            | risk_unapproved_products
            | support_expired_products
            | change_action_products
            | supplier_gap_products
        )
        flags: dict[UUID, dict[str, object]] = {}
        for product_id in product_ids:
            open_critical = open_critical_by_product.get(product_id, 0)
            flags[product_id] = {
                "has_open_critical_vuln": open_critical > 0,
                "open_critical_vuln_count": open_critical,
                "risk_unapproved": product_id in risk_unapproved_products,
                "support_expired": product_id in support_expired_products,
                "change_action_required": product_id in change_action_products,
                "supplier_due_diligence_gap": product_id in supplier_gap_products,
            }
        return flags

    @staticmethod
    def _default_flags() -> dict[str, object]:
        """Flag dict for a product that appears in no warning signal."""
        return {
            "has_open_critical_vuln": False,
            "open_critical_vuln_count": 0,
            "risk_unapproved": False,
            "support_expired": False,
            "change_action_required": False,
            "supplier_due_diligence_gap": False,
        }

    # ── Per-release / per-product assembly ────────────────────────────────────

    def _build_release_readiness(
        self,
        release: ProductRelease,
        approved_release_ids: set[UUID],
    ) -> ReleaseReadinessRead:
        rows = [row for row in self.requirement_service.release_matrix(release.id)
                if row.annex_requirement.kind == "essential"
                and row.annex_requirement.annex_part == AnnexPart.part_i]
        total = len(rows)
        assessed = sum(row.applicability_decision != RequirementApplicabilityDecision.undecided for row in rows)
        met = sum(row.finalized for row in rows)
        coverage = ReadinessCoverage(total=total, assessed=assessed, met=met,
            assessed_pct=round(assessed / total * 100) if total else 0,
            met_pct=round(met / total * 100) if total else 0)
        return ReleaseReadinessRead(
            release_id=release.id,
            version_label=self._version_label(release),
            system_version=release.system_version,
            release_status=str(release.release_status),
            is_released=release.release_status in _RELEASED_STATUSES,
            coverage=coverage,
            state=self._derive_state(coverage),
            is_approved=release.id in approved_release_ids,
        )

    def _build_product_readiness(
        self,
        product: Product,
        approved_release_ids: set[UUID],
        flags_by_product: dict[UUID, dict[str, object]],
    ) -> ProductReadinessRead:
        # `releases` is pre-sorted ascending by system_version; newest first here.
        releases_desc = list(reversed(product.releases))
        release_rows = [
            self._build_release_readiness(
                r, approved_release_ids
            )
            for r in releases_desc
        ]

        representative = self._representative_release(product)
        representative_id = representative.id if representative else None
        # Conformance only means something for an in-scope product that actually
        # has a released release; otherwise there is no market obligation to meet.
        is_conformant = (
            product.scope_status == "in_scope"
            and representative is not None
            and representative.release_status in _RELEASED_STATUSES
            and representative.id in approved_release_ids
        )

        flags = flags_by_product.get(product.id, self._default_flags())
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

    # ── Public API ────────────────────────────────────────────────────────────

    def list_product_readiness(self) -> list[ProductReadinessRead]:
        """
        Readiness for every product, grouped by product (name-sorted).

        Coverage comes from each release's assessment matrix; approvals and
        operational flags are loaded for the portfolio.

        Each product is still assembled defensively: a failure while building one
        product's rows must not blank the whole panel — that product falls back to
        an empty-coverage row and the error is logged for diagnosis.
        """
        products = self.product_repository.list_all()

        # ── Batched inputs (constant number of queries, portfolio-wide) ──
        approved_release_ids = self._approved_release_ids()
        flags_by_product = self._secondary_flags_by_product()

        rows: list[ProductReadinessRead] = []
        for product in products:
            try:
                rows.append(
                    self._build_product_readiness(
                        product,
                        approved_release_ids,
                        flags_by_product,
                    )
                )
            except Exception:
                logger.exception(
                    "Failed to compute readiness for product %s (%s); returning empty row",
                    product.id,
                    product.product_code,
                )
                rows.append(self._empty_product_row(product))
        rows.sort(key=lambda r: r.name.lower())
        return rows

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

    def _empty_product_row(self, product: Product) -> ProductReadinessRead:
        """A product row with no release coverage — used as a safe fallback."""
        return ProductReadinessRead(
            product_id=product.id,
            product_code=product.product_code,
            name=product.name,
            scope_status=product.scope_status,
            releases=[],
            representative_release_id=None,
            is_conformant=False,
        )

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
