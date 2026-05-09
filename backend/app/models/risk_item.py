from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import RiskItemStatus, RiskLevel


class RiskItem(UUIDTimestampMixin, Base):
    __tablename__ = "risk_items"

    risk_assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    threat_scenario: Mapped[str] = mapped_column(Text, nullable=False)
    asset_affected: Mapped[str] = mapped_column(String(255), nullable=False)

    likelihood: Mapped[RiskLevel] = mapped_column(nullable=False)
    impact: Mapped[RiskLevel] = mapped_column(nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(nullable=False, index=True)

    mitigation_plan: Mapped[str] = mapped_column(Text, nullable=False)
    residual_risk_level: Mapped[RiskLevel | None] = mapped_column(nullable=True)

    status: Mapped[RiskItemStatus] = mapped_column(
        nullable=False,
        default=RiskItemStatus.open,
        index=True,
    )
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Due date for completing the mitigation plan for this risk item.
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    risk_assessment: Mapped["RiskAssessment"] = relationship(
        "RiskAssessment",
        back_populates="risk_items",
    )
    owner_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[owner_user_id],
    )
    requirement_mappings: Mapped[list["RequirementMapping"]] = relationship(
        "RequirementMapping",
        back_populates="risk_item",
        passive_deletes=True,
        order_by="desc(RequirementMapping.created_at)",
    )