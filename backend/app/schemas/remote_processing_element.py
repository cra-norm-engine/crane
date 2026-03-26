from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RemoteProcessingElementBase(BaseModel):
    product_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    provider_name: str | None = Field(default=None, max_length=255)
    data_processed: str | None = None
    geographic_location: str | None = Field(default=None, max_length=255)
    criticality: str | None = Field(default=None, max_length=100)


class RemoteProcessingElementCreate(RemoteProcessingElementBase):
    pass


class RemoteProcessingElementUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    provider_name: str | None = Field(default=None, max_length=255)
    data_processed: str | None = None
    geographic_location: str | None = Field(default=None, max_length=255)
    criticality: str | None = Field(default=None, max_length=100)


class RemoteProcessingElementRead(RemoteProcessingElementBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime