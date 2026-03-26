from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import AnnexPart
from app.schemas.common import ORMBaseModel, TimestampedRead


class AnnexRequirementCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    annex_part: AnnexPart
    is_active: bool = True


class AnnexRequirementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    annex_part: AnnexPart | None = None
    is_active: bool | None = None


class AnnexRequirementRead(TimestampedRead):
    code: str
    title: str
    description: str
    annex_part: AnnexPart
    is_active: bool


class AnnexRequirementSummaryRead(ORMBaseModel):
    id: UUID
    code: str
    title: str
    annex_part: AnnexPart
    is_active: bool