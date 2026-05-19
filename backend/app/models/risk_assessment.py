from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint  # Text needed for rejection_reason
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import RiskAssessmentStatus


class RiskAssessment(UUIDTimestampMixin, Base):
    __tablename__ = "risk_assessments"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "system_version",
            name="uq_risk_assessments_product_system_version",
        ),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_release_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_releases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Auto-incremented system version (v1, v2, v3, etc.)
    system_version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # User-defined assessment name (optional: "Q2 Assessment", "Annual Review", etc.)
    user_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[RiskAssessmentStatus] = mapped_column(
        nullable=False,
        default=RiskAssessmentStatus.draft,
        index=True,
    )
    methodology: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Approval workflow — reviewer fields (Track B: risk assessment approval).
    # reviewer_user_id is set when an assessor submits the assessment for review
    # and a reviewer then accepts or rejects it.
    reviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # rejection_reason is populated when a reviewer rejects the assessment and
    # the status is rolled back to draft so the owner can revise and re-submit.
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="risk_assessments",
    )
    product_release: Mapped["ProductRelease | None"] = relationship(
        "ProductRelease",
        back_populates="risk_assessments",
    )
    owner_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[owner_user_id],
    )
    # The user who reviewed (approved or rejected) this assessment.
    reviewer_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[reviewer_user_id],
    )

    risk_items: Mapped[list["RiskItem"]] = relationship(
        "RiskItem",
        back_populates="risk_assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(RiskItem.created_at)",
    )
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        "EvidenceItem",
        back_populates="risk_assessment",
        passive_deletes=True,
        order_by="desc(EvidenceItem.created_at)",
    )