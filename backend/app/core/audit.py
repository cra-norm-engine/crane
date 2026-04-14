from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log_event import AuditLogEvent
from app.models.base import utc_now


class AuditLogger:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log_event(
        self,
        *,
        actor_user_id: UUID | None,
        action_type: str,
        entity_type: str,
        entity_id: UUID | None = None,
        status: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details_json: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
        commit: bool = False,
    ) -> AuditLogEvent:
        event_occurred_at = occurred_at or utc_now()
        event_details = details_json or {}

        event = AuditLogEvent(
            occurred_at=event_occurred_at,
            actor_user_id=actor_user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=event_details,
        )

        self.db.add(event)
        self.db.flush()

        if commit:
            self.db.commit()

        return event


def create_audit_event(
    db: Session,
    *,
    actor_user_id: UUID | None,
    action_type: str,
    entity_type: str,
    entity_id: UUID | None = None,
    status: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details_json: dict[str, Any] | None = None,
    occurred_at: datetime | None = None,
    commit: bool = False,
) -> AuditLogEvent:
    return AuditLogger(db).log_event(
        actor_user_id=actor_user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        ip_address=ip_address,
        user_agent=user_agent,
        details_json=details_json,
        occurred_at=occurred_at,
        commit=commit,
    )
