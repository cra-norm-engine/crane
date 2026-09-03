from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event, snapshot_model
from app.core.config import settings
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException, ValidationException
from app.models.artifact import ArtifactRevision
from app.models.audit_log_event import AuditLogEvent
from app.models.base import utc_now
from app.models.comment import Comment
from app.models.enums import AuditStatus, EntityType
from app.models.manual_task import ManualTask, ManualTaskArtifactLink, TaskNotification
from app.models.product import Product, ProductRelease
from app.models.user import User
from app.schemas.my_tasks import ManualTaskCreate, ManualTaskUpdate, TaskActivityRead, TaskNotificationRead


class ManualTaskService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def visible_task(self, task_id: UUID, actor: User) -> ManualTask:
        task = self.db.scalar(select(ManualTask).where(
            ManualTask.id == task_id,
            or_(ManualTask.created_by_user_id == actor.id, ManualTask.assigned_to_user_id == actor.id),
        ))
        if task is None:
            raise NotFoundException("Task not found")
        return task

    def list(
        self, actor: User, *, scope: str = "all", state: str = "all",
        priority: str | None = None, product_id: UUID | None = None,
        product_release_id: UUID | None = None, search: str | None = None,
    ) -> list[ManualTask]:
        stmt = select(ManualTask)
        if scope == "my_work":
            stmt = stmt.where(ManualTask.assigned_to_user_id == actor.id)
        elif scope == "assigned_by_me":
            stmt = stmt.where(ManualTask.created_by_user_id == actor.id, ManualTask.assigned_to_user_id != actor.id)
        elif scope == "all":
            stmt = stmt.where(or_(ManualTask.created_by_user_id == actor.id, ManualTask.assigned_to_user_id == actor.id))
        else:
            raise ValidationException("Invalid task scope")
        if state == "open":
            stmt = stmt.where(ManualTask.status != "completed", ManualTask.archived_at.is_(None))
        elif state == "completed":
            stmt = stmt.where(ManualTask.status == "completed", ManualTask.archived_at.is_(None))
        elif state == "archived":
            stmt = stmt.where(ManualTask.archived_at.is_not(None))
        elif state != "all":
            raise ValidationException("Invalid task state")
        if priority:
            if priority not in {"low", "medium", "high"}:
                raise ValidationException("Invalid task priority")
            stmt = stmt.where(ManualTask.priority == priority)
        if product_id:
            stmt = stmt.where(ManualTask.product_id == product_id)
        if product_release_id:
            stmt = stmt.where(ManualTask.product_release_id == product_release_id)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(or_(ManualTask.title.ilike(term), ManualTask.description.ilike(term)))
        return list(self.db.scalars(stmt.order_by(ManualTask.updated_at.desc())).all())

    def create(self, payload: ManualTaskCreate, actor: User) -> ManualTask:
        assignee, _, _ = self._validate(payload, actor)
        task = ManualTask(
            title=payload.title.strip(), description=payload.description, due_date=payload.due_date,
            priority=payload.priority, assigned_to_user_id=assignee.id,
            product_id=payload.product_id, product_release_id=payload.product_release_id,
            parent_task_id=payload.parent_task_id,
            created_by_user_id=actor.id,
        )
        self.db.add(task)
        self.db.flush()
        self._audit(task, actor, "manual_task.created", {"snapshot": snapshot_model(task)})
        self._notify(task, assignee.id, "assigned", "New task assigned", task.title, f"assigned:{task.id}:{assignee.id}", actor.id)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(self, task_id: UUID, payload: ManualTaskUpdate, actor: User) -> ManualTask:
        task = self.visible_task(task_id, actor)
        if task.created_by_user_id != actor.id:
            raise ForbiddenException("Only the task creator can edit its definition")
        changes = payload.model_dump(exclude_unset=True)
        if changes.get("title", task.title) is None or changes.get("priority", task.priority) is None:
            raise ValidationException("Title and priority cannot be null")
        effective = ManualTaskCreate(
            title=changes.get("title", task.title),
            description=changes.get("description", task.description),
            due_date=changes.get("due_date", task.due_date),
            priority=changes.get("priority", task.priority),
            assigned_to_user_id=changes.get("assigned_to_user_id", task.assigned_to_user_id),
            product_id=changes.get("product_id", task.product_id),
            product_release_id=changes.get("product_release_id", task.product_release_id),
            parent_task_id=changes.get("parent_task_id", task.parent_task_id),
        )
        if effective.parent_task_id == task.id:
            raise ValidationException("A task cannot be its own parent")
        assignee, _, _ = self._validate(effective, actor)
        before = snapshot_model(task)
        old_assignee = task.assigned_to_user_id
        task.title, task.description, task.due_date, task.priority = effective.title.strip(), effective.description, effective.due_date, effective.priority
        task.assigned_to_user_id, task.product_id, task.product_release_id, task.parent_task_id = assignee.id, effective.product_id, effective.product_release_id, effective.parent_task_id
        self.db.flush()
        after = snapshot_model(task)
        changed = {key: {"before": before[key], "after": after[key]} for key in after if before.get(key) != after[key]}
        self._audit(task, actor, "manual_task.updated", {"changes": changed})
        if old_assignee != assignee.id:
            self._audit(task, actor, "manual_task.reassigned", {"before": str(old_assignee), "after": str(assignee.id)})
            self._notify(task, assignee.id, "reassigned", "Task reassigned to you", task.title, f"reassigned:{task.id}:{assignee.id}:{task.updated_at}", actor.id)
        self.db.commit()
        self.db.refresh(task)
        return task

    def set_status(self, task_id: UUID, status: str, actor: User) -> ManualTask:
        if status not in {"open", "in_progress", "completed"}:
            raise ValidationException("Invalid task status")
        task = self.visible_task(task_id, actor)
        if task.assigned_to_user_id != actor.id:
            raise ForbiddenException("Only the assignee can update task status")
        if task.archived_at:
            raise ConflictException("Restore this task before changing its status")
        if status == "completed":
            return self.complete(task_id, None, actor)
        old_status = task.status
        if old_status == "completed":
            raise ValidationException("Use reopen with a reason to reopen a completed task")
        task.status = status
        self._audit(task, actor, "manual_task.status_changed", {"before": old_status, "after": status})
        self.db.commit()
        self.db.refresh(task)
        return task

    def complete(self, task_id: UUID, note: str | None, actor: User) -> ManualTask:
        task = self.visible_task(task_id, actor)
        if task.assigned_to_user_id != actor.id:
            raise ForbiddenException("Only the assignee can complete this task")
        if task.archived_at:
            raise ConflictException("Restore this task before completing it")
        if task.status == "completed":
            return task
        if task.priority == "high" and not (note and note.strip()) and not task.artifact_links:
            raise ValidationException("High-priority tasks require a completion note or evidence")
        task.status, task.completed_at, task.completed_by_user_id = "completed", utc_now(), actor.id
        task.completion_note = note.strip() if note and note.strip() else None
        self._audit(task, actor, "manual_task.completed", {"completion_note_provided": bool(task.completion_note)})
        if task.created_by_user_id != actor.id:
            self._notify(task, task.created_by_user_id, "completed", "Task completed", task.title, f"completed:{task.id}:{task.completed_at}", actor.id)
        self.db.commit()
        self.db.refresh(task)
        return task

    def reopen(self, task_id: UUID, reason: str, actor: User) -> ManualTask:
        task = self.visible_task(task_id, actor)
        if actor.id not in {task.created_by_user_id, task.assigned_to_user_id}:
            raise ForbiddenException()
        if task.archived_at:
            raise ConflictException("Restore this task before reopening it")
        task.status, task.completed_at, task.completed_by_user_id, task.completion_note = "open", None, None, None
        self._audit(task, actor, "manual_task.reopened", {"reason": reason.strip()})
        other = task.assigned_to_user_id if actor.id == task.created_by_user_id else task.created_by_user_id
        self._notify(task, other, "reopened", "Task reopened", task.title, f"reopened:{task.id}:{utc_now().isoformat()}", actor.id)
        self.db.commit(); self.db.refresh(task)
        return task

    def archive(self, task_id: UUID, reason: str, actor: User) -> ManualTask:
        task = self.visible_task(task_id, actor)
        if task.created_by_user_id != actor.id:
            raise ForbiddenException("Only the creator can archive this task")
        task.archived_at, task.archived_by_user_id, task.archive_reason = utc_now(), actor.id, reason.strip()
        self._audit(task, actor, "manual_task.archived", {"reason": task.archive_reason})
        self.db.commit(); self.db.refresh(task)
        return task

    def restore(self, task_id: UUID, actor: User) -> ManualTask:
        task = self.visible_task(task_id, actor)
        if task.created_by_user_id != actor.id:
            raise ForbiddenException("Only the creator can restore this task")
        task.archived_at = task.archived_by_user_id = task.archive_reason = None
        self._audit(task, actor, "manual_task.restored", {})
        self.db.commit(); self.db.refresh(task)
        return task

    def attach_artifact(self, task_id: UUID, revision_id: UUID, actor: User) -> ManualTask:
        task = self.visible_task(task_id, actor)
        if task.assigned_to_user_id != actor.id:
            raise ForbiddenException("Only the assignee can attach completion evidence")
        if task.archived_at:
            raise ConflictException("Archived tasks are read-only")
        revision = self.db.get(ArtifactRevision, revision_id)
        if revision is None:
            raise NotFoundException("Artifact revision not found")
        exists = self.db.scalar(select(ManualTaskArtifactLink).where(
            ManualTaskArtifactLink.manual_task_id == task.id,
            ManualTaskArtifactLink.artifact_revision_id == revision_id,
        ))
        if not exists:
            self.db.add(ManualTaskArtifactLink(manual_task_id=task.id, artifact_revision_id=revision_id, linked_by_user_id=actor.id))
            self._audit(task, actor, "manual_task.evidence_attached", {"artifact_revision_id": str(revision_id)})
            self.db.commit(); self.db.refresh(task)
        return task

    def detach_artifact(self, task_id: UUID, revision_id: UUID, actor: User) -> ManualTask:
        task = self.visible_task(task_id, actor)
        if task.assigned_to_user_id != actor.id:
            raise ForbiddenException("Only the assignee can remove completion evidence")
        if task.archived_at:
            raise ConflictException("Archived tasks are read-only")
        link = self.db.scalar(select(ManualTaskArtifactLink).where(
            ManualTaskArtifactLink.manual_task_id == task.id,
            ManualTaskArtifactLink.artifact_revision_id == revision_id,
        ))
        if link:
            self.db.delete(link)
            self._audit(task, actor, "manual_task.evidence_detached", {"artifact_revision_id": str(revision_id)})
            self.db.commit(); self.db.refresh(task)
        return task

    def activity(self, task_id: UUID, actor: User) -> list[TaskActivityRead]:
        self.visible_task(task_id, actor)
        events = list(self.db.scalars(select(AuditLogEvent).where(
            AuditLogEvent.entity_type == EntityType.manual_task,
            AuditLogEvent.entity_id == task_id,
        )).all())
        comments = list(self.db.scalars(select(Comment).where(Comment.entity_type == "manual_task", Comment.entity_id == task_id)).all())
        actor_ids = {e.actor_user_id for e in events if e.actor_user_id} | {c.author_user_id for c in comments}
        users = {u.id: u for u in self.db.scalars(select(User).where(User.id.in_(actor_ids))).all()} if actor_ids else {}
        rows = [TaskActivityRead(id=e.id, occurred_at=e.occurred_at, actor_name=self._display(users.get(e.actor_user_id)), action_type=e.action_type, details=e.details_json) for e in events]
        rows += [TaskActivityRead(id=c.id, occurred_at=c.created_at, actor_name=self._display(users.get(c.author_user_id)), action_type="comment.created", details={}) for c in comments]
        return sorted(rows, key=lambda row: row.occurred_at, reverse=True)

    def notifications(self, actor: User, unread_only: bool = False) -> list[TaskNotificationRead]:
        self.generate_due_notifications(actor.id)
        stmt = select(TaskNotification).where(TaskNotification.recipient_user_id == actor.id)
        if unread_only:
            stmt = stmt.where(TaskNotification.read_at.is_(None))
        return [TaskNotificationRead.model_validate(n, from_attributes=True) for n in self.db.scalars(stmt.order_by(TaskNotification.created_at.desc()).limit(100)).all()]

    def mark_notification_read(self, notification_id: UUID, actor: User) -> None:
        item = self.db.scalar(select(TaskNotification).where(TaskNotification.id == notification_id, TaskNotification.recipient_user_id == actor.id))
        if item is None:
            raise NotFoundException("Notification not found")
        item.read_at = utc_now(); self.db.commit()

    def generate_due_notifications(self, user_id: UUID | None = None) -> None:
        today = date.today()
        stmt = select(ManualTask).where(ManualTask.status != "completed", ManualTask.archived_at.is_(None), ManualTask.due_date.is_not(None))
        if user_id:
            stmt = stmt.where(ManualTask.assigned_to_user_id == user_id)
        for task in self.db.scalars(stmt).all():
            event = "overdue" if task.due_date < today else "due_soon" if task.due_date <= today + timedelta(days=settings.task_due_warning_days) else None
            if event:
                self._notify(task, task.assigned_to_user_id, event, "Task overdue" if event == "overdue" else "Task due soon", task.title, f"{event}:{task.id}:{task.due_date}")
        self.db.commit()

    def _validate(self, payload: ManualTaskCreate, actor: User) -> tuple[User, Product | None, ProductRelease | None]:
        if not payload.title.strip():
            raise ValidationException("Title must not be blank")
        assignee = self.db.get(User, payload.assigned_to_user_id) if payload.assigned_to_user_id else actor
        product = self.db.get(Product, payload.product_id) if payload.product_id else None
        release = self.db.get(ProductRelease, payload.product_release_id) if payload.product_release_id else None
        if assignee is None or not assignee.is_active:
            raise ValidationException("Assignee must be an active user")
        if payload.product_id and product is None:
            raise ValidationException("Product not found")
        if payload.product_release_id and (release is None or not product or release.product_id != product.id):
            raise ValidationException("Release must belong to the selected product")
        if payload.parent_task_id:
            if payload.parent_task_id == getattr(payload, "id", None):
                raise ValidationException("A task cannot be its own parent")
            parent = self.db.get(ManualTask, payload.parent_task_id)
            if parent is None or parent.created_by_user_id != actor.id:
                raise ValidationException("Parent task not found")
        return assignee, product, release

    def _audit(self, task: ManualTask, actor: User, action: str, details: dict) -> None:
        create_audit_event(self.db, actor_user_id=actor.id, action_type=action, entity_type=EntityType.manual_task, entity_id=task.id, status=AuditStatus.success, details_json={**details, "product_id": str(task.product_id) if task.product_id else None, "product_release_id": str(task.product_release_id) if task.product_release_id else None})

    def _notify(self, task: ManualTask, recipient: UUID, event: str, title: str, message: str, dedupe: str, actor_id: UUID | None = None) -> None:
        if recipient == actor_id or self.db.scalar(select(TaskNotification.id).where(TaskNotification.dedupe_key == dedupe)):
            return
        self.db.add(TaskNotification(manual_task_id=task.id, recipient_user_id=recipient, event_type=event, title=title, message=message, dedupe_key=dedupe))

    @staticmethod
    def _display(user: User | None) -> str | None:
        return (user.full_name.strip() or user.email) if user else None
