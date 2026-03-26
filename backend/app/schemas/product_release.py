from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ConformityRoute, ProductClassification, ReleaseStatus


class ProductReleaseBase(BaseModel):
    product_id: UUID
    version: str = Field(min_length=1, max_length=100)
    release_status: ReleaseStatus = ReleaseStatus.draft
    planned_release_date: datetime | None = None
    actual_release_date: datetime | None = None
    classification_snapshot: ProductClassification = ProductClassification.normal
    conformity_route_snapshot: ConformityRoute = ConformityRoute.undecided
    release_notes: str | None = None


class ProductReleaseCreate(ProductReleaseBase):
    pass


class ProductReleaseUpdate(BaseModel):
    version: str | None = Field(default=None, min_length=1, max_length=100)
    release_status: ReleaseStatus | None = None
    planned_release_date: datetime | None = None
    actual_release_date: datetime | None = None
    classification_snapshot: ProductClassification | None = None
    conformity_route_snapshot: ConformityRoute | None = None
    release_notes: str | None = None


class ProductReleaseRead(ProductReleaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime