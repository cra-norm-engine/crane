from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.services.comment_service import CommentService

router = APIRouter()


@router.get("/", response_model=list[CommentRead])
def list_comments(
    entity_type: str = Query(min_length=1),
    entity_id: UUID = Query(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.comment_read)),
) -> list[CommentRead]:
    return CommentService(db).list_comments(entity_type, entity_id)


@router.post("/", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.comment_write)),
) -> CommentRead:
    return CommentService(db).create_comment(payload, actor=current_user)


@router.put("/{comment_id}", response_model=CommentRead)
def update_comment(
    comment_id: UUID,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.comment_write)),
) -> CommentRead:
    return CommentService(db).update_comment(comment_id, payload, actor=current_user)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.comment_write)),
) -> Response:
    CommentService(db).delete_comment(comment_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
