from __future__ import annotations

from pydantic import EmailStr

from app.schemas.common import TimestampedRead


class UserCreate(TimestampedRead):
    email: EmailStr
    full_name: str
    roles: list[str]


class UserRead(TimestampedRead):
    email: EmailStr
    full_name: str
    roles: list[str]
    is_active: bool