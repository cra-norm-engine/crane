"""
Service layer for Substantial Change Tracking.

Implements the full change lifecycle workflow:
  draft → submitted → under_review → assessed → action_required | closed

Business rules enforced here:
  - Only 'draft' changes can be edited
  - Workflow transitions are checked strictly (no skipping states)
  - Security-type changes can still be assessed but never auto-flagged as substantial
  - When is_substantial = True, four standard compliance actions are auto-created
  - Closing a change with outstanding (non-completed) compliance actions is blocked
"""

from __future__ import annotations

from datetime import date, datetime, UTC
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import AppException, NotFoundException
from app.models.change import Change, ChangeComplianceAction, SubstantialModificationAssessment
from app.models.enums import (
    AuditStatus,
    ChangeStatus,
    ChangeType,
    ComplianceActionStatus,
    ComplianceActionType,
    EntityType,
)
from app.repositories.change_repository import ChangeRepository
from app.repositories.product_release_repository import ProductReleaseRepository
from app.schemas.change import (
    AssessmentCreate,
    AssessmentRead,
    ChangeAssign,
    ChangeCreate,
    ChangeRead,
    ChangeSummary,
    ChangeUpdate,
    ComplianceActionRead,
    ComplianceActionUpdate,
)


# ---------------------------------------------------------------------------
# Compliance actions that are automatically created for substantial changes.
# These correspond to the CRA obligations triggered by a substantial modification.
# ---------------------------------------------------------------------------
_SUBSTANTIAL_ACTIONS = [
    ComplianceActionType.renew_conformity_assessment,
    ComplianceActionType.update_technical_docs,
    ComplianceActionType.update_declaration_of_conformity,
    ComplianceActionType.re_release_product,
]


def _today() -> date:
    """Return today's date in UTC."""
    return datetime.now(UTC).date()


class ChangeService:
    """
    Orchestrates all operations on Change records, including workflow
    transitions, assessments, and compliance action tracking.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ChangeRepository(db)
        # Used to verify a product version exists before creating a change
        self.release_repo = ProductReleaseRepository(db)

    # -----------------------------------------------------------------------
    # Read operations
    # -----------------------------------------------------------------------

    def list_changes(
        self,
        *,
        product_version_id: UUID | None = None,
        product_id: UUID | None = None,
        status: ChangeStatus | None = None,
        is_substantial: bool | None = None,
    ) -> list[ChangeSummary]:
        """
        Return a list of change summaries (no nested assessment detail).
        Supports filtering by product version, product, workflow status, and substantiality.
        product_id scopes results to a specific product (used by the release form
        dropdown so only same-product changes are offered for linking).
        """
        changes = self.repo.list_all(
            product_version_id=product_version_id,
            product_id=product_id,
            status=status,
            is_substantial=is_substantial,
        )
        return [self._to_summary(c) for c in changes]

    def get_change(self, change_id: UUID) -> ChangeRead:
        """Return full detail for a single change including its assessment."""
        change = self.repo.get_or_404(change_id)
        return self._to_read(change)

    # -----------------------------------------------------------------------
    # Workflow: create / edit
    # -----------------------------------------------------------------------

    def create_change(self, payload: ChangeCreate, *, actor: object) -> ChangeRead:
        """
        Create a new change in 'draft' status.
        Verifies the target product version exists before creating.
        """
        # Ensure the product version exists (raises 404 if not)
        self.release_repo.get_or_404(payload.product_version_id)

        change = Change(
            product_version_id=payload.product_version_id,
            initiator_user_id=getattr(actor, "id", None),
            change_type=payload.change_type,
            title=payload.title,
            description=payload.description,
            change_date=payload.change_date,
            status=ChangeStatus.draft,
        )
        self.db.add(change)
        self.db.flush()  # Get the generated ID before the audit event

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="create",
            entity_type=EntityType.change,
            entity_id=change.id,
            status=AuditStatus.success,
            details_json={"title": payload.title, "change_type": payload.change_type},
        )
        self.db.commit()
        self.db.refresh(change)
        return self._to_read(change)

    def update_change(
        self, change_id: UUID, payload: ChangeUpdate, *, actor: object
    ) -> ChangeRead:
        """
        Update an existing change. Only allowed while status is 'draft'.
        Attempting to edit a submitted/assessed change raises a 409.
        """
        change = self.repo.get_or_404(change_id)

        if change.status != ChangeStatus.draft:
            raise AppException(
                "Only draft changes can be edited. Submit the change to lock it.",
                status_code=409,
            )

        # Apply only the fields that were provided (partial update)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(change, field, value)

        # Serialize dates to ISO strings for the JSON audit payload
        audit_details = {
            k: v.isoformat() if isinstance(v, date) else v
            for k, v in payload.model_dump(exclude_unset=True).items()
        }

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="update",
            entity_type=EntityType.change,
            entity_id=change.id,
            status=AuditStatus.success,
            details_json=audit_details,
        )
        self.db.commit()
        self.db.refresh(change)
        return self._to_read(change)

    def assign_change(self, change_id: UUID, payload: ChangeAssign, *, actor: object) -> ChangeRead:
        """
        Update assignee and/or due date on a change regardless of its workflow status.
        Unlike update_change, this is not restricted to 'draft'.
        """
        change = self.repo.get_or_404(change_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(change, field, value)

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="update",
            entity_type=EntityType.change,
            entity_id=change.id,
            status=AuditStatus.success,
            details_json={"action": "assign", **{
                k: v.isoformat() if isinstance(v, date) else str(v) if v else None
                for k, v in payload.model_dump(exclude_unset=True).items()
            }},
        )
        self.db.commit()
        self.db.refresh(change)
        return self._to_read(change)

    # -----------------------------------------------------------------------
    # Workflow transitions
    # -----------------------------------------------------------------------

    def submit_change(self, change_id: UUID, *, actor: object) -> ChangeRead:
        """
        Transition: draft → submitted.
        Signals that the change is ready for assessment.
        """
        change = self.repo.get_or_404(change_id)
        self._require_status(change, ChangeStatus.draft, "submit")

        change.status = ChangeStatus.submitted
        change.submitted_at = _today()

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="update",
            entity_type=EntityType.change,
            entity_id=change.id,
            status=AuditStatus.success,
            details_json={"transition": "draft → submitted"},
        )
        self.db.commit()
        self.db.refresh(change)
        return self._to_read(change)

    def claim_change(self, change_id: UUID, *, actor: object) -> ChangeRead:
        """
        Transition: submitted → under_review.
        Assigns the calling user as assessor and marks the change as being reviewed.
        """
        change = self.repo.get_or_404(change_id)
        self._require_status(change, ChangeStatus.submitted, "claim")

        change.status = ChangeStatus.under_review
        change.assessor_user_id = getattr(actor, "id", None)

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="update",
            entity_type=EntityType.change,
            entity_id=change.id,
            status=AuditStatus.success,
            details_json={"transition": "submitted → under_review"},
        )
        self.db.commit()
        self.db.refresh(change)
        return self._to_read(change)

    def assess_change(
        self, change_id: UUID, payload: AssessmentCreate, *, actor: object
    ) -> ChangeRead:
        """
        Transition: under_review → assessed (or action_required if substantial).

        Steps:
          1. Validate the change is under review
          2. Derive is_substantial from the four criteria
          3. Create the assessment record
          4. If substantial, auto-create the four compliance action items
          5. Set change status to 'action_required' (substantial) or 'assessed'
        """
        change = self.repo.get_or_404(change_id)
        self._require_status(change, ChangeStatus.under_review, "assess")

        # A change already has an assessment if re-assess is attempted — reject it
        if self.repo.get_assessment(change_id) is not None:
            raise AppException("This change has already been assessed.", status_code=409)

        # Derive substantiality from the five Art. 3(30) / §103 criteria.
        # CRA Art. 3(4): Security-type changes are never substantial by definition.
        criteria_positive = (
            payload.alters_intended_use
            or payload.introduces_new_threat_vectors
            or payload.enables_new_attack_scenarios
            or payload.changes_attack_likelihood
            or payload.changes_attack_impact
        )
        is_substantial = criteria_positive and change.change_type != ChangeType.security

        # Create the assessment record
        assessment = SubstantialModificationAssessment(
            change_id=change_id,
            assessor_user_id=getattr(actor, "id", None),
            alters_intended_use=payload.alters_intended_use,
            introduces_new_threat_vectors=payload.introduces_new_threat_vectors,
            enables_new_attack_scenarios=payload.enables_new_attack_scenarios,
            changes_attack_likelihood=payload.changes_attack_likelihood,
            changes_attack_impact=payload.changes_attack_impact,
            is_substantial=is_substantial,
            reasoning=payload.reasoning,
            decision_date=payload.decision_date,
            methodology=payload.methodology,
            template_answers=payload.template_answers,
        )
        self.db.add(assessment)
        self.db.flush()  # Need assessment.id for compliance actions

        # Auto-create compliance actions when change is substantial
        if is_substantial:
            for action_type in _SUBSTANTIAL_ACTIONS:
                self.db.add(
                    ChangeComplianceAction(
                        assessment_id=assessment.id,
                        action_type=action_type,
                        action_status=ComplianceActionStatus.pending,
                    )
                )

        # Advance the change status
        change.status = (
            ChangeStatus.action_required if is_substantial else ChangeStatus.assessed
        )
        change.assessed_at = _today()
        change.assessor_user_id = getattr(actor, "id", None)

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="update",
            entity_type=EntityType.substantial_modification_assessment,
            entity_id=assessment.id,
            status=AuditStatus.success,
            details_json={
                "change_id": str(change_id),
                "is_substantial": is_substantial,
                "decision_date": str(payload.decision_date),
            },
        )
        self.db.commit()
        self.db.refresh(change)
        return self._to_read(change)

    def close_change(self, change_id: UUID, *, actor: object) -> ChangeRead:
        """
        Transition: assessed | action_required → closed.

        For substantial changes, all compliance actions must be completed
        before the change can be closed.
        """
        change = self.repo.get_or_404(change_id)

        if change.status not in (ChangeStatus.assessed, ChangeStatus.action_required):
            raise AppException(
                f"Cannot close a change that is in '{change.status}' status. "
                "It must be assessed first.",
                status_code=409,
            )

        # Block closure if any compliance action is still pending / in-progress
        if change.assessment and change.assessment.is_substantial:
            incomplete = [
                a for a in change.assessment.compliance_actions
                if a.action_status != ComplianceActionStatus.completed
            ]
            if incomplete:
                raise AppException(
                    f"Cannot close: {len(incomplete)} compliance action(s) are not yet completed.",
                    status_code=409,
                )

        change.status = ChangeStatus.closed
        change.closed_at = _today()

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="update",
            entity_type=EntityType.change,
            entity_id=change.id,
            status=AuditStatus.success,
            details_json={"transition": "→ closed"},
        )
        self.db.commit()
        self.db.refresh(change)
        return self._to_read(change)

    # -----------------------------------------------------------------------
    # Compliance actions
    # -----------------------------------------------------------------------

    def update_compliance_action(
        self,
        action_id: UUID,
        payload: ComplianceActionUpdate,
        *,
        actor: object,
    ) -> ComplianceActionRead:
        """
        Update the status, due date, or notes of a compliance action.
        When marking an action as 'completed', the completed_by user is recorded.
        """
        action = self.repo.get_compliance_action_or_404(action_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(action, field, value)

        # Record who completed it when status is set to 'completed'
        if payload.action_status == ComplianceActionStatus.completed:
            action.completed_by_user_id = getattr(actor, "id", None)

        # Convert date objects to ISO strings so json.dumps in the audit layer
        # can serialize the payload (Python's json encoder rejects date objects).
        audit_details = {
            k: v.isoformat() if isinstance(v, date) else v
            for k, v in payload.model_dump(exclude_unset=True).items()
        }

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="update",
            entity_type=EntityType.change_compliance_action,
            entity_id=action.id,
            status=AuditStatus.success,
            details_json=audit_details,
        )
        self.db.commit()
        self.db.refresh(action)
        return ComplianceActionRead.model_validate(action)

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _require_status(
        self, change: Change, required: ChangeStatus, action: str
    ) -> None:
        """Raise 409 if the change is not in the required status for a transition."""
        if change.status != required:
            raise AppException(
                f"Cannot {action}: change must be in '{required}' status "
                f"(currently '{change.status}').",
                status_code=409,
            )

    def _to_read(self, change: Change) -> ChangeRead:
        """Convert a Change ORM object to its full read schema."""
        assessment = None
        if change.assessment:
            assessment = AssessmentRead(
                id=change.assessment.id,
                created_at=change.assessment.created_at,
                updated_at=change.assessment.updated_at,
                change_id=change.assessment.change_id,
                assessor_user_id=change.assessment.assessor_user_id,
                alters_intended_use=change.assessment.alters_intended_use,
                introduces_new_threat_vectors=change.assessment.introduces_new_threat_vectors,
                enables_new_attack_scenarios=change.assessment.enables_new_attack_scenarios,
                changes_attack_likelihood=change.assessment.changes_attack_likelihood,
                changes_attack_impact=change.assessment.changes_attack_impact,
                is_substantial=change.assessment.is_substantial,
                reasoning=change.assessment.reasoning,
                decision_date=change.assessment.decision_date,
                compliance_actions=[
                    ComplianceActionRead.model_validate(a)
                    for a in change.assessment.compliance_actions
                ],
            )

        return ChangeRead(
            id=change.id,
            created_at=change.created_at,
            updated_at=change.updated_at,
            product_version_id=change.product_version_id,
            initiator_user_id=change.initiator_user_id,
            assessor_user_id=change.assessor_user_id,
            assigned_to_user_id=change.assigned_to_user_id,
            change_type=change.change_type,
            title=change.title,
            description=change.description,
            change_date=change.change_date,
            due_date=change.due_date,
            status=change.status,
            submitted_at=change.submitted_at,
            assessed_at=change.assessed_at,
            closed_at=change.closed_at,
            assessment=assessment,
        )

    def _to_summary(self, change: Change) -> ChangeSummary:
        """
        Convert a Change ORM object to its lightweight summary schema.
        Resolves product_name and release_version from the eagerly-loaded
        product_version relationship so the list UI shows human-readable names.
        """
        is_substantial = (
            change.assessment.is_substantial if change.assessment else None
        )
        assessment_id = change.assessment.id if change.assessment else None

        # Resolve human-readable identifiers from the eagerly-loaded relations.
        # product_version is loaded by _base_query; its .product is also loaded.
        release = change.product_version  # ProductRelease ORM object or None
        product_name = release.product.name if release and release.product else None
        release_version = f"v{release.system_version}" if release else None

        return ChangeSummary(
            id=change.id,
            created_at=change.created_at,
            updated_at=change.updated_at,
            product_version_id=change.product_version_id,
            initiator_user_id=change.initiator_user_id,
            assessor_user_id=change.assessor_user_id,
            change_type=change.change_type,
            title=change.title,
            change_date=change.change_date,
            status=change.status,
            is_substantial=is_substantial,
            assessment_id=assessment_id,
            product_name=product_name,
            release_version=release_version,
        )
