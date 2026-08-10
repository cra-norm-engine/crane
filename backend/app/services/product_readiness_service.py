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
already enforces (RequirementMappingService._is_finalized), so the dashboard
number and the requirement matrix can never disagree.

Two numbers are reported per release:
  * assessed_pct — % of Part I requirements with an applicability decision made
  * met_pct      — % fully finalized (the headline / ring value)

Operational signals (open critical vulns, unapproved risk, expired support,
changes needing action) are returned as *informational flags only* — they never
change the coverage percentages.

Performance note
----------------
This used to call ``RequirementMappingService.release_matrix()`` once per release
inside a loop over every product — rebuilding the full, richly-eager-loaded
requirement matrix (trace records, risk items, artifacts, sorted sets) just to
extract three integers per release, plus a handful of per-release/per-product
COUNT queries. On a portfolio with many releases that was ``~5·releases +
5·products`` queries and a lot of throwaway object construction.

The computation is now **batched**: a bounded, constant number of set-based
aggregate queries covers every release/product at once, and the finalize rule is
evaluated in pure Python from those aggregates. The met/assessed semantics are a
faithful transcription of ``_build_row`` + ``_is_finalized`` for Part I rows, so
the results are byte-for-byte identical to the old per-release matrix path — just
far cheaper. No caching is involved; every call is fresh.
"""
from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from sqlalchemy import distinct, exists, func, select
from sqlalchemy.orm import Session

from app.models.annex_requirement import AnnexRequirement
from app.models.change import Change
from app.models.enums import (
    AnnexPart,
    ChangeStatus,
    ReleaseStatus,
    RequirementApplicabilityDecision,
    RequirementAssessmentStatus,
    RequirementProgressStatus,
    RiskAssessmentStatus,
    SecurityUpdateSeverity,
    VulnerabilityLifecycleStatus,
)
from app.models.product import Product, ProductRelease
from app.models.requirement_assessment import ReleaseRequirementAssessment
from app.models.requirement_mapping import (
    ProductRequirementDecision,
    RequirementMapping,
    RequirementMappingArtifactLink,
)
from app.models.risk_assessment import RiskAssessment
from app.models.support_period_record import SupportPeriodRecord
from app.models.vulnerability_report import VulnerabilityReport
from app.models.supplier_assessment import ProductComponentLink, SupplierAssessment, ThirdPartyComponent
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


class _ReleaseDecision:
    """The per-(release, requirement) inputs the finalize rule consumes.

    Mirrors exactly what ``_build_row`` extracts before calling
    ``_is_finalized``: the applicability decision, the decision's implementation
    status, and whether the requirement's mappings for that release carry any
    risk item / artifact.
    """

    __slots__ = (
        "applicability_decision",
        "implementation_status",
        "has_risk_item",
        "has_artifact",
    )

    def __init__(
        self,
        applicability_decision: RequirementApplicabilityDecision,
        implementation_status: RequirementProgressStatus,
    ) -> None:
        self.applicability_decision = applicability_decision
        self.implementation_status = implementation_status
        self.has_risk_item = False
        self.has_artifact = False


class ProductReadinessService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.product_repository = ProductRepository(db)
        self.requirement_service = RequirementMappingService(db)

    # ── Batched inputs ────────────────────────────────────────────────────────

    def _part_i_requirement_ids(self) -> set[UUID]:
        """Active Annex I **Part I** requirement ids — the coverage denominator.

        Loaded once; identical for every release. Ensures the catalog is seeded
        the same way the matrix path does before reading it.
        """
        self.requirement_service._ensure_catalog_seeded()
        rows = self.db.execute(
            select(AnnexRequirement.id).where(
                AnnexRequirement.is_active.is_(True),
                AnnexRequirement.annex_part == AnnexPart.part_i,
            )
        ).all()
        return {row[0] for row in rows}

    def _release_decisions(
        self, part_i_ids: set[UUID]
    ) -> dict[UUID, dict[UUID, _ReleaseDecision]]:
        """All Part I applicability decisions, grouped release → requirement.

        One query for every release of every product. Only Part I requirements
        are kept (they are the only ones that count toward coverage). Risk-item /
        artifact presence is layered on afterwards (``_apply_mapping_presence``).
        """
        if not part_i_ids:
            return {}
        rows = self.db.execute(
            select(
                ProductRequirementDecision.product_release_id,
                ProductRequirementDecision.annex_requirement_id,
                ProductRequirementDecision.applicability_decision,
                ProductRequirementDecision.implementation_status,
            ).where(ProductRequirementDecision.annex_requirement_id.in_(part_i_ids))
        ).all()

        by_release: dict[UUID, dict[UUID, _ReleaseDecision]] = {}
        for release_id, requirement_id, applicability, impl_status in rows:
            by_release.setdefault(release_id, {})[requirement_id] = _ReleaseDecision(
                applicability, impl_status
            )
        return by_release

    def _apply_mapping_presence(
        self,
        decisions_by_release: dict[UUID, dict[UUID, _ReleaseDecision]],
        part_i_ids: set[UUID],
    ) -> None:
        """Flag which (release, requirement) pairs have a risk item / artifact.

        Reuses the exact truthiness the matrix uses:
          * risk item present  = a RequirementMapping for that (release, req) has
            ``risk_item_id`` set (mirrors ``_unique_risk_items``).
          * artifact present   = a RequirementMappingArtifactLink exists on such a
            mapping, but only when the artifact-links table is available (mirrors
            ``_unique_artifacts`` under ``_artifact_links_available()``).

        Two grouped queries total (one for risk items, one for artifacts) rather
        than a matrix rebuild per release.
        """
        if not decisions_by_release or not part_i_ids:
            return

        # Risk-item presence per (release, requirement): any mapping with a risk item.
        risk_rows = self.db.execute(
            select(
                RequirementMapping.product_release_id,
                RequirementMapping.annex_requirement_id,
            )
            .where(
                RequirementMapping.annex_requirement_id.in_(part_i_ids),
                RequirementMapping.risk_item_id.isnot(None),
            )
            .group_by(
                RequirementMapping.product_release_id,
                RequirementMapping.annex_requirement_id,
            )
        ).all()
        for release_id, requirement_id in risk_rows:
            entry = decisions_by_release.get(release_id, {}).get(requirement_id)
            if entry is not None:
                entry.has_risk_item = True

        # Artifact presence — only meaningful when the artifact-links table exists.
        # Guarded exactly like the matrix's _unique_artifacts / _traceability_strength.
        if not self.requirement_service._artifact_links_available():
            return
        artifact_rows = self.db.execute(
            select(
                RequirementMapping.product_release_id,
                RequirementMapping.annex_requirement_id,
            )
            .where(
                RequirementMapping.annex_requirement_id.in_(part_i_ids),
                exists().where(
                    RequirementMappingArtifactLink.requirement_mapping_id
                    == RequirementMapping.id
                ),
            )
            .group_by(
                RequirementMapping.product_release_id,
                RequirementMapping.annex_requirement_id,
            )
        ).all()
        for release_id, requirement_id in artifact_rows:
            entry = decisions_by_release.get(release_id, {}).get(requirement_id)
            if entry is not None:
                entry.has_artifact = True

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
        due_rows = self.db.execute(
            select(ProductRelease.product_id, ProductRelease.id, ProductComponentLink.component_id, ThirdPartyComponent.supplier_id)
            .join(ProductComponentLink, ProductComponentLink.product_release_id == ProductRelease.id)
            .join(ThirdPartyComponent, ThirdPartyComponent.id == ProductComponentLink.component_id)
            .where(ProductComponentLink.criticality.in_(["medium", "high"]))
        ).all()
        today = date.today()
        for product_id, release_id, component_id, supplier_id in due_rows:
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

    # ── Coverage (from batched inputs) ────────────────────────────────────────

    def _coverage_from_decisions(
        self,
        total: int,
        release_decisions: dict[UUID, _ReleaseDecision],
    ) -> ReadinessCoverage:
        """Annex I Part I coverage for one release, from its batched decisions.

        Faithful transcription of the matrix path for Part I rows:
          * assessed = decisions whose applicability != undecided.
          * met      = _finalized(...) per the exact _is_finalized rule.
        """
        assessed = 0
        met = 0
        for entry in release_decisions.values():
            if entry.applicability_decision != RequirementApplicabilityDecision.undecided:
                assessed += 1
            if self._is_finalized(entry):
                met += 1
        return ReadinessCoverage(
            total=total,
            assessed=assessed,
            met=met,
            assessed_pct=round(assessed / total * 100) if total else 0,
            met_pct=round(met / total * 100) if total else 0,
        )

    @staticmethod
    def _is_finalized(entry: _ReleaseDecision) -> bool:
        """Whether a requirement is fully handled for this release.

        Byte-for-byte transcription of
        ``RequirementMappingService._is_finalized`` (the single source of truth):
          * undecided                → never finalized.
          * any decision             → requires at least one risk justification.
          * additionally if APPLICABLE → requires ≥1 linked artifact and a
            ``validated`` implementation status.
          * NOT_APPLICABLE           → finalized once decided + risk-justified.

        A requirement with no decision row simply never appears here, so it is
        treated as undecided (not finalized) — matching the matrix, where a
        missing decision yields applicability_decision == undecided.
        """
        if entry.applicability_decision == RequirementApplicabilityDecision.undecided:
            return False
        if not entry.has_risk_item:
            return False
        if entry.applicability_decision == RequirementApplicabilityDecision.applicable:
            return (
                entry.has_artifact
                and entry.implementation_status == RequirementProgressStatus.validated
            )
        return True

    # ── Per-release / per-product assembly ────────────────────────────────────

    def _build_release_readiness(
        self,
        release: ProductRelease,
        total: int,
        decisions_by_release: dict[UUID, dict[UUID, _ReleaseDecision]],
        approved_release_ids: set[UUID],
    ) -> ReleaseReadinessRead:
        coverage = self._coverage_from_decisions(
            total, decisions_by_release.get(release.id, {})
        )
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
        total: int,
        decisions_by_release: dict[UUID, dict[UUID, _ReleaseDecision]],
        approved_release_ids: set[UUID],
        flags_by_product: dict[UUID, dict[str, object]],
    ) -> ProductReadinessRead:
        # `releases` is pre-sorted ascending by system_version; newest first here.
        releases_desc = list(reversed(product.releases))
        release_rows = [
            self._build_release_readiness(
                r, total, decisions_by_release, approved_release_ids
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

        All heavy inputs are fetched up-front in a bounded number of batched
        queries (Part I catalog, decisions, mapping presence, approvals, flags),
        then assembled in memory — no per-release matrix rebuild.

        Each product is still assembled defensively: a failure while building one
        product's rows must not blank the whole panel — that product falls back to
        an empty-coverage row and the error is logged for diagnosis.
        """
        products = self.product_repository.list_all()

        # ── Batched inputs (constant number of queries, portfolio-wide) ──
        part_i_ids = self._part_i_requirement_ids()
        total = len(part_i_ids)
        decisions_by_release = self._release_decisions(part_i_ids)
        self._apply_mapping_presence(decisions_by_release, part_i_ids)
        approved_release_ids = self._approved_release_ids()
        flags_by_product = self._secondary_flags_by_product()

        rows: list[ProductReadinessRead] = []
        for product in products:
            try:
                rows.append(
                    self._build_product_readiness(
                        product,
                        total,
                        decisions_by_release,
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
