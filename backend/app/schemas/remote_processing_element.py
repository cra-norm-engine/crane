from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    # DIGITALEUROPE inclusion criteria (I1/I3/I5/I6); None = not yet answered.
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
    created_at: datetime
    updated_at: datetime


class RemoteProcessingAssessRequest(BaseModel):
    """Payload for the DIGITALEUROPE-aligned CRA Art. 3(2) RDPS evaluation wizard.

    The four boolean fields correspond to the DIGITALEUROPE inclusion criteria:
      I1 — is_developed_by_manufacturer
      I3 — is_necessary_for_product_function
      I5 — directly_interacts_with_product
      I6 — has_bidirectional_exchange

    All four must be True for an element to be classified as cra_art_3_2_in_scope.
    A False on any criterion leads to out_of_scope or third_party_component.
    None means the question has not been answered yet.
    """
    # I1: Designed/developed by or on behalf of the manufacturer for this specific product.
    is_developed_by_manufacturer: bool | None = None
    # I3: Absence of the service would prevent the product from performing its functions.
    is_necessary_for_product_function: bool | None = None
    # I5: The service directly interacts with the product itself (not just with users).
    directly_interacts_with_product: bool | None = None
    # I6: Data exchange is bidirectional — product sends data, RDPS processes and returns a result.
    has_bidirectional_exchange: bool | None = None
    # Context: is the third-party provider already covered by NIS2 as an MSP?
    provider_is_nis2_msp: bool | None = None
    classification_rationale: str | None = None
    # Optional manual override for edge cases not covered by the decision tree.
    classification_override: RemoteProcessingClassification | None = None
