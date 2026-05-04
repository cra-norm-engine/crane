from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.cvd_policy import CvdPolicyCreate, CvdPolicyRead, CvdPolicyUpdate
from app.services.cvd_policy_service import CvdPolicyService

router = APIRouter()


@router.get("/", response_model=list[CvdPolicyRead])
def list_cvd_policies(
    product_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> list[CvdPolicyRead]:
    return CvdPolicyService(db).list_cvd_policies(product_id=product_id)


@router.post("/", response_model=CvdPolicyRead, status_code=status.HTTP_201_CREATED)
def create_cvd_policy(
    payload: CvdPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> CvdPolicyRead:
    return CvdPolicyService(db).create_cvd_policy(payload, actor=current_user)


@router.get("/{policy_id}", response_model=CvdPolicyRead)
def get_cvd_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> CvdPolicyRead:
    return CvdPolicyService(db).get_cvd_policy(policy_id)


@router.put("/{policy_id}", response_model=CvdPolicyRead)
def update_cvd_policy(
    policy_id: UUID,
    payload: CvdPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> CvdPolicyRead:
    return CvdPolicyService(db).update_cvd_policy(policy_id, payload, actor=current_user)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_cvd_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> Response:
    CvdPolicyService(db).delete_cvd_policy(policy_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
