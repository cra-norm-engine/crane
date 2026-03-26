from __future__ import annotations

from uuid import UUID

from pydantic import EmailStr

from app.schemas.common import ORMBaseModel, TimestampedRead


class UserCreate(ORMBaseModel):
    email: EmailStr
    full_name: str
    roles: list[str]


class UserRead(TimestampedRead):
    email: EmailStr
    full_name: str
    roles: list[str]
    is_active: bool


class UserSummaryRead(ORMBaseModel):
    id: UUID
    email: EmailStr
    full_name: str