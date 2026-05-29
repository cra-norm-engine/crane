from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.enums import ConformityRoute, ProductClassification, ReleaseStatus
from app.schemas.remote_processing_element import RemoteProcessingElementRead


class ProductReleaseBase(BaseModel):
    product_id: UUID
    release_status: ReleaseStatus = ReleaseStatus.draft
    planned_release_date: datetime | None = None
    actual_release_date: datetime | None = None

    # Gap 3 — formal EU market placement date (CRA Art. 3(20)).
    # Distinct from actual_release_date; set when the release transitions to
    # placed_on_market status. NULL until the market placement event occurs.
    placed_on_market_date: date | None = None

    classification_snapshot: ProductClassification = ProductClassification.normal
    conformity_route_snapshot: ConformityRoute = ConformityRoute.undecided
    release_notes: str | None = None

    # Gap 2 — for non-substantial updates: points to the base release whose
    # placed_on_market_date this version inherits (CRA guidance §15, Example 2).
    # NULL for original placements and post-substantial-modification releases.
    parent_release_id: UUID | None = None

    # Gap 5 — Article 13(10) consolidated support flag.
    # True when this release absorbs security update obligations for all older versions.
    is_consolidated_support_version: bool = False

    # Art. 13(7) + Art. 3(30): FK to the SubstantialModificationAssessment that
    # documents the substantiality determination for this release. Required for
    # v2+ releases (those with a parent_release_id) before gate approval.
    substantiality_analysis_id: UUID | None = None

    # Optional CRA traceability link: set when this release is a direct consequence
    # of a substantial modification assessment (CRA Art. 13(8) re-release obligation).
    caused_by_change_id: UUID | None = None

    # Gap 1 — CRA Art. 13(2) + Annex I Part I §2(a): release must not contain known
    # exploitable vulnerabilities. Flag must be False for the release gate to pass.
    has_known_exploitable_vulnerabilities: bool = False
    kev_notes: str | None = None

    # User-defined version name (optional: "Spring 2026", "RC-1", etc.)
    user_version: str | None = Field(default=None, max_length=100)

    # Gap 2 — hardware and software version components for embedded products.
    # Null for pure-software products; only surfaced when is_embedded_product is True.
    hardware_version: str | None = Field(default=None, max_length=150)
    software_version: str | None = Field(default=None, max_length=150)

    # CRA Art. 28 + Annex V — EU Declaration of Conformity metadata.
    # eu_doc_date must be on or before placed_on_market_date (enforced in service layer).
    eu_doc_date: date | None = None
    eu_doc_number: str | None = Field(default=None, max_length=100)
    eu_doc_notified_body: str | None = Field(default=None, max_length=255)


class ProductReleaseCreate(ProductReleaseBase):
    # Gap 1 — IDs of remote processing elements in scope for this release.
    # The service strips this field before constructing the ORM object and
    # uses it to populate the M2M release_remote_processing_elements join table.
    remote_processing_element_ids: list[UUID] = []


class ProductReleaseUpdate(BaseModel):
    release_status: ReleaseStatus | None = None
    planned_release_date: datetime | None = None
    actual_release_date: datetime | None = None
    # Gap 3 — allow setting/correcting the formal placement date after creation
    placed_on_market_date: date | None = None
    classification_snapshot: ProductClassification | None = None
    conformity_route_snapshot: ConformityRoute | None = None
    release_notes: str | None = None
    # Gap 2 — allow correcting the parent release link if set incorrectly
    parent_release_id: UUID | None = None
    # Gap 5 — can be toggled after release if the manufacturer designates this
    # version as the Article 13(10) consolidated support version
    is_consolidated_support_version: bool | None = None
    # Art. 13(7): link the substantiality analysis assessment to this release;
    # can be set or corrected after creation
    substantiality_analysis_id: UUID | None = None
    # Allow updating the causal change link even after creation (e.g. if
    # the association was missed at release time and needs to be corrected)
    caused_by_change_id: UUID | None = None
    # Gap 1 — KEV status can be updated as vulnerabilities are found/fixed
    has_known_exploitable_vulnerabilities: bool | None = None
    kev_notes: str | None = None

    # CRA Art. 28 — EU DoC fields can be updated after creation (e.g. number assigned later)
    eu_doc_date: date | None = None
    eu_doc_number: str | None = Field(default=None, max_length=100)
    eu_doc_notified_body: str | None = Field(default=None, max_length=255)


class ProductReleaseRead(ProductReleaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    system_version: int  # Auto-incremented version number
    product_name: str | None = None  # Populated via the product relationship
    # Gap 1 — remote processing elements linked to this release via the M2M join table.
    release_remote_processing_elements: list[RemoteProcessingElementRead] = []
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore
    @property
    def system_version_label(self) -> str:
        """Display system version as v1, v2, v3"""
        return f"v{self.system_version}"

    @computed_field  # type: ignore
    @property
    def display_version(self) -> str:
        """
        Smart display:
        - If user_version is set: "Spring 2026 (v2)"
        - If not set: "v2"
        """
        if self.user_version:
            return f"{self.user_version} ({self.system_version_label})"
        return self.system_version_label