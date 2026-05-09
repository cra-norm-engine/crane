from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, ForbiddenException
from app.models.comment import Comment
from app.models.enums import AuditStatus, EntityType
from app.repositories.comment_repository import CommentRepository
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate


class CommentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CommentRepository(db)

    def list_comments(self, entity_type: str, entity_id: UUID) -> list[CommentRead]:
        comments = self.repository.list_for_entity(entity_type, entity_id)
        return [CommentRead.model_validate(c) for c in comments]

    def create_comment(self, payload: CommentCreate, actor: object) -> CommentRead:
        comment = Comment(
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            body=payload.body,
            author_user_id=getattr(actor, "id"),
        )
        try:
            self.repository.add(comment)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="comment.created",
                entity_type=EntityType.comment,
                entity_id=comment.id,
                status=AuditStatus.success,
                details_json={
                    "entity_type": comment.entity_type,
                    "entity_id": str(comment.entity_id),
                },
            )
            self.db.commit()
            self.db.refresh(comment)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create comment") from exc
        return CommentRead.model_validate(comment)

    def update_comment(self, comment_id: UUID, payload: CommentUpdate, actor: object) -> CommentRead:
        comment = self.repository.get_or_404(comment_id)

        # Only the original author may edit a comment.
        if comment.author_user_id != getattr(actor, "id"):
            raise ForbiddenException("You can only edit your own comments")

        comment.body = payload.body
        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="comment.updated",
                entity_type=EntityType.comment,
                entity_id=comment.id,
                status=AuditStatus.success,
                details_json={
                    "entity_type": comment.entity_type,
                    "entity_id": str(comment.entity_id),
                },
            )
            self.db.commit()
            self.db.refresh(comment)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to update comment") from exc
        return CommentRead.model_validate(comment)

    def delete_comment(self, comment_id: UUID, actor: object) -> None:
        comment = self.repository.get_or_404(comment_id)

        # Authors may delete their own comments; admins may delete any comment.
        actor_roles = {
            getattr(ur.role, "name", None)
            for ur in getattr(actor, "roles", []) or []
        }
        is_admin = "admin" in actor_roles
        is_author = comment.author_user_id == getattr(actor, "id")

        if not is_author and not is_admin:
            raise ForbiddenException("You can only delete your own comments")

        self.repository.delete(comment)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="comment.deleted",
            entity_type=EntityType.comment,
            entity_id=comment_id,
            status=AuditStatus.success,
            details_json={
                "entity_type": comment.entity_type,
                "entity_id": str(comment.entity_id),
            },
        )
        self.db.commit()
