from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.audit import AuditEventListRead, AuditIntegrityRead
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", response_model=AuditEventListRead)
def list_audit_events(
    entity_id: UUID | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    product_release_id: UUID | None = Query(default=None),
    actor_user_id: UUID | None = Query(default=None),
    action_type: str | None = Query(default=None, max_length=120),
    action_prefix: str | None = Query(default=None, max_length=120),
    entity_type: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.audit_read)),
) -> AuditEventListRead:
    return AuditService(db).list_events(
        entity_id=entity_id,
        product_id=product_id,
        product_release_id=product_release_id,
        actor_user_id=actor_user_id,
        action_type=action_type,
        action_prefix=action_prefix,
        entity_type=entity_type,
        limit=limit,
    )


@router.get("/integrity", response_model=AuditIntegrityRead)
def verify_audit_integrity(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.audit_read)),
) -> AuditIntegrityRead:
    return AuditService(db).verify_integrity()
