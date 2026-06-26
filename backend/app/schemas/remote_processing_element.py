# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import RemoteProcessingClassification, RemoteProcessingElementType


class RemoteProcessingElementBase(BaseModel):
    product_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    provider_name: str | None = Field(default=None, max_length=255)
    data_processed: str | None = None
    geographic_location: str | None = Field(default=None, max_length=255)
    criticality: str | None = Field(default=None, max_length=100)
    # CRA Art. 3(2) fields — writeable on create and update
    element_type: RemoteProcessingElementType | None = None
    # CRA Art. 3(2) inclusion criteria (1-4); None = not yet answered.
    is_developed_by_manufacturer: bool | None = None
    is_necessary_for_product_function: bool | None = None
    directly_interacts_with_product: bool | None = None
    has_bidirectional_exchange: bool | None = None
    provider_is_nis2_msp: bool | None = None
    classification: RemoteProcessingClassification = RemoteProcessingClassification.not_assessed
    classification_rationale: str | None = None


class RemoteProcessingElementCreate(RemoteProcessingElementBase):
    pass


class RemoteProcessingElementUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    provider_name: str | None = Field(default=None, max_length=255)
    data_processed: str | None = None
    geographic_location: str | None = Field(default=None, max_length=255)
    criticality: str | None = Field(default=None, max_length=100)
    element_type: RemoteProcessingElementType | None = None
    is_developed_by_manufacturer: bool | None = None
    is_necessary_for_product_function: bool | None = None
    directly_interacts_with_product: bool | None = None
    has_bidirectional_exchange: bool | None = None
    provider_is_nis2_msp: bool | None = None
    classification: RemoteProcessingClassification | None = None
    classification_rationale: str | None = None


class RemoteProcessingElementRead(RemoteProcessingElementBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assessed_at: datetime | None = None
    assessed_by_user_id: UUID | None = None
    # Display name of the user who ran the evaluation, resolved from the assessed_by relationship.
    assessed_by_name: str | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _resolve_assessed_by_name(cls, data: Any) -> Any:
        # When validating from an ORM object (from_attributes), the assessor's name is not a
        # column, so resolve it from the assessed_by relationship and inject it for validation.
        if isinstance(data, dict):
            return data
        assessed_by = getattr(data, "assessed_by", None)
        full_name = getattr(assessed_by, "full_name", None)
        if not full_name:
            return data
        # Build a dict of the fields Pydantic needs, plus the resolved assessor name.
        values: dict[str, Any] = {
            name: getattr(data, name) for name in cls.model_fields if name != "assessed_by_name"
        }
        values["assessed_by_name"] = full_name
        return values


class RemoteProcessingAssessRequest(BaseModel):
    """Payload for the CRA Art. 3(2) RDPS evaluation wizard.

    The four boolean fields correspond to the four inclusion criteria:
      Criterion 1 — is_developed_by_manufacturer
      Criterion 2 — is_necessary_for_product_function
      Criterion 3 — directly_interacts_with_product
      Criterion 4 — has_bidirectional_exchange

    All four must be True for an element to be classified as cra_art_3_2_in_scope.
    A False on any criterion leads to out_of_scope or third_party_component.
    None means the question has not been answered yet.
    """
    # Criterion 1: Designed/developed by or on behalf of the manufacturer for this specific product.
    is_developed_by_manufacturer: bool | None = None
    # Criterion 2: Absence of the service would prevent the product from performing its functions.
    is_necessary_for_product_function: bool | None = None
    # Criterion 3: The service directly interacts with the product itself (not just with users).
    directly_interacts_with_product: bool | None = None
    # Criterion 4: Data exchange is bidirectional — product sends data, RDPS processes and returns a result.
    has_bidirectional_exchange: bool | None = None
    # Context: is the third-party provider already covered by NIS2 as an MSP?
    provider_is_nis2_msp: bool | None = None
    classification_rationale: str | None = None
    # Optional manual override for edge cases not covered by the decision tree.
    classification_override: RemoteProcessingClassification | None = None
