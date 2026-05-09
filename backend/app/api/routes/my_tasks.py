"""
My Tasks endpoint — aggregates open items assigned to the current user
across all entity types that support task assignment:

  • vulnerability_reports  (assigned_to_user_id)
  • changes                (assigned_to_user_id)
  • release_gate_items     (assigned_to_user_id)
  • risk_items             (owner_user_id)

Results are sorted: overdue first, then by due_date ascending, then no-date items last.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.change import Change
from app.models.enums import (
    ArtifactReviewDecision,
    ChangeStatus,
    RiskItemStatus,
    VulnerabilityLifecycleStatus,
)
from app.models.release_gate import ReleaseGate, ReleaseGateItem
from app.models.risk_item import RiskItem
from app.models.user import User
from app.models.vulnerability_report import VulnerabilityReport
from app.schemas.my_tasks import TaskItem
from app.repositories.user_repository import UserRepository

router = APIRouter()

# Terminal statuses excluded from My Tasks — records in these states are done.
_VULN_TERMINAL = {VulnerabilityLifecycleStatus.disclosed, VulnerabilityLifecycleStatus.retired}
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


@router.get("/", response_model=list[TaskItem])
def list_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskItem]:
    tasks: list[TaskItem] = []
    today = date.today()  # noqa: F841 — kept for future date comparisons

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

    tasks.sort(key=_sort_key)
    return tasks
