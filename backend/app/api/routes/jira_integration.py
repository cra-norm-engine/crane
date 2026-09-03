from __future__ import annotations

from typing import Annotated
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.product import Product, ProductRelease
from app.schemas.jira_integration import (
    JiraConnectionRead,
    JiraConnectionUpdate,
    JiraForgeTaskRead,
    JiraOAuthStartRead,
    JiraSyncRequest,
    JiraTaskLinkRead,
    JiraUserMappingRead,
    JiraUserMappingWrite,
)
from app.services.jira_integration_service import JiraIntegrationService

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
ForgeAuthorization = Annotated[str | None, Header()]


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppException("Forge invocation token is required", 401, "INVALID_FORGE_TOKEN")
    return authorization.split(" ", 1)[1]


@router.get("/oauth/start", response_model=JiraOAuthStartRead)
def oauth_start(db: DbSession, current_user: CurrentUser) -> JiraOAuthStartRead:
    return JiraOAuthStartRead(authorization_url=JiraIntegrationService(db).oauth_url(current_user))


@router.get("/oauth/callback", include_in_schema=False)
def oauth_callback(code: str, state: str, db: DbSession) -> RedirectResponse:
    connection = JiraIntegrationService(db).complete_oauth(code, state)
    parts = urlsplit(settings.jira_frontend_settings_url)
    query = urlencode([*parse_qsl(parts.query), ("jira", "connected"), ("site", connection.site_name)])
    destination = urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
    return RedirectResponse(destination, status_code=303)


@router.get("/connections", response_model=list[JiraConnectionRead])
def connections(db: DbSession, current_user: CurrentUser) -> list:
    return JiraIntegrationService(db).list_connections(current_user)


@router.patch("/connections/{connection_id}", response_model=JiraConnectionRead)
def configure_connection(connection_id: UUID, payload: JiraConnectionUpdate, db: DbSession, current_user: CurrentUser):
    return JiraIntegrationService(db).configure(connection_id, payload, current_user)


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def disconnect_connection(connection_id: UUID, db: DbSession, current_user: CurrentUser) -> Response:
    JiraIntegrationService(db).disconnect(connection_id, current_user)
    return Response(status_code=204)


@router.get("/connections/{connection_id}/users", response_model=list[JiraUserMappingRead])
def user_mappings(connection_id: UUID, db: DbSession, current_user: CurrentUser) -> list:
    return JiraIntegrationService(db).user_mappings(connection_id, current_user)


@router.put("/connections/{connection_id}/users", response_model=JiraUserMappingRead)
def set_user_mapping(connection_id: UUID, payload: JiraUserMappingWrite, db: DbSession, current_user: CurrentUser):
    return JiraIntegrationService(db).set_user_mapping(connection_id, payload, current_user)


@router.get("/tasks/{task_id}", response_model=JiraTaskLinkRead | None)
def task_link(task_id: UUID, db: DbSession, current_user: CurrentUser):
    return JiraIntegrationService(db).task_link(task_id, current_user)


@router.post("/tasks/{task_id}/export", response_model=JiraTaskLinkRead, status_code=201)
def export_task(task_id: UUID, connection_id: Annotated[UUID, Query()], db: DbSession, current_user: CurrentUser):
    return JiraIntegrationService(db).export_task(task_id, connection_id, current_user)


@router.post("/tasks/{task_id}/sync", response_model=JiraTaskLinkRead)
def sync_task(task_id: UUID, payload: JiraSyncRequest, db: DbSession, current_user: CurrentUser):
    return JiraIntegrationService(db).sync_task(task_id, payload.direction, current_user)


@router.post("/forge/events", status_code=202)
def forge_event(payload: dict, db: DbSession, authorization: ForgeAuthorization = None) -> dict:
    event = JiraIntegrationService(db).enqueue_forge_event(_bearer(authorization), payload)
    return {"accepted": True, "duplicate": event is None}


@router.get("/forge/issues/{issue_id}", response_model=JiraForgeTaskRead)
def forge_issue(issue_id: str, db: DbSession, authorization: ForgeAuthorization = None) -> JiraForgeTaskRead:
    result = JiraIntegrationService(db).forge_task(_bearer(authorization), issue_id)
    if result is None:
        return JiraForgeTaskRead(linked=False)
    link, task = result
    product = db.get(Product, task.product_id) if task.product_id else None
    release = db.get(ProductRelease, task.product_release_id) if task.product_release_id else None
    version = None
    if release:
        version = release.user_version or f"v{release.system_version}"
    return JiraForgeTaskRead(
        linked=True, issue_key=link.issue_key, task_id=task.id, title=task.title,
        status=task.status, priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        product_name=product.name if product else None, release_version=version,
        crane_url=JiraIntegrationService._crane_task_url(task.id),
        evidence_count=len(task.artifact_links), sync_status=link.sync_status,
    )
