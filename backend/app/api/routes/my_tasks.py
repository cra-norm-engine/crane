# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""
My Tasks endpoint — aggregates open items assigned to the current user
across all entity types that support task assignment:

  • vulnerability_reports      (assigned_to_user_id)
  • changes and their compliance actions (assigned_to_user_id)
  • release_gate_items         (assigned_to_user_id)
  • risk_items                 (owner_user_id)
  • lifecycle_notifications    (recipient_user_id, EOS alerts only)

Results are sorted: overdue first, then by due_date ascending, then no-date items last.
"""
from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.change import Change, ChangeComplianceAction, SubstantialModificationAssessment
from app.models.enums import (
    ArtifactReviewDecision,
    ChangeStatus,
    ComplianceActionStatus,
    LifecycleNotificationStatus,
    LifecycleNotificationType,
    RiskItemStatus,
    VulnerabilityLifecycleStatus,
)
from app.models.lifecycle_notification import LifecycleNotification
from app.models.manual_task import ManualTask
from app.models.product import Product, ProductRelease
from app.models.release_gate import ReleaseGate, ReleaseGateItem
from app.models.risk_item import RiskItem
from app.models.support_period_record import SupportPeriodRecord
from app.models.user import User
from app.models.vulnerability_report import VulnerabilityReport
from app.models.supplier_assessment import ComponentMaintainerNotification, SupplierAssessment
from app.schemas.my_tasks import (
    ManualTaskComplete, ManualTaskCreate, ManualTaskReason, ManualTaskStatusUpdate,
    ManualTaskUpdate, TaskActivityRead, TaskArtifactRead, TaskItem, TaskNotificationRead,
)
from app.repositories.user_repository import UserRepository
from app.services.manual_task_service import ManualTaskService

router = APIRouter()

# Terminal statuses excluded from My Tasks — records in these states are done.
_VULN_TERMINAL = {
    VulnerabilityLifecycleStatus.fixed,
    VulnerabilityLifecycleStatus.disclosed,
    VulnerabilityLifecycleStatus.retired,
}
_CHANGE_TERMINAL = {ChangeStatus.closed}
_GATE_TERMINAL = {ArtifactReviewDecision.accepted}
_RISK_TERMINAL = {RiskItemStatus.mitigated, RiskItemStatus.accepted, RiskItemStatus.closed}


def _is_overdue(due_date: date | None) -> bool:
    return due_date is not None and due_date < date.today()


def _sort_key(task: TaskItem) -> tuple:
    # Overdue tasks first (0), then by date ascending (1 with date), then no date (2).
    if task.is_overdue:
        return (0, task.due_date or date.max)
    if task.due_date:
        return (1, task.due_date)
    return (2, date.max)


def _user_display(user: User | None) -> str | None:
    if user is None:
        return None
    return user.full_name.strip() if user.full_name and user.full_name.strip() else user.email


def _release_display(release: ProductRelease | None) -> str | None:
    if release is None:
        return None
    system_label = f"v{release.system_version}"
    return f"{release.user_version} ({system_label})" if release.user_version else system_label


def _manual_task_item(
    task: ManualTask,
    viewer_id: UUID,
    db: Session,
) -> TaskItem:
    creator = db.get(User, task.created_by_user_id)
    assignee = db.get(User, task.assigned_to_user_id)
    product = db.get(Product, task.product_id) if task.product_id else None
    release = db.get(ProductRelease, task.product_release_id) if task.product_release_id else None
    completed_by = db.get(User, task.completed_by_user_id) if task.completed_by_user_id else None
    evidence = [TaskArtifactRead(
        id=link.id, revision_id=link.artifact_revision_id,
        artifact_id=link.artifact_revision.artifact_id,
        title=link.artifact_revision.artifact.title,
        filename=link.artifact_revision.original_filename,
        uploader_name=_user_display(link.artifact_revision.uploaded_by_user),
        revision_number=link.artifact_revision.revision_number,
        linked_at=link.created_at,
    ) for link in task.artifact_links]
    return TaskItem(
        entity_type="manual_task", entity_id=task.id, title=task.title, description=task.description,
        status=task.status, created_at=task.created_at, due_date=task.due_date,
        is_overdue=task.status != "completed" and task.archived_at is None and _is_overdue(task.due_date),
        product_name=product.name if product else None,
        release_version=_release_display(release), severity=None,
        created_by_name=_user_display(creator), assigned_to_user_id=task.assigned_to_user_id,
        assigned_to_name=_user_display(assignee), related_product_id=task.product_id,
        assigned_to_avatar_data=assignee.avatar_data if assignee else None,
        related_release_id=task.product_release_id,
        parent_task_id=task.parent_task_id,
        viewer_is_assignee=task.assigned_to_user_id == viewer_id,
        viewer_is_creator=task.created_by_user_id == viewer_id,
        is_completed=task.status == "completed",
        priority=task.priority, completed_at=task.completed_at,
        completed_by_name=_user_display(completed_by), completion_note=task.completion_note,
        archived_at=task.archived_at, archive_reason=task.archive_reason,
        can_edit_definition=task.created_by_user_id == viewer_id and task.archived_at is None,
        can_update_status=task.assigned_to_user_id == viewer_id and task.archived_at is None,
        can_archive=task.created_by_user_id == viewer_id,
        evidence=evidence,
    )


@router.post("/", response_model=TaskItem, status_code=status.HTTP_201_CREATED)
def create_manual_task(
    payload: ManualTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskItem:
    return _manual_task_item(ManualTaskService(db).create(payload, current_user), current_user.id, db)


@router.patch("/{task_id}/status", response_model=TaskItem)
def update_manual_task_status(
    task_id: UUID,
    payload: ManualTaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskItem:
    return _manual_task_item(ManualTaskService(db).set_status(task_id, payload.status, current_user), current_user.id, db)


@router.patch("/{task_id}", response_model=TaskItem)
def update_manual_task(
    task_id: UUID,
    payload: ManualTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskItem:
    return _manual_task_item(ManualTaskService(db).update(task_id, payload, current_user), current_user.id, db)


@router.post("/{task_id}/complete", response_model=TaskItem)
def complete_manual_task(task_id: UUID, payload: ManualTaskComplete, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TaskItem:
    return _manual_task_item(ManualTaskService(db).complete(task_id, payload.completion_note, current_user), current_user.id, db)


@router.post("/{task_id}/reopen", response_model=TaskItem)
def reopen_manual_task(task_id: UUID, payload: ManualTaskReason, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TaskItem:
    return _manual_task_item(ManualTaskService(db).reopen(task_id, payload.reason, current_user), current_user.id, db)


@router.post("/{task_id}/archive", response_model=TaskItem)
def archive_manual_task(task_id: UUID, payload: ManualTaskReason, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TaskItem:
    return _manual_task_item(ManualTaskService(db).archive(task_id, payload.reason, current_user), current_user.id, db)


@router.post("/{task_id}/restore", response_model=TaskItem)
def restore_manual_task(task_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TaskItem:
    return _manual_task_item(ManualTaskService(db).restore(task_id, current_user), current_user.id, db)


@router.get("/{task_id}/activity", response_model=list[TaskActivityRead])
def manual_task_activity(task_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[TaskActivityRead]:
    return ManualTaskService(db).activity(task_id, current_user)


@router.post("/{task_id}/artifacts/{revision_id}", response_model=TaskItem)
def attach_manual_task_artifact(task_id: UUID, revision_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TaskItem:
    return _manual_task_item(ManualTaskService(db).attach_artifact(task_id, revision_id, current_user), current_user.id, db)


@router.delete("/{task_id}/artifacts/{revision_id}", response_model=TaskItem)
def detach_manual_task_artifact(task_id: UUID, revision_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TaskItem:
    return _manual_task_item(ManualTaskService(db).detach_artifact(task_id, revision_id, current_user), current_user.id, db)


@router.get("/notifications/list", response_model=list[TaskNotificationRead])
def list_task_notifications(unread_only: bool = Query(default=False), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[TaskNotificationRead]:
    return ManualTaskService(db).notifications(current_user, unread_only)


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def read_task_notification(notification_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Response:
    ManualTaskService(db).mark_notification_read(notification_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/", response_model=list[TaskItem])
def list_my_tasks(
    include_completed: bool = Query(default=False),
    scope: str = Query(default="my_work"),
    state: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    product_release_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskItem]:
    tasks: list[TaskItem] = []
    today = date.today()  # noqa: F841 — kept for future date comparisons

    # ── Tasks created directly from the task page ───────────────────────────
    requested_state = state or ("all" if include_completed else "open")
    for manual_task in ManualTaskService(db).list(
        current_user, scope=scope, state=requested_state, priority=priority,
        product_id=product_id, product_release_id=product_release_id, search=search,
    ):
        tasks.append(_manual_task_item(manual_task, current_user.id, db))

    # Generated module work belongs only in the open My Work view.
    if scope == "assigned_by_me" or requested_state in {"completed", "archived"} or priority or product_id or product_release_id:
        tasks.sort(key=_sort_key)
        return tasks

    # ── Vulnerability reports ──────────────────────────────────────────────────
    vuln_stmt = (
        select(VulnerabilityReport)
        .where(
            VulnerabilityReport.assigned_to_user_id == current_user.id,
            VulnerabilityReport.status.notin_(list(_VULN_TERMINAL)),
        )
        .options(joinedload(VulnerabilityReport.product_release))
    )
    for vr in db.scalars(vuln_stmt).unique().all():
        release = vr.product_release
        product_name = getattr(getattr(release, "product", None), "name", None)
        # reporter_name is a free-text field for external reporters; use it as created_by
        created_by = vr.reporter_name or None
        tasks.append(TaskItem(
            entity_type="vulnerability_report",
            entity_id=vr.id,
            title=vr.title,
            status=vr.status,
            due_date=vr.due_date,
            is_overdue=_is_overdue(vr.due_date),
            product_name=product_name,
            release_version=getattr(release, "version", None),
            severity=vr.severity,
            created_by_name=created_by,
        ))

    # ── Changes ───────────────────────────────────────────────────────────────
    change_stmt = (
        select(Change)
        .where(
            Change.assigned_to_user_id == current_user.id,
            Change.status.notin_(list(_CHANGE_TERMINAL)),
        )
        .options(joinedload(Change.product_version))
    )
    changes = db.scalars(change_stmt).unique().all()

    # Resolve initiator names in one batch query.
    initiator_ids = {ch.initiator_user_id for ch in changes if ch.initiator_user_id}
    initiator_map: dict = {}
    if initiator_ids:
        user_repo = UserRepository(db)
        for uid in initiator_ids:
            u = user_repo.get_by_id(uid)
            if u:
                initiator_map[str(uid)] = _user_display(u)

    for ch in changes:
        release = ch.product_version
        product_name = getattr(getattr(release, "product", None), "name", None)
        tasks.append(TaskItem(
            entity_type="change",
            entity_id=ch.id,
            title=ch.title,
            status=ch.status,
            due_date=ch.due_date,
            is_overdue=_is_overdue(ch.due_date),
            product_name=product_name,
            release_version=getattr(release, "version", None),
            severity=None,
            created_by_name=initiator_map.get(str(ch.initiator_user_id)) if ch.initiator_user_id else None,
        ))

    # ── Substantial-change compliance actions ────────────────────────────────
    action_stmt = (
        select(ChangeComplianceAction)
        .where(
            ChangeComplianceAction.assigned_to_user_id == current_user.id,
            ChangeComplianceAction.action_status != ComplianceActionStatus.completed,
        )
        .options(
            joinedload(ChangeComplianceAction.assessment)
            .joinedload(SubstantialModificationAssessment.change)
            .joinedload(Change.product_version)
        )
    )
    for action in db.scalars(action_stmt).unique().all():
        change = action.assessment.change
        release = change.product_version
        product_name = getattr(getattr(release, "product", None), "name", None)
        tasks.append(TaskItem(
            entity_type="change_compliance_action",
            entity_id=action.id,
            title=action.action_type.value.replace("_", " ").title(),
            status=action.action_status,
            due_date=action.due_date,
            is_overdue=_is_overdue(action.due_date),
            product_name=product_name,
            release_version=getattr(release, "version", None),
            severity=None,
            parent_id=change.id,
            created_by_name=None,
        ))

    # ── Release gate items ────────────────────────────────────────────────────
    gate_stmt = (
        select(ReleaseGateItem)
        .where(
            ReleaseGateItem.assigned_to_user_id == current_user.id,
            ReleaseGateItem.status.notin_(list(_GATE_TERMINAL)),
        )
        .options(
            joinedload(ReleaseGateItem.release_gate).joinedload(ReleaseGate.product_release)
        )
    )
    for gi in db.scalars(gate_stmt).unique().all():
        release = getattr(getattr(gi, "release_gate", None), "product_release", None)
        product_name = getattr(getattr(release, "product", None), "name", None)
        tasks.append(TaskItem(
            entity_type="release_gate_item",
            entity_id=gi.id,
            title=gi.title,
            status=gi.status,
            due_date=gi.due_date,
            is_overdue=_is_overdue(gi.due_date),
            product_name=product_name,
            release_version=getattr(release, "version", None),
            severity=None,
            parent_id=getattr(release, "id", None),
            created_by_name=None,
        ))

    # ── Risk items ────────────────────────────────────────────────────────────
    risk_stmt = (
        select(RiskItem)
        .where(
            RiskItem.owner_user_id == current_user.id,
            RiskItem.status.notin_(list(_RISK_TERMINAL)),
        )
        .options(joinedload(RiskItem.risk_assessment))
    )
    for ri in db.scalars(risk_stmt).unique().all():
        assessment = ri.risk_assessment
        product_name = getattr(getattr(assessment, "product", None), "name", None)
        tasks.append(TaskItem(
            entity_type="risk_item",
            entity_id=ri.id,
            title=ri.title,
            status=ri.status,
            due_date=ri.due_date,
            is_overdue=_is_overdue(ri.due_date),
            product_name=product_name,
            release_version=None,
            severity=ri.risk_level,
            parent_id=getattr(assessment, "id", None),
            created_by_name=None,
        ))

    for assessment in db.scalars(select(SupplierAssessment).where(
        SupplierAssessment.owner_user_id == current_user.id,
        SupplierAssessment.reassessment_required.is_(True),
    )).all():
        tasks.append(TaskItem(entity_type="supplier_reassessment",entity_id=assessment.id,
            title=f"Reassess {assessment.title}",status="reassessment_required",due_date=assessment.reassessment_due_date,
            is_overdue=_is_overdue(assessment.reassessment_due_date),product_name=None,release_version=None,
            severity=assessment.assessment_tier,parent_id=assessment.id,created_by_name=None))

    for notification in db.scalars(select(ComponentMaintainerNotification).where(
        ComponentMaintainerNotification.assigned_to_user_id == current_user.id,
        ComponentMaintainerNotification.status.notin_(["acknowledged", "closed"]),
    )).all():
        tasks.append(TaskItem(entity_type="maintainer_notification",entity_id=notification.id,
            title="Notify component maintainer",status=notification.status,due_date=notification.due_date,
            is_overdue=_is_overdue(notification.due_date),product_name=None,release_version=None,severity=None,
            parent_id=notification.vulnerability_report_id,created_by_name=None))

    # ── EOS alerts (lifecycle notifications) ─────────────────────────────────
    # Surface pending end-of-support alerts where the current user is a recipient.
    eos_stmt = (
        select(LifecycleNotification)
        .where(
            LifecycleNotification.recipient_user_id == current_user.id,
            LifecycleNotification.notification_type == LifecycleNotificationType.end_of_support_upcoming,
            LifecycleNotification.status == LifecycleNotificationStatus.pending,
        )
        .options(
            joinedload(LifecycleNotification.support_period_record).joinedload(SupportPeriodRecord.product),
            joinedload(LifecycleNotification.support_period_record).joinedload(SupportPeriodRecord.product_release),
        )
    )
    for notif in db.scalars(eos_stmt).unique().all():
        sp = notif.support_period_record
        product_name = getattr(getattr(sp, "product", None), "name", None) if sp else None
        product_id = getattr(sp, "product_id", None) if sp else None
        release = getattr(sp, "product_release", None) if sp else None
        release_version = getattr(release, "version", None)
        support_end_date: date | None = getattr(sp, "support_end_date", None) if sp else None
        tasks.append(TaskItem(
            entity_type="eos_alert",
            entity_id=notif.id,
            title=notif.title,
            status=notif.status.value,
            due_date=support_end_date,
            is_overdue=_is_overdue(support_end_date),
            product_name=product_name,
            release_version=release_version,
            severity=None,
            # parent_id carries product_id so the frontend can deep-link to the product detail page.
            parent_id=product_id,
            created_by_name=None,
        ))

    tasks.sort(key=_sort_key)
    return tasks
