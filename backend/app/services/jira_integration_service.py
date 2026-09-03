from __future__ import annotations

import base64
import hashlib
import json
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID

import httpx
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.base import utc_now
from app.models.enums import AuditStatus, EntityType
from app.models.jira_integration import (
    JiraConnection,
    JiraSyncEvent,
    JiraTaskLink,
    JiraUserMapping,
)
from app.models.manual_task import ManualTask
from app.models.user import User
from app.schemas.jira_integration import JiraConnectionUpdate, JiraUserMappingWrite
from app.schemas.my_tasks import ManualTaskUpdate
from app.services.manual_task_service import ManualTaskService

_ATLASSIAN_AUTHORIZE = "https://auth.atlassian.com/authorize"
_ATLASSIAN_TOKEN = "https://auth.atlassian.com/oauth/token"
_ATLASSIAN_RESOURCES = "https://api.atlassian.com/oauth/token/accessible-resources"
_FORGE_JWKS = "https://forge.cdn.prod.atlassian-dev.net/.well-known/jwks.json"
_FORGE_ISSUER = "forge/invocation-token"
_jwks_cache: tuple[datetime, dict] | None = None


class JiraIntegrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest())
        self.cipher = Fernet(key)

    def oauth_url(self, actor: User) -> str:
        if not settings.jira_oauth_client_id or not settings.jira_oauth_client_secret:
            raise ValidationException("Jira OAuth client ID and secret are not configured")
        state = jwt.encode(
            {"sub": str(actor.id), "type": "jira_oauth", "exp": utc_now() + timedelta(minutes=10)},
            settings.secret_key,
            algorithm="HS256",
        )
        query = urlencode({
            "audience": "api.atlassian.com",
            "client_id": settings.jira_oauth_client_id,
            "scope": "offline_access read:jira-work write:jira-work read:jira-user",
            "redirect_uri": settings.jira_oauth_redirect_uri,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
        })
        return f"{_ATLASSIAN_AUTHORIZE}?{query}"

    def complete_oauth(self, code: str, state: str) -> JiraConnection:
        try:
            claims = jwt.decode(state, settings.secret_key, algorithms=["HS256"])
            if claims.get("type") != "jira_oauth":
                raise JWTError("wrong state type")
            actor_id = UUID(claims["sub"])
        except (JWTError, KeyError, ValueError) as exc:
            raise ValidationException("Invalid or expired Jira OAuth state") from exc
        actor = self.db.get(User, actor_id)
        if actor is None or not actor.is_active:
            raise ForbiddenException("The connecting CRANE user is unavailable")
        token = self._oauth_post({
            "grant_type": "authorization_code", "client_id": settings.jira_oauth_client_id,
            "client_secret": settings.jira_oauth_client_secret, "code": code,
            "redirect_uri": settings.jira_oauth_redirect_uri,
        })
        resources = self._raw_get(_ATLASSIAN_RESOURCES, token["access_token"])
        if not resources:
            raise ValidationException("No Jira Cloud site was granted")
        resource = resources[0]
        connection = self.db.scalar(select(JiraConnection).where(
            JiraConnection.created_by_user_id == actor.id, JiraConnection.cloud_id == resource["id"],
        ))
        expires_at = utc_now() + timedelta(seconds=int(token.get("expires_in", 3600)))
        if connection is None:
            connection = JiraConnection(
                created_by_user_id=actor.id, cloud_id=resource["id"], site_url=resource["url"],
                site_name=resource.get("name") or resource["url"], access_token_encrypted=self._encrypt(token["access_token"]),
            )
            self.db.add(connection)
        connection.access_token_encrypted = self._encrypt(token["access_token"])
        if token.get("refresh_token"):
            connection.refresh_token_encrypted = self._encrypt(token["refresh_token"])
        connection.access_token_expires_at = expires_at
        connection.scopes = token.get("scope")
        connection.is_active, connection.last_error = True, None
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def list_connections(self, actor: User) -> list[JiraConnection]:
        return list(self.db.scalars(select(JiraConnection).where(JiraConnection.created_by_user_id == actor.id).order_by(JiraConnection.created_at)).all())

    def connection(self, connection_id: UUID, actor: User) -> JiraConnection:
        item = self.db.scalar(select(JiraConnection).where(JiraConnection.id == connection_id, JiraConnection.created_by_user_id == actor.id))
        if item is None:
            raise NotFoundException("Jira connection not found")
        return item

    def configure(self, connection_id: UUID, payload: JiraConnectionUpdate, actor: User) -> JiraConnection:
        item = self.connection(connection_id, actor)
        item.project_key, item.issue_type = payload.project_key.strip().upper(), payload.issue_type.strip()
        item.status_mapping_json, item.priority_mapping_json = payload.status_mapping_json, payload.priority_mapping_json
        self.db.commit()
        self.db.refresh(item)
        return item

    def disconnect(self, connection_id: UUID, actor: User) -> None:
        item = self.connection(connection_id, actor)
        item.is_active = False
        item.access_token_encrypted = self._encrypt("revoked")
        item.refresh_token_encrypted = None
        self.db.commit()

    def set_user_mapping(self, connection_id: UUID, payload: JiraUserMappingWrite, actor: User) -> JiraUserMapping:
        connection = self.connection(connection_id, actor)
        if self.db.get(User, payload.crane_user_id) is None:
            raise ValidationException("CRANE user not found")
        mapping = self.db.scalar(select(JiraUserMapping).where(
            JiraUserMapping.connection_id == connection.id, JiraUserMapping.crane_user_id == payload.crane_user_id,
        ))
        if mapping is None:
            mapping = JiraUserMapping(connection_id=connection.id, crane_user_id=payload.crane_user_id, jira_account_id=payload.jira_account_id)
            self.db.add(mapping)
        mapping.jira_account_id, mapping.jira_display_name = payload.jira_account_id, payload.jira_display_name
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def user_mappings(self, connection_id: UUID, actor: User) -> list[JiraUserMapping]:
        connection = self.connection(connection_id, actor)
        return list(self.db.scalars(select(JiraUserMapping).where(JiraUserMapping.connection_id == connection.id)).all())

    def task_link(self, task_id: UUID, actor: User) -> JiraTaskLink | None:
        ManualTaskService(self.db).visible_task(task_id, actor)
        return self.db.scalar(select(JiraTaskLink).where(JiraTaskLink.manual_task_id == task_id))

    def export_task(self, task_id: UUID, connection_id: UUID, actor: User) -> JiraTaskLink:
        task = ManualTaskService(self.db).visible_task(task_id, actor)
        if task.created_by_user_id != actor.id:
            raise ForbiddenException("Only the task creator can create its Jira issue")
        connection = self.connection(connection_id, actor)
        if not connection.is_active or not connection.project_key:
            raise ValidationException("Configure an active Jira project before exporting tasks")
        existing = self.db.scalar(select(JiraTaskLink).where(JiraTaskLink.manual_task_id == task.id))
        if existing:
            return existing
        client = JiraClient(self.db, connection, self.cipher)
        issue = client.post("/rest/api/3/issue", {"fields": self._jira_fields(task, connection)})
        issue_key = issue["key"]
        issue_url = f"{connection.site_url.rstrip('/')}/browse/{issue_key}"
        client.post(f"/rest/api/3/issue/{issue_key}/remotelink", {
            "globalId": f"crane:manual-task:{task.id}", "relationship": "compliance task",
            "object": {"url": self._crane_task_url(task.id), "title": f"CRANE task: {task.title}"},
        })
        link = JiraTaskLink(
            connection_id=connection.id, manual_task_id=task.id, issue_id=issue["id"], issue_key=issue_key,
            issue_url=issue_url, sync_status="synced", last_synced_at=utc_now(), last_payload_hash=self._task_hash(task),
        )
        self.db.add(link)
        self._audit(task, actor, "manual_task.jira_linked", {"jira_issue_key": issue_key, "jira_cloud_id": connection.cloud_id})
        self.db.commit()
        self.db.refresh(link)
        return link

    def sync_task(self, task_id: UUID, direction: str, actor: User) -> JiraTaskLink:
        task = ManualTaskService(self.db).visible_task(task_id, actor)
        link = self.db.scalar(select(JiraTaskLink).where(JiraTaskLink.manual_task_id == task.id))
        if link is None:
            raise NotFoundException("Task is not linked to Jira")
        connection = self.db.get(JiraConnection, link.connection_id)
        if connection is None or connection.created_by_user_id != actor.id:
            raise ForbiddenException("Use the Jira connection owner to synchronize this task")
        client = JiraClient(self.db, connection, self.cipher)
        try:
            if direction == "push":
                client.put(f"/rest/api/3/issue/{link.issue_key}", {"fields": self._jira_fields(task, connection, include_project=False)})
                self._push_status(client, link.issue_key, task.status, connection)
            elif direction == "pull":
                issue = client.get(f"/rest/api/3/issue/{link.issue_key}?fields=summary,description,duedate,priority,assignee,status,updated")
                self._apply_jira_issue(task, issue, connection, actor)
            else:
                raise ValidationException("Invalid Jira synchronization direction")
            link.sync_status, link.last_error, link.last_synced_at = "synced", None, utc_now()
            link.last_payload_hash = self._task_hash(task)
            self._audit(task, actor, "manual_task.jira_synced", {"direction": direction, "jira_issue_key": link.issue_key})
            self.db.commit()
            self.db.refresh(link)
        except Exception as exc:
            self.db.rollback()
            link = self.db.get(JiraTaskLink, link.id)
            if link:
                link.sync_status, link.last_error = "failed", str(exc)[:2000]
                self.db.commit()
            raise
        return link

    def enqueue_forge_event(self, token: str, payload: dict) -> JiraSyncEvent | None:
        claims = verify_forge_token(token)
        installation_id = ((claims.get("app") or {}).get("installationId"))
        cloud_id = ((claims.get("context") or {}).get("cloudId"))
        connection = self.db.scalar(select(JiraConnection).where(or_(
            JiraConnection.forge_installation_id == installation_id,
            JiraConnection.cloud_id == cloud_id,
        )))
        if connection is None:
            raise NotFoundException("No CRANE Jira connection matches this Forge installation")
        if installation_id and not connection.forge_installation_id:
            connection.forge_installation_id = installation_id
        event = payload.get("event") if isinstance(payload.get("event"), dict) else payload
        issue = event.get("issue") or {}
        issue_id = str(issue.get("id") or event.get("issueId") or "")
        event_type = str(event.get("eventType") or event.get("webhookEvent") or "issue_updated")
        fallback = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        event_key = str(event.get("id") or f"forge:{connection.id}:{event_type}:{issue_id}:{fallback}")
        if self.db.scalar(select(JiraSyncEvent.id).where(JiraSyncEvent.event_key == event_key)):
            return None
        link = self.db.scalar(select(JiraTaskLink).where(JiraTaskLink.connection_id == connection.id, JiraTaskLink.issue_id == issue_id)) if issue_id else None
        item = JiraSyncEvent(
            connection_id=connection.id, manual_task_id=link.manual_task_id if link else None,
            direction="inbound", event_type=event_type[:50], event_key=event_key[:255],
            payload_json={**payload, "_forge_principal": claims.get("principal")},
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def process_event(self, event_id: UUID) -> None:
        """Consume one durable Forge event; safe to invoke from a background task."""
        item = self.db.get(JiraSyncEvent, event_id)
        if item is None or item.status == "processed":
            return
        link = self.db.get(JiraTaskLink, item.manual_task_id) if item.manual_task_id else None
        connection = self.db.get(JiraConnection, item.connection_id)
        task = self.db.get(ManualTask, item.manual_task_id) if item.manual_task_id else None
        if link is None or connection is None or task is None:
            item.status, item.processed_at = "ignored", utc_now()
            self.db.commit()
            return
        if "deleted" in item.event_type.lower():
            link.sync_status = "jira_deleted"
            link.last_error = "The linked Jira issue was deleted"
            item.status, item.processed_at = "processed", utc_now()
            self.db.commit()
            return
        try:
            issue = JiraClient(self.db, connection, self.cipher).get(
                f"/rest/api/3/issue/{link.issue_key}?fields=summary,description,duedate,priority,assignee,status,updated"
            )
            creator = self.db.get(User, task.created_by_user_id)
            if creator is None:
                raise NotFoundException("Task creator no longer exists")
            self._apply_jira_issue(task, issue, connection, creator)
            link.sync_status, link.last_error, link.last_synced_at = "synced", None, utc_now()
            item.status, item.processed_at, item.last_error = "processed", utc_now(), None
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            item = self.db.get(JiraSyncEvent, event_id)
            link = self.db.get(JiraTaskLink, item.manual_task_id) if item and item.manual_task_id else None
            if item:
                item.attempts += 1
                item.last_error = str(exc)[:2000]
                item.status = "failed" if item.attempts >= 5 else "pending"
                item.next_attempt_at = utc_now() + timedelta(minutes=2 ** min(item.attempts, 5))
            if link:
                link.sync_status, link.last_error = "failed", str(exc)[:2000]
            self.db.commit()

    def process_pending_events(self, limit: int = 50) -> int:
        due = or_(JiraSyncEvent.next_attempt_at.is_(None), JiraSyncEvent.next_attempt_at <= utc_now())
        event_ids = list(self.db.scalars(
            select(JiraSyncEvent.id)
            .where(JiraSyncEvent.status == "pending", due)
            .order_by(JiraSyncEvent.created_at)
            .limit(limit)
        ).all())
        for event_id in event_ids:
            self.process_event(event_id)
        return len(event_ids)

    def forge_task(self, token: str, issue_id: str) -> tuple[JiraTaskLink, ManualTask] | None:
        claims = verify_forge_token(token)
        installation_id = ((claims.get("app") or {}).get("installationId"))
        cloud_id = ((claims.get("context") or {}).get("cloudId"))
        connection = self.db.scalar(select(JiraConnection).where(or_(JiraConnection.forge_installation_id == installation_id, JiraConnection.cloud_id == cloud_id)))
        if connection is None:
            return None
        link = self.db.scalar(select(JiraTaskLink).where(JiraTaskLink.connection_id == connection.id, JiraTaskLink.issue_id == issue_id))
        return (link, self.db.get(ManualTask, link.manual_task_id)) if link else None

    def _jira_fields(self, task: ManualTask, connection: JiraConnection, include_project: bool = True) -> dict:
        fields: dict = {
            "summary": task.title, "description": text_to_adf(task.description or ""),
            "duedate": task.due_date.isoformat() if task.due_date else None,
            "labels": ["crane-compliance"],
        }
        if include_project:
            fields.update({"project": {"key": connection.project_key}, "issuetype": {"name": connection.issue_type}})
        priority = connection.priority_mapping_json.get(task.priority)
        if priority:
            fields["priority"] = {"id" if str(priority).isdigit() else "name": str(priority)}
        mapping = self.db.scalar(select(JiraUserMapping).where(
            JiraUserMapping.connection_id == connection.id, JiraUserMapping.crane_user_id == task.assigned_to_user_id,
        ))
        if mapping:
            fields["assignee"] = {"accountId": mapping.jira_account_id}
        return fields

    def _apply_jira_issue(self, task: ManualTask, issue: dict, connection: JiraConnection, actor: User) -> None:
        fields = issue.get("fields") or {}
        service = ManualTaskService(self.db)
        if actor.id == task.created_by_user_id:
            priority_name = (fields.get("priority") or {}).get("name")
            inverse_priority = {str(v).lower(): k for k, v in connection.priority_mapping_json.items()}
            assignee = (fields.get("assignee") or {}).get("accountId")
            user_mapping = self.db.scalar(select(JiraUserMapping).where(JiraUserMapping.connection_id == connection.id, JiraUserMapping.jira_account_id == assignee)) if assignee else None
            service.update(task.id, ManualTaskUpdate(
                title=fields.get("summary") or task.title,
                description=adf_to_text(fields.get("description")),
                due_date=fields.get("duedate"),
                priority=inverse_priority.get(str(priority_name).lower(), task.priority),
                assigned_to_user_id=user_mapping.crane_user_id if user_mapping else task.assigned_to_user_id,
            ), actor)
            task = self.db.get(ManualTask, task.id)
        status_id = str((fields.get("status") or {}).get("id") or "")
        inverse_status = {str(v): k for k, v in connection.status_mapping_json.items()}
        wanted = inverse_status.get(status_id)
        status_actor = self.db.get(User, task.assigned_to_user_id)
        if wanted and status_actor and wanted != task.status:
            if wanted == "completed":
                service.complete(task.id, "Completed in Jira", status_actor)
            elif task.status == "completed":
                service.reopen(task.id, "Reopened in Jira", status_actor)
                if wanted != "open":
                    service.set_status(task.id, wanted, status_actor)
            else:
                service.set_status(task.id, wanted, status_actor)

    @staticmethod
    def _push_status(client: JiraClient, issue_key: str, status: str, connection: JiraConnection) -> None:
        target = connection.status_mapping_json.get(status)
        if not target:
            return
        transitions = client.get(f"/rest/api/3/issue/{issue_key}/transitions").get("transitions", [])
        transition = next((item for item in transitions if str(item.get("to", {}).get("id")) == str(target) or str(item.get("id")) == str(target)), None)
        if transition:
            client.post(f"/rest/api/3/issue/{issue_key}/transitions", {"transition": {"id": transition["id"]}})

    @staticmethod
    def _task_hash(task: ManualTask) -> str:
        raw = json.dumps({"title": task.title, "description": task.description, "due_date": str(task.due_date), "priority": task.priority, "status": task.status, "assignee": str(task.assigned_to_user_id)}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _crane_task_url(task_id: UUID) -> str:
        return f"{settings.jira_frontend_settings_url.split('/settings')[0].rstrip('/')}/my-tasks?task={task_id}"

    def _audit(self, task: ManualTask, actor: User, action: str, details: dict) -> None:
        create_audit_event(self.db, actor_user_id=actor.id, action_type=action, entity_type=EntityType.manual_task, entity_id=task.id, status=AuditStatus.success, details_json=details)

    def _encrypt(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()

    def _oauth_post(self, payload: dict) -> dict:
        try:
            response = httpx.post(_ATLASSIAN_TOKEN, json=payload, timeout=20)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise AppException("Jira OAuth exchange failed", 502, "JIRA_OAUTH_ERROR") from exc

    @staticmethod
    def _raw_get(url: str, token: str) -> list[dict]:
        try:
            response = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise AppException("Unable to read Jira Cloud sites", 502, "JIRA_API_ERROR") from exc


class JiraClient:
    def __init__(self, db: Session, connection: JiraConnection, cipher: Fernet) -> None:
        self.db, self.connection, self.cipher = db, connection, cipher

    def get(self, path: str) -> dict:
        return self._request("GET", path)

    def post(self, path: str, payload: dict) -> dict:
        return self._request("POST", path, payload)

    def put(self, path: str, payload: dict) -> dict:
        return self._request("PUT", path, payload)

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        token = self._access_token()
        url = f"https://api.atlassian.com/ex/jira/{self.connection.cloud_id}{path}"
        for attempt in range(4):
            response = httpx.request(method, url, json=payload, headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"}, timeout=20)
            if response.status_code == 429 and attempt < 3:
                time.sleep(min(float(response.headers.get("Retry-After", "1")), 10))
                continue
            if response.status_code == 401 and attempt == 0:
                token = self._refresh()
                continue
            if response.is_error:
                raise AppException(f"Jira API request failed ({response.status_code})", 502, "JIRA_API_ERROR")
            return response.json() if response.content else {}
        raise AppException("Jira API rate limit retry exhausted", 503, "JIRA_RATE_LIMIT")

    def _access_token(self) -> str:
        if self.connection.access_token_expires_at and self.connection.access_token_expires_at > utc_now() + timedelta(seconds=60):
            return self._decrypt(self.connection.access_token_encrypted)
        return self._refresh()

    def _refresh(self) -> str:
        if not self.connection.refresh_token_encrypted:
            raise AppException("Jira authorization expired; reconnect Jira", 401, "JIRA_RECONNECT_REQUIRED")
        response = httpx.post(_ATLASSIAN_TOKEN, json={
            "grant_type": "refresh_token", "client_id": settings.jira_oauth_client_id,
            "client_secret": settings.jira_oauth_client_secret,
            "refresh_token": self._decrypt(self.connection.refresh_token_encrypted),
        }, timeout=20)
        if response.is_error:
            raise AppException("Jira authorization expired; reconnect Jira", 401, "JIRA_RECONNECT_REQUIRED")
        data = response.json()
        self.connection.access_token_encrypted = self.cipher.encrypt(data["access_token"].encode()).decode()
        if data.get("refresh_token"):
            self.connection.refresh_token_encrypted = self.cipher.encrypt(data["refresh_token"].encode()).decode()
        self.connection.access_token_expires_at = utc_now() + timedelta(seconds=int(data.get("expires_in", 3600)))
        self.db.commit()
        return data["access_token"]

    def _decrypt(self, value: str) -> str:
        try:
            return self.cipher.decrypt(value.encode()).decode()
        except InvalidToken as exc:
            raise AppException("Stored Jira credentials cannot be decrypted", 500, "JIRA_TOKEN_ERROR") from exc


def text_to_adf(value: str) -> dict:
    paragraphs = value.splitlines() or [""]
    return {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": ([{"type": "text", "text": line}] if line else [])} for line in paragraphs]}


def adf_to_text(value: dict | None) -> str | None:
    if not value:
        return None
    lines: list[str] = []
    for node in value.get("content", []):
        texts: list[str] = []
        stack = list(node.get("content", []))
        while stack:
            item = stack.pop(0)
            if item.get("type") == "text":
                texts.append(item.get("text", ""))
            stack[0:0] = item.get("content", [])
        lines.append("".join(texts))
    return "\n".join(lines)


def verify_forge_token(token: str) -> dict:
    if not settings.jira_forge_app_id:
        raise AppException("Forge app ID is not configured", 503, "JIRA_FORGE_NOT_CONFIGURED")
    try:
        header = jwt.get_unverified_header(token)
        jwks = _forge_jwks()
        key = next(item for item in jwks["keys"] if item.get("kid") == header.get("kid"))
        return jwt.decode(token, key, algorithms=["RS256"], audience=settings.jira_forge_app_id, issuer=_FORGE_ISSUER, options={"verify_at_hash": False})
    except (JWTError, KeyError, StopIteration, httpx.HTTPError) as exc:
        raise AppException("Invalid Forge invocation token", 401, "INVALID_FORGE_TOKEN") from exc


def _forge_jwks() -> dict:
    global _jwks_cache
    now = datetime.now(UTC)
    if _jwks_cache and _jwks_cache[0] > now:
        return _jwks_cache[1]
    response = httpx.get(_FORGE_JWKS, timeout=10)
    response.raise_for_status()
    _jwks_cache = (now + timedelta(hours=1), response.json())
    return _jwks_cache[1]
