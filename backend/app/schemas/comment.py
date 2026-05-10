from __future__ import annotations

from datetime import datetime
from uuid import UUID

import bleach
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Tags and attributes permitted in comment bodies (rich text without active content).
_ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "p", "br", "ul", "ol", "li", "code", "pre"]
_ALLOWED_ATTRS = {"a": ["href", "title"]}


def _sanitize_body(value: str) -> str:
    """Strip disallowed HTML from a comment body before storage."""
    return bleach.clean(value, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS)


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
    @field_validator("body")
    @classmethod
    def sanitize_body(cls, v: str) -> str:
        return _sanitize_body(v)


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1)

    @field_validator("body")
    @classmethod
    def sanitize_body(cls, v: str) -> str:
        return _sanitize_body(v)


class CommentRead(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_user_id: UUID
    author: AuthorRead | None = None
    created_at: datetime
    updated_at: datetime
