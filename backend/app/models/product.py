from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
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

    classification_snapshot: Mapped[ProductClassification] = mapped_column(
        nullable=False,
        default=ProductClassification.normal,
    )
    conformity_route_snapshot: Mapped[ConformityRoute] = mapped_column(
        nullable=False,
        default=ConformityRoute.undecided,
    )
    release_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional link to the substantial change that triggered this re-release.
    # NULL for planned/routine releases; set when the release is a direct
    # consequence of a CRA substantial modification (Art. 13(8)).
    caused_by_change_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("changes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    product: Mapped[Product] = relationship(back_populates="releases")
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
