# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.enums import (
    ConformityRoute,
    ProductClassification,
    ProductLifecycleStatus,
    ProductType,
    ReleaseStatus,
    RemoteProcessingClassification,
    RemoteProcessingElementType,
)


class SystemProfile(BaseModel):
    # Phase 4 — system-as-product vs component-by-component strategy.
    sold_as_product: bool | None = None
    who_integrates_system: str | None = None
    marketed_as_product: bool | None = None
    core_minimum_products_combination: str | None = None


class TailorMadeTerms(BaseModel):
    # Phase 4 — B2B tailor-made product contract terms.
    customized_support_period: str | None = None
    customized_security_config: str | None = None
    specific_user: str | None = None
    agreement_via_contractual_terms: str | None = None


class ProductBase(BaseModel):
    product_code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    parent_product_id: UUID | None = None
    manufacturer_name: str = Field(min_length=1, max_length=255)
    # CRA Annex V(2) — manufacturer's registered trade address for the DoC (free text).
    manufacturer_address: str | None = None
    intended_use: str = Field(min_length=1)
    product_type: str = Field(min_length=1, max_length=150)
    current_classification: ProductClassification = ProductClassification.normal
    scope_status: str = "undecided"
    # CRA obligation tier: legacy (reporting-only) vs active (full obligations).
    lifecycle_status: ProductLifecycleStatus = ProductLifecycleStatus.active

    # Phase 3 — typed CRA product classification (software vs hardware+digital).
    product_type_class: ProductType = ProductType.undecided
    # Phase 3 — product-level conformity assessment route.
    conformity_route: ConformityRoute = ConformityRoute.undecided

    # Phase 2 — out-of-scope decision provenance. The signature/justification are
    # user-editable; scope_decided_by/at are stamped by the scope wizard.
    out_of_scope_justification: str | None = None
    scope_decision_signature: str | None = Field(default=None, max_length=255)

    # Phase 4 — additive system & tailor-made metadata (nullable JSON). Field
    # names match the model columns so create/update/read round-trip cleanly.
    system_profile_json: SystemProfile | None = None
    tailor_made_terms_json: TailorMadeTerms | None = None

    # Gap 2 — true when this product combines physical hardware with software/firmware
    # (e.g. embedded IoT devices). Enables per-release hardware_version and
    # software_version fields in the release creation form.
    is_embedded_product: bool = False

    # Gap 4 — Article 69(2): distinguishes products placed on market before CRA
    # full applicability (transition provisions apply to these products).
    is_pre_cra: bool = False

    # Gap 4 — Earliest known EU market placement date for this product line.
    # Required for pre-CRA products to anchor the transition period calculation.
    first_placed_on_market_date: date | None = None

    # Gap 4 — Annex I Part II §6: vulnerability reporting contact details.
    security_contact_email: str | None = Field(default=None, max_length=320)
    security_contact_url: str | None = Field(default=None, max_length=2048)

    # Economic operators (CRA Art. 13, 18–23). Free-text descriptions of the
    # other operators in the supply chain; surfaced in the compliance report's
    # "Economic operators" section. Optional — many products have none (e.g. a
    # manufacturer selling direct has no importer/distributor).
    authorised_representative: str | None = None
    importers: str | None = None
    distributors: str | None = None
    single_point_of_contact: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    # product_code is included here so the edit form can correct naming errors.
    # The uniqueness constraint on the DB column will reject duplicates at write time.
    product_code: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    parent_product_id: UUID | None = None
    manufacturer_name: str | None = Field(default=None, min_length=1, max_length=255)
    # CRA Annex V(2) — manufacturer's registered trade address for the DoC (free text).
    manufacturer_address: str | None = None
    intended_use: str | None = Field(default=None, min_length=1)
    product_type: str | None = Field(default=None, min_length=1, max_length=150)
    current_classification: ProductClassification | None = None
    scope_status: str | None = None
    lifecycle_status: ProductLifecycleStatus | None = None
    # Phase 3 — typed product classification + product-level conformity route.
    product_type_class: ProductType | None = None
    conformity_route: ConformityRoute | None = None
    # Phase 2 — allow manual entry/refinement of the out-of-scope decision.
    out_of_scope_justification: str | None = None
    scope_decision_signature: str | None = Field(default=None, max_length=255)
    # Phase 4 — additive system & tailor-made metadata.
    system_profile_json: SystemProfile | None = None
    tailor_made_terms_json: TailorMadeTerms | None = None
    # Gap 2 — allow toggling the embedded product flag after creation
    is_embedded_product: bool | None = None
    # Allow updating the pre-CRA flag and first placement date independently
    is_pre_cra: bool | None = None
    first_placed_on_market_date: date | None = None
    security_contact_email: str | None = Field(default=None, max_length=320)
    security_contact_url: str | None = Field(default=None, max_length=2048)
    # Economic operators (CRA Art. 13, 18–23) — editable post-creation.
    authorised_representative: str | None = None
    importers: str | None = None
    distributors: str | None = None
    single_point_of_contact: str | None = None


class ProductSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_code: str
    name: str
    manufacturer_name: str
    product_type: str
    current_classification: ProductClassification
    scope_status: str
    lifecycle_status: ProductLifecycleStatus
    # Phase 3 — typed classification + product-level conformity route in list view.
    product_type_class: ProductType
    conformity_route: ConformityRoute
    # Gap 2 — exposed so list views can show the embedded product indicator
    is_embedded_product: bool
    # Gap 4 — exposed in list views so the product list can flag pre-CRA products
    is_pre_cra: bool
    first_placed_on_market_date: date | None
    security_contact_email: str | None
    security_contact_url: str | None
    # Phase 2 — provenance surfaced so the list can flag unsigned out-of-scope rows.
    scope_decided_at: datetime | None
    scope_decision_signature: str | None
    # Phase 4 — lightweight boolean flags for the inventory "flags" chips (S/T/R),
    # resolved from model properties so the list need not ship the full JSON blobs.
    has_system_profile: bool
    has_tailor_made_terms: bool
    has_remote_processing: bool
    created_at: datetime
    updated_at: datetime


class ProductHierarchyNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_code: str
    name: str
    current_classification: ProductClassification
    scope_status: str


class ProductReleaseSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    system_version: int
    user_version: str | None
    # Gap 2 — hardware and software version components for embedded products
    hardware_version: str | None = None
    software_version: str | None = None
    release_status: ReleaseStatus
    classification_snapshot: ProductClassification
    conformity_route_snapshot: ConformityRoute
    planned_release_date: datetime | None
    actual_release_date: datetime | None

    # Gap 3 — formal EU placement date, separate from actual_release_date
    placed_on_market_date: date | None

    # Gap 2 — ID of the base release this non-substantial update derives from
    parent_release_id: UUID | None

    # Gap 5 — Article 13(10) consolidated support flag
    is_consolidated_support_version: bool

    # Gap 1 — Known exploitable vulnerability status for release gate
    has_known_exploitable_vulnerabilities: bool
    kev_notes: str | None

    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore
    @property
    def display_version(self) -> str:
        """
        Smart display:
        - If user_version is set: "Spring 2026 (v2)"
        - If not set: "v2"
        """
        if self.user_version:
            return f"{self.user_version} (v{self.system_version})"
        return f"v{self.system_version}"


class RemoteProcessingElementSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    provider_name: str | None
    geographic_location: str | None
    criticality: str | None
    element_type: RemoteProcessingElementType | None = None
    classification: RemoteProcessingClassification = RemoteProcessingClassification.not_assessed
    created_at: datetime
    updated_at: datetime


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    # Phase 2 — read-only decision provenance (stamped by the scope wizard).
    scope_decided_by_user_id: UUID | None = None
    scope_decided_at: datetime | None = None
    # Resolved signer display name (model property scope_decided_by_name).
    scope_decided_by_name: str | None = None
    created_at: datetime
    updated_at: datetime


class ProductDetailRead(ProductRead):
    child_products: list[ProductHierarchyNode] = []
    releases: list[ProductReleaseSummaryRead] = []
    remote_processing_elements: list[RemoteProcessingElementSummaryRead] = []