from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import CvdPolicyStatus


class CvdPolicy(UUIDTimestampMixin, Base):
    """
    Gap 2 — Annex I Part II §5: manufacturers must have a Coordinated Vulnerability
    Disclosure (CVD) policy. One policy record per product; versioned by creating a new
    record and archiving the previous one.

    Fields follow ISO/IEC 29147, RFC 9116 (security.txt), and ENISA CRA guidance.
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

    # ── Contact & reporting channels ────────────────────────────────────────
    # Primary security contact email advertised in the policy.
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    # URL to the PGP/GPG public key for encrypted vulnerability submission.
    pgp_key_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # RFC 9116 security.txt canonical URL (/.well-known/security.txt).
    security_txt_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Bug bounty or VDP platform URL (HackerOne, Bugcrowd, Intigriti, etc.).
    bug_bounty_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # ── Timelines ────────────────────────────────────────────────────────────
    # Commitment to send an initial acknowledgement within this many hours.
    # ISO/IEC 29147 recommends ≤ 7 days; 48 h is considered best practice.
    response_sla_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=48)

    # Days before public disclosure. CRA guidance recommends ≤ 90 days.
    disclosure_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)

    # ── Legal & researcher relations ─────────────────────────────────────────
    # Whether the policy contains a safe-harbour clause protecting good-faith researchers.
    safe_harbor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Whether the policy commits to acknowledging researchers publicly (hall of fame / CVE credit).
    acknowledgement_offered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Scope ────────────────────────────────────────────────────────────────
    # Description of what is in scope for vulnerability reports (products, versions, components).
    scope_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Explicit out-of-scope items (third-party components, deprecated versions, etc.).
    out_of_scope_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Which product versions currently receive security patches.
    supported_versions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Policy document ──────────────────────────────────────────────────────
    # Public URL where the full human-readable policy is published.
    policy_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Full policy text stored here for offline / compliance-package reference.
    policy_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="cvd_policies",
    )
