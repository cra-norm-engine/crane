from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import SbomFormat


class SbomRecord(UUIDTimestampMixin, Base):
    """
    Gap 10 — Annex I Part II §1: manufacturers must prepare a machine-readable SBOM
    listing at minimum top-level dependencies. This model stores structured SBOM metadata
    and the component list alongside an optional file reference for the original document.
    """

    __tablename__ = "sbom_records"

    product_release_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # SBOM specification format.
    format: Mapped[SbomFormat] = mapped_column(nullable=False, default=SbomFormat.cyclonedx)
    # Specification version string, e.g. "1.5" for CycloneDX or "2.3" for SPDX.
    spec_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Parsed component list stored as structured JSON for querying.
    # Each element is a dict with at minimum: name, version, purl/cpe (optional).
    components_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    # Cached count for quick display without scanning components_json.
    component_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Reference to the uploaded artifact file (filename / storage key).
    file_name: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Name and version of the tool that generated the SBOM.
    tool_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # When the SBOM was generated (may differ from the record creation timestamp).
    generated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Optional human-readable notes about scope, exclusions, etc.
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Raw uploaded SBOM file content — stored for re-analysis runs.
    sbom_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # sbom-tools quality score (0–100). Null if analysis has not been run.
    quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full JSON output from sbom-tools validate + quality runs.
    analysis_findings: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    product_release: Mapped["ProductRelease"] = relationship(
        "ProductRelease",
        back_populates="sbom_records",
    )
    vulnerability_findings: Mapped[list["SbomVulnerabilityFinding"]] = relationship(  # type: ignore[name-defined]
        "SbomVulnerabilityFinding",
        back_populates="sbom_record",
        cascade="all, delete-orphan",
    )
