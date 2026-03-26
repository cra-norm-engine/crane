from __future__ import annotations

from uuid import UUID

from app.schemas.common import ORMBaseModel


class PermissionRead(ORMBaseModel):
    id: UUID
    key: str
    description: str | None = None