from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ConformityRoute, ProductClassification, ReleaseStatus


class ProductReleaseBase(BaseModel):
    product_id: UUID
    version: str = Field(min_length=1, max_length=100)
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

    # Optional CRA traceability link: set when this release is a direct consequence
    # of a substantial modification assessment (CRA Art. 13(8) re-release obligation).
    caused_by_change_id: UUID | None = None


class ProductReleaseCreate(ProductReleaseBase):
    pass


class ProductReleaseUpdate(BaseModel):
    version: str | None = Field(default=None, min_length=1, max_length=100)
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
    # Allow updating the causal change link even after creation (e.g. if
    # the association was missed at release time and needs to be corrected)
    caused_by_change_id: UUID | None = None


class ProductReleaseRead(ProductReleaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime