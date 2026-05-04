from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import CvdPolicyStatus


class CvdPolicy(UUIDTimestampMixin, Base):
    """
    Gap 2 — Annex I Part II §5: manufacturers must have a Coordinated Vulnerability
    Disclosure (CVD) policy. One policy record per product; versioned by creating a new
    record and archiving the previous one.
    """

    __tablename__ = "cvd_policies"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[CvdPolicyStatus] = mapped_column(
        nullable=False,
        default=CvdPolicyStatus.draft,
        index=True,
    )

    # Public URL where the policy is published (e.g. security.txt, product page).
    policy_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Number of days the manufacturer keeps vulnerability information under embargo
    # before public disclosure. CRA guidance recommends ≤ 90 days.
    disclosure_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)

    # Primary security contact email advertised in the policy.
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    # Full policy text (may duplicate an external document for offline reference).
    policy_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="cvd_policies",
    )
