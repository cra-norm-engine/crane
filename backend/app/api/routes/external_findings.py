from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permissions_dependency, security_scheme
from app.core.audit import create_audit_event
from app.core.database import get_db
from app.core.permissions import Permission, require_permissions
from app.models.base import utc_now
from app.models.ingestion_key import IngestionKey
from app.models.sbom_record import SbomRecord
from app.models.user import User
from app.schemas.external_finding import (
    ExternalFindingsImport, ImportResult, IngestionKeyCreate, IngestionKeyIssued, IngestionKeyRead,
)
from app.services.external_finding_service import import_external_findings

router = APIRouter(tags=["external-findings"])
admin = require_permissions_dependency(Permission.admin_manage_users)
ingestion_key_scheme = APIKeyHeader(name="X-CRANE-Ingestion-Key", auto_error=False)


def key_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/admin/ingestion-keys", response_model=IngestionKeyIssued, status_code=201)
def issue_key(payload: IngestionKeyCreate, response: Response, db: Session = Depends(get_db), user: User = Depends(admin)):
    if db.get(SbomRecord, payload.sbom_record_id) is None:
        raise HTTPException(404, "SBOM not found")
    token = "crane_ingest_" + secrets.token_urlsafe(32)
    key = IngestionKey(
        name=payload.name, sbom_record_id=payload.sbom_record_id, source=payload.source,
        token_hash=key_hash(token), created_by_user_id=user.id,
        expires_at=utc_now() + timedelta(days=payload.expires_in_days),
    )
    db.add(key)
    db.flush()
    create_audit_event(db, actor_user_id=user.id, action_type="ingestion_key.created",
                      entity_type="ingestion_key", entity_id=key.id, status="success",
                      details_json={"source": key.source, "sbom_record_id": str(key.sbom_record_id)})
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return IngestionKeyIssued(**IngestionKeyRead.model_validate(key).model_dump(), token=token)


@router.get("/admin/ingestion-keys", response_model=list[IngestionKeyRead])
def list_keys(db: Session = Depends(get_db), user: User = Depends(admin)):
    return db.scalars(select(IngestionKey).order_by(IngestionKey.created_at.desc())).all()


@router.delete("/admin/ingestion-keys/{key_id}", status_code=204)
def revoke_key(key_id: UUID, db: Session = Depends(get_db), user: User = Depends(admin)):
    key = db.get(IngestionKey, key_id)
    if key is None:
        raise HTTPException(404, "Ingestion key not found")
    if key.revoked_at is None:
        key.revoked_at = utc_now()
        create_audit_event(db, actor_user_id=user.id, action_type="ingestion_key.revoked",
                          entity_type="ingestion_key", entity_id=key.id, status="success")
        db.commit()
    return Response(status_code=204)


def ingestion_identity(
    token: str | None = Depends(ingestion_key_scheme),
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User | IngestionKey:
    # Dedicated scheme: these keys cannot authenticate to any other CRANE endpoint.
    if token is None:
        user = get_current_user(credentials, db)
        require_permissions(user, {Permission.vulnerability_report_write, Permission.security_update_write})
        return user
    if len(token) > 200:
        raise HTTPException(401, "Invalid ingestion key")
    key = db.scalar(select(IngestionKey).where(IngestionKey.token_hash == key_hash(token)))
    if key is None or key.revoked_at is not None or key.expires_at <= utc_now():
        raise HTTPException(401, "Invalid or expired ingestion key")
    owner = db.get(User, key.created_by_user_id)
    if owner is None or not owner.is_active or owner.must_change_password:
        raise HTTPException(401, "Ingestion key owner is inactive")
    require_permissions(owner, {Permission.admin_manage_users})
    return key


@router.put("/sbom-records/{sbom_id}/external-vulnerability-findings", response_model=ImportResult)
def ingest(sbom_id: UUID, payload: ExternalFindingsImport, db: Session = Depends(get_db), identity=Depends(ingestion_identity)):
    if isinstance(identity, IngestionKey):
        if identity.sbom_record_id != sbom_id or identity.source != payload.source:
            raise HTTPException(403, "Ingestion key is not authorized for this SBOM/source")
        actor_id = identity.created_by_user_id
    else:
        actor_id = identity.id
    return import_external_findings(db, sbom_id, payload, actor_user_id=actor_id)
