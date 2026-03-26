from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ConformityRoute, ProductClassification, ReleaseStatus


class ProductBase(BaseModel):
    product_code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    parent_product_id: UUID | None = None
    manufacturer_name: str = Field(min_length=1, max_length=255)
    intended_use: str = Field(min_length=1)
    product_type: str = Field(min_length=1, max_length=150)
    current_classification: ProductClassification = ProductClassification.normal
    scope_status: str = "undecided"


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    parent_product_id: UUID | None = None
    manufacturer_name: str | None = Field(default=None, min_length=1, max_length=255)
    intended_use: str | None = Field(default=None, min_length=1)
    product_type: str | None = Field(default=None, min_length=1, max_length=150)
    current_classification: ProductClassification | None = None
    scope_status: str | None = None


class ProductSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_code: str
    name: str
    manufacturer_name: str
    product_type: str
    current_classification: ProductClassification
    scope_status: str
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
    version: str
    release_status: ReleaseStatus
    classification_snapshot: ProductClassification
    conformity_route_snapshot: ConformityRoute
    planned_release_date: datetime | None
    actual_release_date: datetime | None
    created_at: datetime
    updated_at: datetime


class RemoteProcessingElementSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    provider_name: str | None
    geographic_location: str | None
    criticality: str | None
    created_at: datetime
    updated_at: datetime


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class ProductDetailRead(ProductRead):
    child_products: list[ProductHierarchyNode] = []
    releases: list[ProductReleaseSummaryRead] = []
    remote_processing_elements: list[RemoteProcessingElementSummaryRead] = []