from uuid import UUID

from fastapi import APIRouter, Depends, Response
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.audit import create_audit_event
from app.core.database import get_db
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.permissions import Permission
from app.models.dependency_track import DependencyTrackConnection
from app.models.product import Product, ProductRelease
from app.models.sbom_record import SbomRecord
from app.models.user import User
from app.schemas.dependency_track import ConnectionCreate, ConnectionCredentials, ConnectionRead, ConnectionUpdate, ProjectOption, SbomOption
from app.services.dependency_track_service import credential_cipher, get_connection, get_json, list_projects, sync_connection

router = APIRouter(prefix="/admin/dependency-track", tags=["dependency-track"])
admin = require_permissions_dependency(Permission.admin_manage_users)


@router.post("/test", response_model=list[ProjectOption])
def test_connection(payload: ConnectionCredentials, user: User = Depends(admin)):
    return list_projects(payload.server_url, payload.api_key.get_secret_value())


@router.get("/sboms", response_model=list[SbomOption])
def sbom_options(db: Session = Depends(get_db), user: User = Depends(admin)):
    rows = db.execute(select(SbomRecord.id, SbomRecord.file_name, SbomRecord.created_at, Product.name, ProductRelease.user_version, ProductRelease.system_version)
                      .join(ProductRelease, SbomRecord.product_release_id == ProductRelease.id)
                      .join(Product, ProductRelease.product_id == Product.id).order_by(Product.name, ProductRelease.system_version.desc(), SbomRecord.created_at.desc()))
    return [SbomOption(id=row.id, label=f"{row.name} · {row.user_version or 'v' + str(row.system_version)} · {row.file_name or 'SBOM'} · {row.created_at:%Y-%m-%d %H:%M}") for row in rows]


@router.get("", response_model=list[ConnectionRead])
def connections(db: Session = Depends(get_db), user: User = Depends(admin)):
    return db.scalars(select(DependencyTrackConnection).order_by(DependencyTrackConnection.created_at.desc())).all()


@router.post("", response_model=ConnectionRead, status_code=201)
def connect(payload: ConnectionCreate, db: Session = Depends(get_db), user: User = Depends(admin)):
    if db.get(SbomRecord, payload.sbom_record_id) is None:
        raise NotFoundException("Upload an SBOM to the intended CRANE release first")
    data = get_json(payload.server_url, payload.api_key.get_secret_value(), f"/api/v1/project/{payload.project_id}")
    try:
        project = ProjectOption.model_validate(data)
    except ValidationError as exc:
        raise ValidationException("Dependency-Track did not return the selected project") from exc
    if project.uuid != payload.project_id:
        raise ValidationException("Dependency-Track returned a different project")
    # Confirm finding access as well as project visibility before persisting a key.
    findings = get_json(payload.server_url, payload.api_key.get_secret_value(), f"/api/v1/finding/project/{project.uuid}", {"suppressed": "true"})
    if not isinstance(findings, list):
        raise ValidationException("Dependency-Track did not return findings for this project")
    item = DependencyTrackConnection(
        server_url=payload.server_url, api_key_encrypted=credential_cipher().encrypt(payload.api_key.get_secret_value().encode()).decode(),
        project_id=project.uuid, project_name=f"{project.name}{' · ' + project.version if project.version else ''}"[:500],
        sbom_record_id=payload.sbom_record_id, created_by_user_id=user.id, automatic_sync=payload.automatic_sync,
    )
    try:
        with db.begin_nested():
            db.add(item)
            db.flush()
    except IntegrityError as exc:
        raise ConflictException("This Dependency-Track project is already connected to the selected SBOM") from exc
    create_audit_event(db, actor_user_id=user.id, action_type="dependency_track.connected", entity_type="dependency_track_connection", entity_id=item.id, status="success",
                      details_json={"server_url": item.server_url, "project_id": str(item.project_id), "sbom_record_id": str(item.sbom_record_id)})
    db.commit()
    return item


@router.post("/{connection_id}/sync", response_model=ConnectionRead)
def sync(connection_id: UUID, db: Session = Depends(get_db), user: User = Depends(admin)):
    return sync_connection(db, connection_id)


@router.patch("/{connection_id}", response_model=ConnectionRead)
def configure(connection_id: UUID, payload: ConnectionUpdate, db: Session = Depends(get_db), user: User = Depends(admin)):
    item = get_connection(db, connection_id)
    item.automatic_sync = payload.automatic_sync
    create_audit_event(db, actor_user_id=user.id, action_type="dependency_track.updated", entity_type="dependency_track_connection", entity_id=item.id, status="success", details_json=payload.model_dump())
    db.commit()
    return item


@router.delete("/{connection_id}", status_code=204)
def disconnect(connection_id: UUID, db: Session = Depends(get_db), user: User = Depends(admin)):
    item = get_connection(db, connection_id)
    create_audit_event(db, actor_user_id=user.id, action_type="dependency_track.disconnected", entity_type="dependency_track_connection", entity_id=item.id, status="success")
    db.delete(item)
    db.commit()
    return Response(status_code=204)
