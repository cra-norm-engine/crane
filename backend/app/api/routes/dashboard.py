from __future__ import annotations

# Dashboard route — GET /dashboard
# Returns a single DashboardRead payload aggregated from multiple tables.
# All queries are read-only; no writes occur in this route.

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, distinct, func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.audit_log_event import AuditLogEvent
from app.models.change import Change, SubstantialModificationAssessment
from app.models.enums import (
    ArtifactReviewDecision,
    ChangeStatus,
    LifecycleNotificationStatus,
    RiskAssessmentStatus,
    RiskItemStatus,
    SecurityUpdateSeverity,
    VulnerabilityLifecycleStatus,
)
from app.models.release_gate import ReleaseGate, ReleaseGateItem
from app.models.risk_item import RiskItem
from app.models.lifecycle_notification import LifecycleNotification
from app.models.product import Product, ProductRelease  # both defined in product.py
from app.models.risk_assessment import RiskAssessment
from app.models.support_period_record import SupportPeriodRecord
from app.models.user import User
from app.models.vulnerability_report import VulnerabilityReport
from app.schemas.dashboard import (
    ActivityItem,
    ChangeSummary,
    DashboardRead,
    LifecycleAlertSummary,
    ProductSummary,
    RiskAssessmentSummary,
    TaskSummary,
    UpcomingRelease,
    VulnSeverityBreakdown,
)

router = APIRouter()

# Only 'retired' is truly terminal for vulnerabilities — 'disclosed' still
# requires active CRA tracking (ENISA reporting, patch distribution, etc.).
_VULN_TERMINAL = {
    VulnerabilityLifecycleStatus.retired,
}



@router.get("", response_model=DashboardRead)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardRead:
    """
    Return a full dashboard summary for the authenticated user.

    Sections:
    - vulnerability_summary  — open vulns by severity + overdue
    - risk_summary           — open risk items by risk level
    - product_summary        — portfolio totals
    - task_summary           — items assigned to current_user
    - change_summary         — open changes and substantial mods
    - upcoming_releases      — releases planned in the next 90 days
    - recent_activity        — last 8 audit log events
    - compliance_score       — 0-100 weighted score
    """

    today = date.today()
    week_end = today + timedelta(days=7)

    # ──────────────────────────────────────────────────────────────────────────
    # VULNERABILITY SUMMARY
    # Count open (non-terminal) vulnerability reports grouped by severity.
    # ──────────────────────────────────────────────────────────────────────────
    terminal_statuses = [s.value for s in _VULN_TERMINAL]

    # Fetch severity + due_date for all open vulns in one pass.
    vuln_rows = db.execute(
        select(VulnerabilityReport.severity, VulnerabilityReport.due_date).where(
            VulnerabilityReport.status.notin_(terminal_statuses)
        )
    ).all()

    vuln_critical = vuln_high = vuln_medium = vuln_low = vuln_overdue = 0
    for row in vuln_rows:
        severity = row.severity
        if severity == SecurityUpdateSeverity.critical:
            vuln_critical += 1
        elif severity == SecurityUpdateSeverity.high:
            vuln_high += 1
        elif severity == SecurityUpdateSeverity.medium:
            vuln_medium += 1
        elif severity == SecurityUpdateSeverity.low:
            vuln_low += 1
        # Overdue: due_date is set and is strictly before today.
        if row.due_date is not None and row.due_date < today:
            vuln_overdue += 1

    vuln_total_open = len(vuln_rows)
    vulnerability_summary = VulnSeverityBreakdown(
        critical=vuln_critical,
        high=vuln_high,
        medium=vuln_medium,
        low=vuln_low,
        total_open=vuln_total_open,
        overdue=vuln_overdue,
    )

    # ──────────────────────────────────────────────────────────────────────────
    # RISK SUMMARY
    # Count risk assessments grouped by workflow status.
    # ──────────────────────────────────────────────────────────────────────────
    assessment_counts = db.execute(
        select(RiskAssessment.status, func.count().label("cnt"))
        .group_by(RiskAssessment.status)
    ).all()

    assessment_map: dict[str, int] = {row.status: row.cnt for row in assessment_counts}
    risk_summary = RiskAssessmentSummary(
        total=sum(assessment_map.values()),
        draft=assessment_map.get(RiskAssessmentStatus.draft, 0),
        in_review=assessment_map.get(RiskAssessmentStatus.in_review, 0),
        approved=assessment_map.get(RiskAssessmentStatus.approved, 0),
        archived=assessment_map.get(RiskAssessmentStatus.archived, 0),
    )

    # ──────────────────────────────────────────────────────────────────────────
    # PRODUCT SUMMARY
    # Total products, in_scope products, products with at least one 'released'
    # release (uses a correlated EXISTS subquery to avoid double-counting).
    # ──────────────────────────────────────────────────────────────────────────
    total_products: int = db.scalar(select(func.count()).select_from(Product)) or 0

    in_scope_products: int = (
        db.scalar(
            select(func.count()).select_from(Product).where(Product.scope_status == "in_scope")
        )
        or 0
    )

    # Count distinct products that have at least one 'released' release.
    released_products: int = (
        db.scalar(
            select(func.count(distinct(ProductRelease.product_id))).where(
                ProductRelease.release_status == "released"
            )
        )
        or 0
    )

    product_summary = ProductSummary(
        total=total_products,
        in_scope=in_scope_products,
        released=released_products,
    )

    # ──────────────────────────────────────────────────────────────────────────
    # TASK SUMMARY (current user only)
    # Matches the My Tasks page: aggregates open items across four entity types:
    #   • VulnerabilityReport  (assigned_to_user_id, status not terminal)
    #   • Change               (assigned_to_user_id, status != 'closed')
    #   • ReleaseGateItem      (assigned_to_user_id, status != 'accepted')
    #   • RiskItem             (owner_user_id, status not terminal)
    # ──────────────────────────────────────────────────────────────────────────
    task_due_dates: list[date | None] = []

    # Vulnerability tasks for this user.
    vuln_task_rows = db.execute(
        select(VulnerabilityReport.due_date).where(
            and_(
                VulnerabilityReport.assigned_to_user_id == current_user.id,
                VulnerabilityReport.status.notin_(terminal_statuses),
            )
        )
    ).scalars().all()
    task_due_dates.extend(vuln_task_rows)

    # Change tasks for this user.
    change_task_rows = db.execute(
        select(Change.due_date).where(
            and_(
                Change.assigned_to_user_id == current_user.id,
                Change.status != ChangeStatus.closed,
            )
        )
    ).scalars().all()
    task_due_dates.extend(change_task_rows)

    # Release gate items assigned to this user (not yet accepted).
    gate_task_rows = db.execute(
        select(ReleaseGateItem.due_date).where(
            and_(
                ReleaseGateItem.assigned_to_user_id == current_user.id,
                ReleaseGateItem.status != ArtifactReviewDecision.accepted,
            )
        )
    ).scalars().all()
    task_due_dates.extend(gate_task_rows)

    # Risk items owned by this user (not mitigated, accepted, or closed).
    risk_terminal = (RiskItemStatus.mitigated, RiskItemStatus.accepted, RiskItemStatus.closed)
    risk_task_rows = db.execute(
        select(RiskItem.due_date).where(
            and_(
                RiskItem.owner_user_id == current_user.id,
                RiskItem.status.notin_(list(risk_terminal)),
            )
        )
    ).scalars().all()
    task_due_dates.extend(risk_task_rows)

    task_total_open = len(task_due_dates)
    task_overdue = 0
    task_due_this_week = 0
    for dd in task_due_dates:
        if dd is None:
            continue
        if dd < today:
            task_overdue += 1
        elif today <= dd <= week_end:
            task_due_this_week += 1

    task_summary = TaskSummary(
        total_open=task_total_open,
        overdue=task_overdue,
        due_this_week=task_due_this_week,
    )

    # ──────────────────────────────────────────────────────────────────────────
    # CHANGE SUMMARY
    # Open changes (status != 'closed'), action_required count, and open
    # substantial modification changes.
    # ──────────────────────────────────────────────────────────────────────────
    change_status_counts = db.execute(
        select(Change.status, func.count().label("cnt"))
        .where(Change.status != ChangeStatus.closed)
        .group_by(Change.status)
    ).all()

    change_total_open = sum(row.cnt for row in change_status_counts)
    change_action_required = sum(
        row.cnt for row in change_status_counts if row.status == ChangeStatus.action_required
    )

    # Substantial open: changes whose assessment has is_substantial=True and the
    # change itself is still open (not closed).
    substantial_open: int = (
        db.scalar(
            select(func.count())
            .select_from(Change)
            .join(SubstantialModificationAssessment, SubstantialModificationAssessment.change_id == Change.id)
            .where(
                and_(
                    SubstantialModificationAssessment.is_substantial.is_(True),
                    Change.status != ChangeStatus.closed,
                )
            )
        )
        or 0
    )

    change_summary = ChangeSummary(
        total_open=change_total_open,
        action_required=change_action_required,
        substantial_open=substantial_open,
    )

    # ──────────────────────────────────────────────────────────────────────────
    # UPCOMING RELEASES
    # ProductReleases with planned_release_date in the next 90 days, not yet
    # released or cancelled.  Limit 5, ordered by planned date ascending.
    # ──────────────────────────────────────────────────────────────────────────
    horizon = today + timedelta(days=90)
    # Statuses that mean "already done" and should be excluded.
    excluded_release_statuses = ("released", "withdrawn")

    upcoming_stmt = (
        select(ProductRelease)
        .where(
            and_(
                ProductRelease.planned_release_date.isnot(None),
                func.date(ProductRelease.planned_release_date) >= today,
                func.date(ProductRelease.planned_release_date) <= horizon,
                ProductRelease.release_status.notin_(excluded_release_statuses),
            )
        )
        .options(joinedload(ProductRelease.product))
        .order_by(ProductRelease.planned_release_date.asc())
        .limit(5)
    )
    upcoming_release_rows = db.execute(upcoming_stmt).unique().scalars().all()

    upcoming_releases: list[UpcomingRelease] = []
    for rel in upcoming_release_rows:
        # planned_release_date is stored as datetime; extract date portion.
        planned_dt = rel.planned_release_date
        planned_date_only: date | None = planned_dt.date() if planned_dt is not None else None
        days_until: int | None = (
            (planned_date_only - today).days if planned_date_only is not None else None
        )
        product_name: str | None = rel.product.name if rel.product is not None else None

        upcoming_releases.append(
            UpcomingRelease(
                id=rel.id,
                product_name=product_name,
                version=f"v{rel.system_version}" if rel.system_version else "unknown",
                planned_date=planned_date_only,
                days_until=days_until,
                release_status=rel.release_status,
            )
        )

    # ──────────────────────────────────────────────────────────────────────────
    # RECENT ACTIVITY
    # Last 8 audit log events, newest first.  Actor email is loaded via a
    # separate scalar query to avoid a JOIN on a potentially large users table.
    # AuditLogEvent uses occurred_at (not created_at) and actor_user_id.
    # ──────────────────────────────────────────────────────────────────────────
    audit_stmt = (
        select(AuditLogEvent)
        .order_by(AuditLogEvent.occurred_at.desc())
        .limit(8)
    )
    audit_events = db.execute(audit_stmt).scalars().all()

    # Batch-fetch actor emails for the returned event set.
    actor_ids = {ev.actor_user_id for ev in audit_events if ev.actor_user_id is not None}
    actor_email_map: dict = {}
    if actor_ids:
        user_rows = db.execute(
            select(User.id, User.email).where(User.id.in_(actor_ids))
        ).all()
        actor_email_map = {row.id: row.email for row in user_rows}

    recent_activity: list[ActivityItem] = []
    for ev in audit_events:
        actor_email = actor_email_map.get(ev.actor_user_id) if ev.actor_user_id else None
        summary = f"{ev.action_type} on {ev.entity_type}"
        recent_activity.append(
            ActivityItem(
                id=ev.id,
                action_type=ev.action_type,
                entity_type=ev.entity_type,
                actor_email=actor_email,
                created_at=ev.occurred_at,  # schema field named created_at; source field is occurred_at
                summary=summary,
            )
        )

    # ──────────────────────────────────────────────────────────────────────────
    # LIFECYCLE ALERT SUMMARY
    # Active support periods by health: expired, expiring soon, healthy.
    # Also counts unacknowledged (pending) lifecycle notifications.
    # ──────────────────────────────────────────────────────────────────────────
    horizon_90  = today + timedelta(days=90)
    horizon_180 = today + timedelta(days=180)

    lifecycle_rows = db.execute(
        select(SupportPeriodRecord.support_end_date)
        .where(SupportPeriodRecord.is_active == True)  # noqa: E712
    ).scalars().all()

    lc_total    = len(lifecycle_rows)
    lc_expired  = sum(1 for d in lifecycle_rows if d < today)
    lc_exp_90   = sum(1 for d in lifecycle_rows if today <= d <= horizon_90)
    lc_exp_180  = sum(1 for d in lifecycle_rows if today <= d <= horizon_180)

    pending_alerts: int = (
        db.scalar(
            select(func.count()).select_from(LifecycleNotification)
            .where(LifecycleNotification.status == LifecycleNotificationStatus.pending)
        )
        or 0
    )

    lifecycle_summary = LifecycleAlertSummary(
        total_active=lc_total,
        expired=lc_expired,
        expiring_90d=lc_exp_90,
        expiring_180d=lc_exp_180,
        pending_alerts=pending_alerts,
    )

    # ──────────────────────────────────────────────────────────────────────────
    # COMPLIANCE SCORE
    # Weighted formula using scope coverage, open critical/high vulns and risks.
    # ──────────────────────────────────────────────────────────────────────────
    scope_factor = (in_scope_products / max(total_products, 1)) * 100
    vuln_factor = 100 - min((vuln_critical * 25 + vuln_high * 10), 100)
    # Penalise for assessments that are not yet approved (draft/in_review count as open).
    unapproved = assessment_map.get(RiskAssessmentStatus.draft, 0) + assessment_map.get(RiskAssessmentStatus.in_review, 0)
    risk_factor = 100 - min(unapproved * 15, 100)
    raw_score = scope_factor * 0.3 + vuln_factor * 0.4 + risk_factor * 0.3
    compliance_score = max(0, min(100, int(raw_score)))

    return DashboardRead(
        vulnerability_summary=vulnerability_summary,
        risk_summary=risk_summary,
        product_summary=product_summary,
        task_summary=task_summary,
        change_summary=change_summary,
        lifecycle_summary=lifecycle_summary,
        upcoming_releases=upcoming_releases,
        recent_activity=recent_activity,
        compliance_score=compliance_score,
    )
