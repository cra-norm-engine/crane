from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import EvidenceType


class EvidenceItem(UUIDTimestampMixin, Base):
    __tablename__ = "evidence_items"

    product_release_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_releases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    risk_assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("risk_assessments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    requirement_mapping_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("requirement_mappings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_type: Mapped[EvidenceType] = mapped_column(nullable=False, index=True)

    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True, index=True)

    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    product_release: Mapped["ProductRelease | None"] = relationship(
        "ProductRelease",
        back_populates="evidence_items",
    )
    risk_assessment: Mapped["RiskAssessment | None"] = relationship(
        "RiskAssessment",
        back_populates="evidence_items",
    )
    requirement_mapping: Mapped["RequirementMapping | None"] = relationship(
        "RequirementMapping",
        back_populates="evidence_items",
    )
    uploaded_by_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[uploaded_by_user_id],
    )