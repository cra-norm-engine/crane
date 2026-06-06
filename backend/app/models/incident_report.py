from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import IncidentReportStatus, SecurityUpdateSeverity


class IncidentReport(UUIDTimestampMixin, Base):
    """
    CRA Art. 14 — severe incident report (the incident branch of ENISA SRP).

    A 'severe incident' is any event that negatively affects the ability of a
    product to protect availability, authenticity, integrity, or confidentiality
    of data — or that has led / could lead to malicious code execution (Art. 14(3)).

    Reporting timeline:
      • Early warning  — within 24 h of detection
      • Notification   — within 72 h of detection
      • Final report   — within 1 month after the 72 h notification
    """

    __tablename__ = "incident_reports"

    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # --- i12 / common: title shown in SRP and internal queue ---
    title: Mapped[str] = mapped_column(Text, nullable=False)

    # --- i13 (X at 24h) — mandatory first question on the SRP form ---
    # Must answer immediately: is this incident suspected to involve unlawful or malicious acts?
    suspected_malicious_act: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # --- i14 (O at 24h, X at 72h) — general nature of what happened ---
    incident_nature: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- i15 (O at 24h, X at 72h) — when the incident was first detected internally ---
    detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- i16 (O at 24h, X at 72h) — when the underlying event actually occurred (may be earlier than detection) ---
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- i17 (O at 24h, X at 72h) — initial impact and scope assessment ---
    initial_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- i18 (O at 24h, X at 72h) — what the manufacturer has already done to contain/fix the incident ---
    corrective_measures_taken: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- i19 (O at 24h, X at 72h) — guidance for product users (patches, config, workarounds) ---
    user_corrective_measures: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- i20 (O at 72h, obligatory-if-available) — flag if report contains sensitive info ---
    information_sensitivity: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- i21 / i22 (O at 72h, X at final) — severity classification per CRA Art. 14(3) ---
    # Which of the two statutory severity criteria this incident meets.
    incident_impact_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Overall severity rating (reuses the same enum as vulnerabilities for consistency).
    severity: Mapped[SecurityUpdateSeverity | None] = mapped_column(nullable=True, index=True)

    # --- i23 (O at 72h, X at final) — concrete impact: systems affected, data exposed, downtime, etc. ---
    incident_impact: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- i24 (O at 72h, X at final) — most likely threat type or root cause ---
    # e.g. "supply chain compromise", "credential stuffing", "zero-day exploit"
    threat_type_root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- i25 (O at 72h, X at final) — mitigation measures applied and still ongoing ---
    applied_mitigations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Internal lifecycle ---
    status: Mapped[IncidentReportStatus] = mapped_column(
        nullable=False,
        default=IncidentReportStatus.reported,
        index=True,
    )

    # Task assignment.
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # --- CRA Art. 14 — ENISA SRP submission tracking ---
    # Flag set by the user when this incident meets the Art. 14 reporting threshold.
    enisa_reporting_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Timestamps for each of the three SRP submission phases.
    enisa_early_warning_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    enisa_initial_report_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Final report for incidents is due 1 month after the 72h notification (not 14 days).
    enisa_final_report_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Reference number issued by the national CSIRT / ENISA SRP.
    enisa_reference_number: Mapped[str | None] = mapped_column(String(255), nullable=True)

    product_release: Mapped["ProductRelease"] = relationship(  # type: ignore[name-defined]
        "ProductRelease",
        back_populates="incident_reports",
    )
