# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.models.audit_log_event import AuditLogEvent
from app.models.base import utc_now


def _json_safe(value: Any) -> Any:
    """Coerce a single column value into a JSON-serialisable form for the ledger."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        # StrEnum members serialise via .value for a stable, human-readable string.
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    return str(value)


def snapshot_model(obj: object) -> dict[str, Any]:
    """
    Serialise a SQLAlchemy model's mapped columns to a JSON-safe dict.

    Used to capture a full snapshot of an entity into the append-only audit
    ledger *before* it is hard-deleted, so the deleted record remains
    recoverable and tamper-evident. Only mapped column attributes are included
    (relationships are intentionally excluded to keep the snapshot self-contained
    and avoid lazy-load surprises during a delete flush).
    """
    mapper = sa_inspect(obj).mapper
    return {
        attr.key: _json_safe(getattr(obj, attr.key))
        for attr in mapper.column_attrs
    }


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
