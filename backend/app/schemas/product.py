from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    description: str | None = None
    manufacturer_name: str
    manufacturer_contact: str | None = None
    product_classification: str = "normal"
    conformity_route: str = "undecided"
    support_period_end_date: datetime | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    manufacturer_name: str | None = None
    manufacturer_contact: str | None = None
    product_classification: str | None = None
    conformity_route: str | None = None
    support_period_end_date: datetime | None = None


class ProductRead(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
