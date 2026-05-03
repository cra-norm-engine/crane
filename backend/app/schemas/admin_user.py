from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMBaseModel


class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8, max_length=255)
    role_ids: list[UUID] = []


class AdminUserRoleUpdate(BaseModel):
    role_ids: list[UUID]


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminUserRead(ORMBaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    roles: list[str]
    is_active: bool
    auth_provider: str
    must_change_password: bool