"""
Pydantic schemas for the Substantial Change Tracking feature.

Three groups of schemas:
  1. Change       — the change record and its workflow transitions
  2. Assessment   — the substantial modification assessment form
  3. ComplianceAction — individual compliance tasks for substantial changes

Each group has separate Create / Update / Read schemas following the project
conventions (Create = inbound data, Read = outbound data with timestamps).
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    ChangeStatus,
    ChangeType,
    ComplianceActionStatus,
    ComplianceActionType,
)
from app.schemas.common import TimestampedRead


# ---------------------------------------------------------------------------
# ComplianceAction schemas
# ---------------------------------------------------------------------------

class ComplianceActionRead(TimestampedRead):
    """
    Read schema for a single compliance action item.
    Returned as part of AssessmentRead when a change is substantial.
    """
    assessment_id: UUID
    action_type: ComplianceActionType
    action_status: ComplianceActionStatus
    due_date: date | None
    notes: str | None
    completed_by_user_id: UUID | None


class ComplianceActionUpdate(BaseModel):
    """
    Update schema for a compliance action.
    Only status, due date, and notes can be changed after creation.
    """
    action_status: ComplianceActionStatus | None = None
    due_date: date | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Assessment schemas
# ---------------------------------------------------------------------------

class AssessmentCreate(BaseModel):
    """
    Input schema for submitting a substantial modification assessment.

    The four boolean criteria (alters_intended_use, etc.) correspond directly
    to the CRA evaluation questions. If ANY is True the system sets
    is_substantial = True automatically.

    Note: for 'security'-type changes, all four criteria should remain False
    per CRA Article 3(4), but the form can still be submitted for audit purposes.
    """
    # The four CRA assessment criteria
    alters_intended_use: bool = False
    increases_cybersecurity_risk: bool = False
    changes_hazard_nature: bool = False
    expands_attack_surface: bool = False

    # Free-text justification for the decision — required
    reasoning: str = Field(min_length=10)

    # Date the decision was made
    decision_date: date


class AssessmentRead(TimestampedRead):
    """
    Read schema for an assessment, including the derived is_substantial flag
    and any compliance actions that were created.
    """
    change_id: UUID
    assessor_user_id: UUID | None

    # The four criteria
    alters_intended_use: bool
    increases_cybersecurity_risk: bool
    changes_hazard_nature: bool
    expands_attack_surface: bool

    # Derived outcome
    is_substantial: bool
    reasoning: str
    decision_date: date

    # Compliance actions (populated only when is_substantial = True)
    compliance_actions: list[ComplianceActionRead]


# ---------------------------------------------------------------------------
# Change schemas
# ---------------------------------------------------------------------------

class ChangeCreate(BaseModel):
    """
    Input schema for recording a new change (creates a draft).
    The initiator provides type, title, description, and the actual change date.
    """
    product_version_id: UUID
    change_type: ChangeType
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10)
    change_date: date


class ChangeUpdate(BaseModel):
    """
    Allows editing a change while it is still in 'draft' status.
    All fields are optional so the caller can patch only what changed.
    """
    change_type: ChangeType | None = None
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=10)
    change_date: date | None = None
    assigned_to_user_id: UUID | None = None
    due_date: date | None = None


class ChangeAssign(BaseModel):
    """Assignment-only patch — works regardless of change status."""
    assigned_to_user_id: UUID | None = None
    due_date: date | None = None


class ChangeRead(TimestampedRead):
    """
    Full read schema for a change, including nested assessment if present.
    """
    product_version_id: UUID
    initiator_user_id: UUID | None
    assessor_user_id: UUID | None
    assigned_to_user_id: UUID | None

    change_type: ChangeType
    title: str
    description: str
    change_date: date
    due_date: date | None

    # Workflow state
    status: ChangeStatus
    submitted_at: date | None
    assessed_at: date | None
    closed_at: date | None

    # Nested assessment (None if not yet assessed)
    assessment: AssessmentRead | None


class ChangeSummary(TimestampedRead):
    """
    Lightweight read schema used in list views — excludes the nested assessment
    to keep response payloads small.
    Includes resolved product_name and release_version so the list UI does not
    have to perform additional lookups to show human-readable identifiers.
    """
    product_version_id: UUID
    initiator_user_id: UUID | None
    assessor_user_id: UUID | None
    change_type: ChangeType
    title: str
    change_date: date
    status: ChangeStatus

    # Shortcut flag so the list view can highlight substantial changes
    # without having to join the assessment table client-side
    is_substantial: bool | None  # None when not yet assessed

    # Human-readable identifiers resolved from the linked product release
    product_name: str | None  # None only if the linked release is orphaned
    release_version: str | None  # None only if the linked release is orphaned
