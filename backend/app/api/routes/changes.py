"""
API routes for Substantial Change Tracking.

Endpoints are grouped into three areas:
  1. Change CRUD + workflow transitions (submit, claim, assess, close)
  2. Global change list (with filters)
  3. Compliance action updates

Permission requirements:
  - change_read  → GET endpoints
  - change_write → POST / PATCH / PUT endpoints
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.enums import ChangeStatus, ChangeType
from app.models.user import User
from app.schemas.change import (
    AssessmentCreate,
    ChangeAssign,
    ChangeCreate,
    ChangeRead,
    ChangeSummary,
    ChangeUpdate,
    ComplianceActionRead,
    ComplianceActionUpdate,
)
from app.services.assessment_template_service import (
    get_questions,
    recommend_actions,
)
from app.services.change_service import ChangeService

router = APIRouter()


# ---------------------------------------------------------------------------
# Change collection and creation
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[ChangeSummary],
    summary="List all changes",
    description=(
        "Returns a pageable list of change summaries. "
        "Filter by product_version_id, status, change_type, or is_substantial."
    ),
)
def list_changes(
    product_version_id: UUID | None = None,
    product_id: UUID | None = None,  # Scope to a specific product (used by release form dropdown)
    status: ChangeStatus | None = None,
    change_type: ChangeType | None = None,
    is_substantial: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_read)),
):
    return ChangeService(db).list_changes(
        product_version_id=product_version_id,
        product_id=product_id,
        status=status,
        is_substantial=is_substantial,
    )


@router.post(
    "",
    response_model=ChangeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new change (draft)",
    description="Records a new change against a product version. Status starts as 'draft'.",
)
def create_change(
    payload: ChangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_write)),
):
    return ChangeService(db).create_change(payload, actor=current_user)


# ---------------------------------------------------------------------------
# Single change detail and editing
# ---------------------------------------------------------------------------

@router.get(
    "/{change_id}",
    response_model=ChangeRead,
    summary="Get change detail",
    description="Returns full detail for a change including its assessment and compliance actions.",
)
def get_change(
    change_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_read)),
):
    return ChangeService(db).get_change(change_id)


@router.patch(
    "/{change_id}",
    response_model=ChangeRead,
    summary="Update a change (draft only)",
    description="Update change fields. Only allowed while the change is in 'draft' status.",
)
def update_change(
    change_id: UUID,
    payload: ChangeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_write)),
):
    return ChangeService(db).update_change(change_id, payload, actor=current_user)


@router.patch(
    "/{change_id}/assign",
    response_model=ChangeRead,
    summary="Assign / set due date on a change",
    description=(
        "Update assigned_to_user_id and/or due_date on a change. "
        "Unlike the general update endpoint, this works regardless of workflow status."
    ),
)
def assign_change(
    change_id: UUID,
    payload: ChangeAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_write)),
):
    return ChangeService(db).assign_change(change_id, payload, actor=current_user)


# ---------------------------------------------------------------------------
# Workflow transition endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{change_id}/submit",
    response_model=ChangeRead,
    summary="Submit change for assessment",
    description="Transitions the change from 'draft' to 'submitted'. Notifies assessors.",
)
def submit_change(
    change_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_write)),
):
    return ChangeService(db).submit_change(change_id, actor=current_user)


@router.post(
    "/{change_id}/claim",
    response_model=ChangeRead,
    summary="Claim change for review",
    description=(
        "Transitions from 'submitted' to 'under_review' and assigns "
        "the calling user as assessor."
    ),
)
def claim_change(
    change_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_write)),
):
    return ChangeService(db).claim_change(change_id, actor=current_user)


@router.post(
    "/{change_id}/assess",
    response_model=ChangeRead,
    summary="Submit substantial modification assessment",
    description=(
        "Records the four CRA evaluation criteria and derives whether the change "
        "is substantial. If substantial, compliance actions are auto-created and "
        "the change moves to 'action_required'. Otherwise it moves to 'assessed'."
    ),
)
def assess_change(
    change_id: UUID,
    payload: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_write)),
):
    return ChangeService(db).assess_change(change_id, payload, actor=current_user)


@router.post(
    "/{change_id}/close",
    response_model=ChangeRead,
    summary="Close a change",
    description=(
        "Transitions the change to 'closed'. "
        "For substantial changes all compliance actions must be completed first."
    ),
)
def close_change(
    change_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_write)),
):
    return ChangeService(db).close_change(change_id, actor=current_user)


# ---------------------------------------------------------------------------
# Compliance action management
# ---------------------------------------------------------------------------

@router.patch(
    "/compliance-actions/{action_id}",
    response_model=ComplianceActionRead,
    summary="Update a compliance action",
    description=(
        "Update the status, due date, or notes of a compliance action. "
        "Setting status to 'completed' records the completing user."
    ),
)
def update_compliance_action(
    action_id: UUID,
    payload: ComplianceActionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_write)),
):
    return ChangeService(db).update_compliance_action(
        action_id, payload, actor=current_user
    )


# ---------------------------------------------------------------------------
# Assessment templates
# ---------------------------------------------------------------------------


@router.get(
    "/assessment-templates/{methodology}",
    summary="Get assessment questions for a methodology",
    description=(
        "Returns the structured questions for STRIDE (6 questions) or TARA (4 questions) "
        "assessment methodologies. Each question maps to one of the four CRA Art. 3(3)(c) criteria."
    ),
)
def get_assessment_template(
    methodology: str,
):
    """Get assessment questions for the specified methodology."""
    questions = get_questions(methodology.lower())
    if not questions:
        return Response(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="Invalid methodology. Use 'stride' or 'tara'.",
        )

    return {
        "methodology": methodology.lower(),
        "questions": [q.to_dict() for q in questions],
    }


@router.get(
    "/{change_id}/recommended-actions",
    summary="Get recommended compliance actions for a change",
    description=(
        "Returns a list of recommended actions based on the change type and assessment outcome. "
        "Note: CRA Art. 3(4) — security-type changes are never substantial and receive "
        "simplified recommendations."
    ),
)
def get_recommended_actions(
    change_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.change_read)),
):
    """Get recommended compliance actions for the change."""
    service = ChangeService(db)
    change = service.repo.get_or_404(change_id)
    assessment = service.repo.get_assessment(change_id)

    is_substantial = assessment.is_substantial if assessment else False
    actions = recommend_actions(is_substantial, change.change_type)

    return {
        "change_id": str(change_id),
        "change_type": change.change_type,
        "is_assessed": assessment is not None,
        "is_substantial": is_substantial,
        "recommended_actions": actions,
    }
