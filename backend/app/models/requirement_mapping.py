from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import (
    RequirementApplicabilityDecision,
    RequirementImplementationStatus,
    SdlActivity,
)


class RequirementMapping(UUIDTimestampMixin, Base):
    __tablename__ = "requirement_mappings"

    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("risk_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    annex_requirement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("annex_requirements.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    engineering_requirement_ref: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    sdl_activity: Mapped[SdlActivity] = mapped_column(
        nullable=False,
        index=True,
    )
    implementation_status: Mapped[RequirementImplementationStatus] = mapped_column(
        nullable=False,
        default=RequirementImplementationStatus.planned,
        index=True,
    )
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    product_release: Mapped["ProductRelease"] = relationship("ProductRelease")
    risk_item: Mapped["RiskItem | None"] = relationship(
        "RiskItem",
        back_populates="requirement_mappings",
    )
    annex_requirement: Mapped["AnnexRequirement"] = relationship(
        "AnnexRequirement",
        back_populates="requirement_mappings",
    )
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        "EvidenceItem",
        back_populates="requirement_mapping",
        passive_deletes=True,
        order_by="desc(EvidenceItem.created_at)",
    )
    artifact_links: Mapped[list["RequirementMappingArtifactLink"]] = relationship(
        "RequirementMappingArtifactLink",
        back_populates="requirement_mapping",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RequirementMappingArtifactLink(UUIDTimestampMixin, Base):
    __tablename__ = "requirement_mapping_artifact_links"
    __table_args__ = (
        UniqueConstraint(
            "requirement_mapping_id",
            "artifact_id",
            name="uq_requirement_mapping_artifact_link",
        ),
    )

    requirement_mapping_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("requirement_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    requirement_mapping: Mapped["RequirementMapping"] = relationship(
        "RequirementMapping",
        back_populates="artifact_links",
    )
    artifact: Mapped["Artifact"] = relationship("Artifact")


class ProductRequirementDecision(UUIDTimestampMixin, Base):
    __tablename__ = "product_requirement_decisions"
    __table_args__ = (
        UniqueConstraint(
            "product_release_id",
            "annex_requirement_id",
            name="uq_product_requirement_decisions_release_requirement",
        ),
    )

    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    annex_requirement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("annex_requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicability_decision: Mapped[RequirementApplicabilityDecision] = mapped_column(
        nullable=False,
        default=RequirementApplicabilityDecision.undecided,
        index=True,
    )
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    product_release: Mapped["ProductRelease"] = relationship("ProductRelease")
    annex_requirement: Mapped["AnnexRequirement"] = relationship("AnnexRequirement")
