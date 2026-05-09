"""
Comment — generic threaded comments attached to any entity in the system.

A single table stores comments for all entity types (vulnerability reports,
changes, market actions, release gates, etc.) using a polymorphic
entity_type / entity_id pair.  This avoids per-entity comment tables and
means new features get comments for free.
"""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class Comment(UUIDTimestampMixin, Base):
    __tablename__ = "comments"

    # Polymorphic target — which entity type this comment belongs to.
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # UUID of the target entity record.
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # The user who wrote the comment.
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Comment body — plain text, no markup enforced at the DB level.
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # Eager-load author so the API can return name/email without an extra query.
    author: Mapped["User"] = relationship("User", lazy="select")
