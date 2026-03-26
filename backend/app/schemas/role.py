from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import ORMBaseModel


class RoleCreate(BaseModel):
    name: str
    description: str | None = None


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RolePermissionsUpdate(BaseModel):
    permission_ids: list[UUID]


class RoleRead(ORMBaseModel):
    id: UUID
    name: str
    description: str | None
    permissions: list[str]