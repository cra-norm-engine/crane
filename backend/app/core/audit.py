from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log_event import AuditLogEvent
from app.models.user import User


def create_audit_event(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_name: str,
    entity_id: UUID | None = None,
    correlation_id: str | None = None,
    ip_address: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> AuditLogEvent:
    event = AuditLogEvent(
        actor_id=actor.id if actor else None,
        action=action,
        entity_name=entity_name,
        entity_id=entity_id,
        correlation_id=correlation_id,
        ip_address=ip_address,
        metadata_json=metadata_json or {},
    )
    db.add(event)
    db.flush()
    return event