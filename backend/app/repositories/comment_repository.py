from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.comment import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Comment)

    def list_for_entity(self, entity_type: str, entity_id: UUID) -> list[Comment]:
        """Return all comments for an entity, oldest first."""
        statement = (
            select(Comment)
            .where(Comment.entity_type == entity_type, Comment.entity_id == entity_id)
            .order_by(Comment.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_or_404(self, comment_id: UUID) -> Comment:
        comment = self.get_by_id(comment_id)
        if comment is None:
            raise NotFoundException("Comment not found")
        return comment
