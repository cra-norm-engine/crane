# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import (
    ConformityRoute,
    ProductClassification,
    ProductLifecycleStatus,
    ProductType,
    ReleaseStatus,
    RemoteProcessingClassification,
    RemoteProcessingElementType,
)


# M2M association table — links each release to the remote processing elements
# that are in scope for that specific release version.
release_remote_processing_element_table = Table(
    "release_remote_processing_elements",
    Base.metadata,
    Column("release_id", PGUUID(as_uuid=True), ForeignKey("product_releases.id", ondelete="CASCADE"), primary_key=True),
    Column("rpe_id", PGUUID(as_uuid=True), ForeignKey("remote_processing_elements.id", ondelete="CASCADE"), primary_key=True),
)


class Product(UUIDTimestampMixin, Base):
    __tablename__ = "products"

    product_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    manufacturer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    intended_use: Mapped[str] = mapped_column(Text, nullable=False)
    product_type: Mapped[str] = mapped_column(String(150), nullable=False, index=True)

    current_classification: Mapped[ProductClassification] = mapped_column(
        nullable=False,
        default=ProductClassification.normal,
    )
    scope_status: Mapped[str] = mapped_column(String(50), nullable=False, default="undecided", index=True)

    # CRA obligation tier. "legacy" products (on the market pre-CRA, not
    # substantially modified) carry reporting-only obligations; "active" products
    # carry the full set. Distinct from is_pre_cra (a raw fact) — this is the
    # decided obligation level.
    lifecycle_status: Mapped[ProductLifecycleStatus] = mapped_column(
        nullable=False,
        default=ProductLifecycleStatus.active,
        server_default=ProductLifecycleStatus.active.value,
        index=True,
    )

    # Phase 3 — typed CRA product classification (software vs hardware+digital).
    # Distinct from the free-text product_type label; used for filtering/logic.
    product_type_class: Mapped[ProductType] = mapped_column(
        nullable=False,
        default=ProductType.undecided,
        server_default=ProductType.undecided.value,
        index=True,
    )

    # Phase 3 — product-level conformity assessment route. Distinct from the
    # per-release conformity_route_snapshot: this is the decided route for the
    # product line, seeded from the scope wizard's suggestion when still undecided.
    conformity_route: Mapped[ConformityRoute] = mapped_column(
        nullable=False,
        default=ConformityRoute.undecided,
        server_default=ConformityRoute.undecided.value,
        index=True,
    )

    # Phase 2 — out-of-scope decision provenance (metamodel: OutOfScopeProduct).
    # The scope wizard records the "why" in ProductScopeEvaluation; these fields
    # capture the signed, accountable decision on the product itself so the
    # inventory is an audit-ready register (who decided, when, signature).
    out_of_scope_justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    scope_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scope_decision_signature: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Phase 4 — additive JSON metadata (matches the annex_ii_json pattern).
    # system_profile_json: {sold_as_product, who_integrates_system,
    #   marketed_as_product, core_minimum_products_combination} — the
    #   system-as-product vs component-by-component strategy.
    # tailor_made_terms_json: {customized_support_period,
    #   customized_security_config, specific_user, agreement_via_contractual_terms}
    #   — B2B tailor-made product terms.
    system_profile_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tailor_made_terms_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Gap 2 — flags that this product combines physical hardware with software/firmware.
    # When True, per-release hardware_version and software_version fields are surfaced
    # so each HW+SW combination can be individually documented for CRA compliance.
    is_embedded_product: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # Gap 4 — Article 69(2): marks products already on the EU market before CRA
    # full applicability. Pre-CRA products have different obligation timelines.
    is_pre_cra: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Gap 4 — Earliest known EU market placement date for this product line.
    # Essential for pre-CRA products to anchor the transition period calculation.
    first_placed_on_market_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Gap 4 — Annex I Part II §6: manufacturer must provide a contact address for
    # vulnerability disclosure. security_contact_email is the primary contact;
    # security_contact_url can point to a security.txt or bug-bounty programme.
    security_contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    security_contact_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Economic operators (CRA Art. 13/18-23) — beyond the manufacturer captured above.
    authorised_representative: Mapped[str | None] = mapped_column(Text, nullable=True)
    importers: Mapped[str | None] = mapped_column(Text, nullable=True)
    distributors: Mapped[str | None] = mapped_column(Text, nullable=True)
    single_point_of_contact: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Specific Annex III/IV category/item this product matches (Art. 7-8).
    annex_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Annex II "information and instructions to the user" checklist:
    # list of {ref, content, status, location}.
    annex_ii_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Phase 2 — the user who signed off the (out-of-)scope decision. Nullable so
    # deleting the user does not erase the product's decision record.
    scope_decided_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[scope_decided_by_user_id],
    )

    # Phase 4 — cheap boolean flags read by ProductSummaryRead for the inventory
    # "flags" chips. has_remote_processing relies on remote_processing_elements
    # being eager-loaded by the list query (selectinload) to avoid an N+1.
    @property
    def has_system_profile(self) -> bool:
        return bool(self.system_profile_json)

    @property
    def has_tailor_made_terms(self) -> bool:
        return bool(self.tailor_made_terms_json)

    @property
    def has_remote_processing(self) -> bool:
        return len(self.remote_processing_elements) > 0

    @property
    def scope_decided_by_name(self) -> str | None:
        # Display name of the user who signed the scope decision, for ProductRead.
        # Relies on the scope_decided_by relationship being loaded (detail query).
        user = self.scope_decided_by
        if user is None:
            return None
        return getattr(user, "full_name", None) or getattr(user, "email", None)

    parent_product: Mapped["Product | None"] = relationship(
        "Product",
        remote_side="Product.id",
        back_populates="child_products",
    )
    child_products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="parent_product",
    )

    releases: Mapped[list["ProductRelease"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        # Always return releases in ascending system_version order so that
        # callers can reliably use at(-1) to find the latest release.
        order_by="ProductRelease.system_version.asc()",
    )
    artifact_links: Mapped[list["ArtifactProductLink"]] = relationship(
        "ArtifactProductLink",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    remote_processing_elements: Mapped[list["RemoteProcessingElement"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    scope_evaluations: Mapped[list["ProductScopeEvaluation"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(ProductScopeEvaluation.created_at)",
    )
    # Security advisories are product-scoped; each advisory links to the affected
    # releases via the advisory_releases join table.
    security_advisories: Mapped[list["SecurityAdvisory"]] = relationship(
        "SecurityAdvisory",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(SecurityAdvisory.created_at)",
    )
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(
        "RiskAssessment",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(RiskAssessment.created_at)",
    )
    support_period_records: Mapped[list["SupportPeriodRecord"]] = relationship(
        "SupportPeriodRecord",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(SupportPeriodRecord.created_at)",
    )
    certification_records: Mapped[list["CertificationRecord"]] = relationship(
        "CertificationRecord",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(CertificationRecord.created_at)",
    )
    cvd_policies: Mapped[list["CvdPolicy"]] = relationship(
        "CvdPolicy",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(CvdPolicy.created_at)",
    )


class ProductRelease(UUIDTimestampMixin, Base):
    __tablename__ = "product_releases"
    __table_args__ = (
        UniqueConstraint("product_id", "system_version", name="uq_product_releases_product_system_version"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Auto-incremented system version (v1, v2, v3, etc.)
    system_version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # User-defined version name (optional: "Spring 2026", "RC-1", etc.)
    user_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Gap 2 — for embedded (hardware+software) products: the specific hardware
    # revision and firmware/software version that make up this release.
    # Both are nullable so they are invisible for pure-software products.
    hardware_version: Mapped[str | None] = mapped_column(String(150), nullable=True)
    software_version: Mapped[str | None] = mapped_column(String(150), nullable=True)

    release_status: Mapped[ReleaseStatus] = mapped_column(nullable=False, default=ReleaseStatus.draft)

    planned_release_date: Mapped[datetime | None] = mapped_column(nullable=True)
    actual_release_date: Mapped[datetime | None] = mapped_column(nullable=True)

    # Gap 3 — Formal EU market placement date (CRA Art. 3(20)).
    # Distinct from actual_release_date: a product may be released internally
    # before or after the regulatory placement event on the EU market.
    # Set when release_status transitions to placed_on_market.
    placed_on_market_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    classification_snapshot: Mapped[ProductClassification] = mapped_column(
        nullable=False,
        default=ProductClassification.normal,
    )
    conformity_route_snapshot: Mapped[ConformityRoute] = mapped_column(
        nullable=False,
        default=ConformityRoute.undecided,
    )
    release_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Gap 2 — Placement lineage for non-substantial updates (CRA guidance §15).
    # When set, this release is a non-substantial update of another release and
    # inherits that release's placed_on_market_date for compliance purposes.
    # NULL for original placements and post-substantial-modification releases.
    parent_release_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_releases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Gap 5 — Article 13(10) consolidated support flag.
    # When True, this release provides security update coverage for all prior
    # versions, allowing the manufacturer to consolidate support obligations.
    is_consolidated_support_version: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Art. 13(7) + Art. 3(30): link to the SubstantialModificationAssessment that
    # documents the substantiality determination for this release (required for v2+).
    # NULL for the first release of a product; must be set before gate approval for
    # all subsequent releases (parent_release_id is set).
    substantiality_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("substantial_modification_assessments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Optional link to the substantial change that triggered this re-release.
    # NULL for planned/routine releases; set when the release is a direct
    # consequence of a CRA substantial modification (Art. 13(8)).
    caused_by_change_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("changes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Gap 1 — CRA Art. 13(2) + Annex I Part I §2(a): products placed on the market
    # must contain no known exploitable vulnerabilities. This flag must be False
    # before the release gate approves the release.
    has_known_exploitable_vulnerabilities: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    # Free-text notes describing any known exploitable vulnerabilities if the flag is set.
    kev_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # CRA Art. 28 — EU Declaration of Conformity metadata.
    # eu_doc_date: date the DoC was drawn up; must be <= placed_on_market_date (Art. 28).
    # eu_doc_number: manufacturer's unique reference number for this DoC (Annex V).
    # eu_doc_notified_body: notified body name/ref; required only for third-party
    # conformity route (ConformityRoute.third_party_assessment).
    eu_doc_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    eu_doc_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    eu_doc_notified_body: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # CRA Art. 28/30 — fuller DoC + CE marking metadata.
    eu_doc_signatory: Mapped[str | None] = mapped_column(String(255), nullable=True)
    eu_doc_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    eu_doc_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ce_marking_info: Mapped[str | None] = mapped_column(Text, nullable=True)

    # CRA Art. 32 — conformity assessment detail (module, NB number, standards).
    conformity_module: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notified_body_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    standards_applied: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Multi-role report sign-off (free text per role).
    signoff_compliance_lead: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signoff_notified_body_reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signoff_executive: Mapped[str | None] = mapped_column(String(255), nullable=True)

    product: Mapped[Product] = relationship(back_populates="releases")

    # Gap 1 — M2M: remote processing elements in scope for this specific release.
    # Populated at release creation time to record which RPEs apply to this version.
    release_remote_processing_elements: Mapped[list["RemoteProcessingElement"]] = relationship(
        "RemoteProcessingElement",
        secondary=release_remote_processing_element_table,
        back_populates="releases",
        lazy="selectin",
    )

    @property
    def product_name(self) -> str | None:
        """Convenience accessor used by ProductReleaseRead schema serialization."""
        return self.product.name if self.product else None

    # Self-referential relationship: the base release this version derives from
    # (for non-substantial updates). Navigates the placement date lineage chain.
    parent_release: Mapped["ProductRelease | None"] = relationship(
        "ProductRelease",
        remote_side="ProductRelease.id",
        foreign_keys="[ProductRelease.parent_release_id]",
        back_populates="derived_releases",
    )
    derived_releases: Mapped[list["ProductRelease"]] = relationship(
        "ProductRelease",
        foreign_keys="[ProductRelease.parent_release_id]",
        back_populates="parent_release",
    )

    # The formal substantiality determination for this release (Art. 13(7)).
    substantiality_analysis: Mapped["SubstantialModificationAssessment | None"] = relationship(
        "SubstantialModificationAssessment",
        foreign_keys="[ProductRelease.substantiality_analysis_id]",
    )

    # Relationship to the substantial change that caused this release (if any).
    # foreign_keys disambiguates from the Change.product_version_id path.
    caused_by_change: Mapped["Change | None"] = relationship(
        "Change",
        foreign_keys="[ProductRelease.caused_by_change_id]",
    )
    risk_assessments: Mapped[list["RiskAssessment"]] = relationship(
        "RiskAssessment",
        back_populates="product_release",
        passive_deletes=True,
        order_by="desc(RiskAssessment.created_at)",
    )
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        "EvidenceItem",
        back_populates="product_release",
        passive_deletes=True,
        order_by="desc(EvidenceItem.created_at)",
    )
    release_gate: Mapped["ReleaseGate | None"] = relationship(
        "ReleaseGate",
        back_populates="product_release",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    security_updates: Mapped[list["SecurityUpdate"]] = relationship(
        "SecurityUpdate",
        back_populates="product_release",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(SecurityUpdate.created_at)",
    )
    vulnerability_reports: Mapped[list["VulnerabilityReport"]] = relationship(
        "VulnerabilityReport",
        back_populates="product_release",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(VulnerabilityReport.created_at)",
    )
    incident_reports: Mapped[list["IncidentReport"]] = relationship(
        "IncidentReport",
        back_populates="product_release",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(IncidentReport.created_at)",
    )
    sbom_records: Mapped[list["SbomRecord"]] = relationship(
        "SbomRecord",
        back_populates="product_release",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(SbomRecord.created_at)",
    )

    # Changes recorded against this product version (for substantial change tracking).
    # foreign_keys disambiguates from the caused_by_change_id FK on this same table.
    changes: Mapped[list["Change"]] = relationship(
        "Change",
        foreign_keys="[Change.product_version_id]",
        back_populates="product_version",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(Change.change_date)",
    )


class RemoteProcessingElement(UUIDTimestampMixin, Base):
    __tablename__ = "remote_processing_elements"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    provider_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_processed: Mapped[str | None] = mapped_column(Text, nullable=True)
    geographic_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criticality: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # --- CRA Art. 3(2) evaluation fields ---
    # Element type helps guide classification (e.g. SaaS vs internal cloud backend).
    element_type: Mapped[str | None] = mapped_column(
        SAEnum(RemoteProcessingElementType, name="remoteprocessingelementtype"),
        nullable=True,
    )
    # CRA Art. 3(2) inclusion criteria 1-4 (None = not yet answered).
    # Criterion 1: Designed/developed by or on behalf of the manufacturer for this product.
    is_developed_by_manufacturer: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Criterion 2: Necessary for the product to perform its functions (absence = cannot function).
    is_necessary_for_product_function: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Criterion 3: Directly interacts with the product itself.
    directly_interacts_with_product: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Criterion 4: Bidirectional data exchange (product → RDPS → result back to product).
    has_bidirectional_exchange: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Context field: is the provider already covered under NIS2 Managed Service Provider rules?
    provider_is_nis2_msp: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Final classification outcome derived from the decision tree.
    classification: Mapped[str] = mapped_column(
        SAEnum(RemoteProcessingClassification, name="remoteprocessingclassification"),
        nullable=False,
        default=RemoteProcessingClassification.not_assessed,
        server_default="not_assessed",
    )
    classification_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assessed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    product: Mapped[Product] = relationship(back_populates="remote_processing_elements")
    # The user who last ran the CRA Art. 3(2) evaluation (used to surface their name in the UI).
    assessed_by: Mapped["User | None"] = relationship("User", foreign_keys=[assessed_by_user_id])
    # Back-reference to releases that include this element in their processing scope.
    releases: Mapped[list["ProductRelease"]] = relationship(
        "ProductRelease",
        secondary=release_remote_processing_element_table,
        back_populates="release_remote_processing_elements",
    )


class ProductScopeEvaluation(UUIDTimestampMixin, Base):
    __tablename__ = "product_scope_evaluations"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    is_digital_product: Mapped[bool] = mapped_column(nullable=False, default=False)
    has_network_connectivity: Mapped[bool] = mapped_column(nullable=False, default=False)
    performs_remote_data_processing: Mapped[bool] = mapped_column(nullable=False, default=False)
    safety_component: Mapped[bool] = mapped_column(nullable=False, default=False)
    used_in_critical_sector: Mapped[bool] = mapped_column(nullable=False, default=False)
    handles_sensitive_functions: Mapped[bool] = mapped_column(nullable=False, default=False)
    excluded_category: Mapped[bool] = mapped_column(nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    in_scope: Mapped[bool] = mapped_column(nullable=False, default=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_classification: Mapped[ProductClassification] = mapped_column(
        nullable=False,
        default=ProductClassification.normal,
    )
    suggested_conformity_route: Mapped[ConformityRoute] = mapped_column(
        nullable=False,
        default=ConformityRoute.undecided,
    )

    product: Mapped[Product] = relationship(back_populates="scope_evaluations")
