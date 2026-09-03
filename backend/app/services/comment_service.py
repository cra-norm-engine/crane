# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.comment import Comment
from app.models.manual_task import ManualTask, TaskNotification
from app.models.enums import AuditStatus, EntityType
from app.repositories.comment_repository import CommentRepository
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate


class CommentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CommentRepository(db)

    def list_comments(self, entity_type: str, entity_id: UUID, actor: object | None = None) -> list[CommentRead]:
        if entity_type == "manual_task":
            self._manual_task_for_actor(entity_id, actor)
        comments = self.repository.list_for_entity(entity_type, entity_id)
        return [CommentRead.model_validate(c) for c in comments]

    def create_comment(self, payload: CommentCreate, actor: object) -> CommentRead:
        if payload.entity_type == "manual_task":
            task = self._manual_task_for_actor(payload.entity_id, actor)
            if task.archived_at:
                raise ConflictException("Archived tasks are read-only")
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
            if comment.entity_type == "manual_task":
                task = self.db.get(ManualTask, comment.entity_id)
                if task:
                    recipients = {task.created_by_user_id, task.assigned_to_user_id} - {comment.author_user_id}
                    for recipient_id in recipients:
                        self.db.add(TaskNotification(
                            manual_task_id=task.id,
                            recipient_user_id=recipient_id,
                            event_type="commented",
                            title="New task comment",
                            message=task.title,
                            dedupe_key=f"commented:{comment.id}:{recipient_id}",
                        ))
            self.db.commit()
            self.db.refresh(comment)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create comment") from exc
        return CommentRead.model_validate(comment)

    def update_comment(self, comment_id: UUID, payload: CommentUpdate, actor: object) -> CommentRead:
        comment = self.repository.get_or_404(comment_id)
        if comment.entity_type == "manual_task":
            task = self._manual_task_for_actor(comment.entity_id, actor)
            if task.archived_at:
                raise ConflictException("Archived tasks are read-only")

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
        if comment.entity_type == "manual_task":
            task = self._manual_task_for_actor(comment.entity_id, actor)
            if task.archived_at:
                raise ConflictException("Archived tasks are read-only")

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

    def _manual_task_for_actor(self, task_id: UUID, actor: object | None) -> ManualTask:
        task = self.db.get(ManualTask, task_id)
        actor_id = getattr(actor, "id", None)
        if task is None or actor_id not in {task.created_by_user_id, task.assigned_to_user_id}:
            raise NotFoundException("Task not found")
        return task
