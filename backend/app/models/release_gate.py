from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import ArtifactReviewDecision, ReleaseGateItemCode, ReleaseGateWorkflowStatus


class ReleaseGate(UUIDTimestampMixin, Base):
    __tablename__ = "release_gates"
    __table_args__ = (
        UniqueConstraint("product_release_id", name="uq_release_gates_product_release"),
    )

    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ReleaseGateWorkflowStatus] = mapped_column(
        nullable=False,
        default=ReleaseGateWorkflowStatus.draft,
        index=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    submitted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    bundle_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bundle_generated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Compliance snapshot captured at gate approval (frozen state of all evidence)
    snapshot_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    product_release: Mapped["ProductRelease"] = relationship("ProductRelease", back_populates="release_gate")
    submitted_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[submitted_by_user_id])
    approved_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by_user_id])
    items: Mapped[list["ReleaseGateItem"]] = relationship(
        "ReleaseGateItem",
        back_populates="release_gate",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ReleaseGateItem.sort_order",
    )


class ReleaseGateItem(UUIDTimestampMixin, Base):
    __tablename__ = "release_gate_items"
    __table_args__ = (
        UniqueConstraint("release_gate_id", "code", name="uq_release_gate_items_gate_code"),
    )

    release_gate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("release_gates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[ReleaseGateItemCode | None] = mapped_column(nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[ArtifactReviewDecision] = mapped_column(
        nullable=False,
        default=ArtifactReviewDecision.pending_review,
        index=True,
    )

    # Task assignment — the team member responsible for completing this gate item.
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Optional deadline for this specific gate item.
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    release_gate: Mapped["ReleaseGate"] = relationship("ReleaseGate", back_populates="items")
    assigned_to_user: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_to_user_id])
    evidence_links: Mapped[list["ReleaseGateEvidenceLink"]] = relationship(
        "ReleaseGateEvidenceLink",
        back_populates="release_gate_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(ReleaseGateEvidenceLink.created_at)",
    )
    prerequisites: Mapped[list["ReleaseGateItem"]] = relationship(
        "ReleaseGateItem",
        secondary="release_gate_item_prerequisites",
        primaryjoin="ReleaseGateItem.id == foreign(release_gate_item_prerequisites.c.dependent_item_id)",
        secondaryjoin="ReleaseGateItem.id == foreign(release_gate_item_prerequisites.c.prerequisite_item_id)",
        lazy="selectin",
        viewonly=True,
    )


class ReleaseGateEvidenceLink(UUIDTimestampMixin, Base):
    __tablename__ = "release_gate_evidence_links"
    __table_args__ = (
        UniqueConstraint(
            "release_gate_item_id",
            "artifact_revision_id",
            name="uq_release_gate_evidence_item_revision",
        ),
    )

    release_gate_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("release_gate_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    artifact_revision_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("artifact_revisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    linked_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    decision: Mapped[ArtifactReviewDecision] = mapped_column(
        nullable=False,
        default=ArtifactReviewDecision.pending_review,
        index=True,
    )
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    release_gate_item: Mapped["ReleaseGateItem"] = relationship("ReleaseGateItem", back_populates="evidence_links")
    artifact_revision: Mapped["ArtifactRevision"] = relationship("ArtifactRevision", back_populates="release_gate_links")
    linked_by_user: Mapped["User"] = relationship("User", foreign_keys=[linked_by_user_id])
    reviewed_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[reviewed_by_user_id])


class ReleaseGateItemPrerequisite(UUIDTimestampMixin, Base):
    """
    A prerequisite dependency between two release gate items in the same gate.

    When a dependent item requires its prerequisite(s) to be accepted before it can be accepted,
    this table records the relationship. E.g., "Test Report depends on SBOM" means the Test Report
    item cannot be accepted until the SBOM item is accepted.
    """

    __tablename__ = "release_gate_item_prerequisites"
    __table_args__ = (
        UniqueConstraint(
            "dependent_item_id",
            "prerequisite_item_id",
            name="uq_release_gate_prerequisites_edge",
        ),
    )

    dependent_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("release_gate_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    prerequisite_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("release_gate_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
