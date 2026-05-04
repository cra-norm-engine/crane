from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import ConformityRoute, ProductClassification, ReleaseStatus


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
        UniqueConstraint("product_id", "version", name="uq_product_releases_product_version"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(100), nullable=False)
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

    product: Mapped[Product] = relationship(back_populates="releases")

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
    security_advisories: Mapped[list["SecurityAdvisory"]] = relationship(
        "SecurityAdvisory",
        back_populates="product_release",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(SecurityAdvisory.created_at)",
    )
    vulnerability_reports: Mapped[list["VulnerabilityReport"]] = relationship(
        "VulnerabilityReport",
        back_populates="product_release",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(VulnerabilityReport.created_at)",
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

    product: Mapped[Product] = relationship(back_populates="remote_processing_elements")


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
