from __future__ import annotations

# Dashboard response schemas for the GET /dashboard endpoint.
# Each nested schema maps to a section of the dashboard summary card.

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class VulnSeverityBreakdown(BaseModel):
    """Open vulnerability counts grouped by severity, plus overdue count."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    total_open: int = 0
    overdue: int = 0


class RiskAssessmentSummary(BaseModel):
    """Risk assessment counts grouped by workflow status."""

    total: int = 0
    draft: int = 0
    in_review: int = 0
    approved: int = 0
    archived: int = 0


class ProductSummary(BaseModel):
    """High-level product portfolio counts."""

    total: int = 0
    in_scope: int = 0
    released: int = 0  # products with at least one 'released' release


class TaskSummary(BaseModel):
    """Open tasks assigned to the requesting user across all entity types."""

    total_open: int = 0
    overdue: int = 0
    due_this_week: int = 0


class ChangeSummary(BaseModel):
    """Open change record counts including substantial modifications."""

    total_open: int = 0
    action_required: int = 0
    substantial_open: int = 0  # changes with is_substantial=True, not yet closed


class UpcomingRelease(BaseModel):
    """A product release planned within the next 90 days."""

    id: UUID
    product_name: str | None
    version: str
    planned_date: date | None
    days_until: int | None
    release_status: str


class ActivityItem(BaseModel):
    """A single recent audit log event rendered as a human-readable summary."""

    id: UUID
    action_type: str
    entity_type: str | None
    actor_email: str | None
    created_at: datetime  # mapped from AuditLogEvent.occurred_at
    summary: str          # e.g. "create on risk_assessment"


class LifecycleAlertSummary(BaseModel):
    """Support-period lifecycle health across the product portfolio."""

    total_active: int = 0      # active support period records
    expired: int = 0           # products past their end-of-support date
    expiring_90d: int = 0      # ending within 90 days (not yet expired)
    expiring_180d: int = 0     # ending within 180 days (includes 90d subset)
    pending_alerts: int = 0    # unacknowledged lifecycle notifications


class DashboardRead(BaseModel):
    """Top-level dashboard response containing all summary sections."""

    vulnerability_summary: VulnSeverityBreakdown
    risk_summary: RiskAssessmentSummary
    product_summary: ProductSummary
    task_summary: TaskSummary
    change_summary: ChangeSummary
    lifecycle_summary: LifecycleAlertSummary
    upcoming_releases: list[UpcomingRelease]
    recent_activity: list[ActivityItem]
    compliance_score: int  # weighted 0-100 score
