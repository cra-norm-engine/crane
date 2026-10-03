from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions import Permission, require_permissions
from app.models.user import User
from app.schemas.annex_requirement import AnnexRequirementCreate, AnnexRequirementRead
from app.schemas.requirement_source import RequirementSourceCreate, RequirementSourcePublish, RequirementSourceRead, RequirementSourceUpdate
from app.services.annex_requirement_service import AnnexRequirementService
from app.services.requirement_source_service import RequirementSourceService

router = APIRouter()


@router.get("", response_model=list[RequirementSourceRead])
def list_sources(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.annex_requirement_read})
    return RequirementSourceService(db).list()


@router.post("", response_model=RequirementSourceRead, status_code=status.HTTP_201_CREATED)
def create_source(payload: RequirementSourceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.annex_requirement_write})
    return RequirementSourceService(db).create(payload)


@router.patch("/{source_id}", response_model=RequirementSourceRead)
def update_source(source_id: UUID, payload: RequirementSourceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.annex_requirement_write})
    return RequirementSourceService(db).update(source_id, payload)


@router.post("/{source_id}/status", response_model=RequirementSourceRead)
def set_source_status(source_id: UUID, payload: RequirementSourcePublish, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.annex_requirement_write})
    return RequirementSourceService(db).set_status(source_id, payload.status)


@router.get("/{source_id}/requirements", response_model=list[AnnexRequirementRead])
def list_source_requirements(source_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.annex_requirement_read})
    source = RequirementSourceService(db).get(source_id)
    return source.requirements


@router.post("/{source_id}/requirements", response_model=AnnexRequirementRead, status_code=status.HTTP_201_CREATED)
def create_source_requirement(source_id: UUID, payload: AnnexRequirementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.annex_requirement_write})
    source = RequirementSourceService(db).get(source_id)
    if source.id != payload.source_id:
        payload = payload.model_copy(update={"source_id": source.id})
    return AnnexRequirementService(db).create(payload, actor_user_id=current_user.id)
