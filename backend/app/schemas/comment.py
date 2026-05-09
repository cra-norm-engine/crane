from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuthorRead(BaseModel):
    """Minimal user projection embedded in comment responses."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str | None = None
    email: str


class CommentBase(BaseModel):
    entity_type: str = Field(min_length=1, max_length=100)
    entity_id: UUID
    body: str = Field(min_length=1)


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1)


class CommentRead(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_user_id: UUID
    author: AuthorRead | None = None
    created_at: datetime
    updated_at: datetime
