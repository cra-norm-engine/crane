"""
MarketAction — CRA Art. 35 recall and withdrawal workflow.

Covers both voluntary/mandatory product recalls (FR39) and withdrawals of
non-compliant products from the market (FR38).  Each record is linked to a
specific ProductRelease and tracks the full lifecycle from initiation through
authority notification to closure.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import MarketActionStatus, MarketActionType


class MarketAction(UUIDTimestampMixin, Base):
    __tablename__ = "market_actions"

    # The specific release being recalled or withdrawn.
    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Distinguishes recall (users must return/stop using the product) from
    # withdrawal (removal from distribution channels before end users receive it).
    action_type: Mapped[MarketActionType] = mapped_column(nullable=False)

    # Workflow status: draft → active → authority_notified → closed.
    status: Mapped[MarketActionStatus] = mapped_column(
        nullable=False,
        default=MarketActionStatus.draft,
    )

    # Mandatory narrative: what non-conformity or safety issue triggered this action.
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Human-readable description of which product versions / serial ranges are affected.
    affected_scope: Mapped[str | None] = mapped_column(Text, nullable=True)

    # What the end user or distributor must do (stop use, return, update, etc.).
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reference number assigned by the market surveillance authority (e.g. RAPEX/ICSMS).
    authority_reference_number: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamp when the relevant market surveillance authority was notified.
    # CRA Art. 14 requires notification within 24 h of an actively exploited vulnerability;
    # Art. 35 requires prompt notification for recalls/withdrawals.
    authority_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Ready-to-send notice text for end users / distributors (CRA Art. 35 §2).
    user_notice_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional internal notes (not sent to users or authorities).
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship back to the release for eager-loading product context.
    product_release: Mapped["ProductRelease"] = relationship(
        "ProductRelease",
        lazy="select",
    )
