from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, String, event, select, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.config import settings
from app.models.base import Base, utc_now

AUDIT_CHAIN_LOCK_KEY = 73194215


class AuditLogEvent(Base):
    __tablename__ = "audit_log_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    occurred_at: Mapped[datetime] = mapped_column(nullable=False, default=utc_now, index=True)

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    sequence_number: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    previous_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("audit_log_events.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )
    previous_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False)

    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    details_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    @staticmethod
    def compute_checksum(
        *,
        occurred_at: datetime,
        actor_user_id: uuid.UUID | None,
        action_type: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        sequence_number: int,
        previous_event_id: uuid.UUID | None,
        previous_checksum: str | None,
        status: str,
        ip_address: str | None,
        user_agent: str | None,
        details_json: dict[str, Any],
    ) -> str:
        payload = {
            "occurred_at": occurred_at.isoformat(),
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
            "action_type": action_type,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "sequence_number": sequence_number,
            "previous_event_id": str(previous_event_id) if previous_event_id else None,
            "previous_checksum": previous_checksum,
            "status": status,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details_json": details_json,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        hmac_key = (settings.audit_hmac_key or settings.secret_key).encode("utf-8")
        return hmac.new(hmac_key, serialized.encode("utf-8"), hashlib.sha256).hexdigest()

    def set_checksum(self) -> None:
        if self.occurred_at is None:
            self.occurred_at = utc_now()

        if self.details_json is None:
            self.details_json = {}

        if self.sequence_number is None:
            self.checksum = ""
            return

        self.checksum = self.compute_checksum(
            occurred_at=self.occurred_at,
            actor_user_id=self.actor_user_id,
            action_type=self.action_type,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            sequence_number=self.sequence_number,
            previous_event_id=self.previous_event_id,
            previous_checksum=self.previous_checksum,
            status=self.status,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            details_json=self.details_json,
        )


def _prepare_new_audit_events(session: Session) -> None:
    new_events = [obj for obj in session.new if isinstance(obj, AuditLogEvent)]
    if not new_events:
        return

    session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": AUDIT_CHAIN_LOCK_KEY})
    latest = session.scalar(
        select(AuditLogEvent).order_by(AuditLogEvent.sequence_number.desc()).limit(1)
    )

    previous_event_id = latest.id if latest is not None else None
    previous_checksum = latest.checksum if latest is not None else None
    sequence_number = latest.sequence_number if latest is not None else 0

    for audit_event in new_events:
        if audit_event.id is None:
            audit_event.id = uuid.uuid4()
        if audit_event.occurred_at is None:
            audit_event.occurred_at = utc_now()
        if audit_event.details_json is None:
            audit_event.details_json = {}

        sequence_number += 1
        audit_event.sequence_number = sequence_number
        audit_event.previous_event_id = previous_event_id
        audit_event.previous_checksum = previous_checksum
        audit_event.set_checksum()

        previous_event_id = audit_event.id
        previous_checksum = audit_event.checksum


@event.listens_for(Session, "before_flush")
def protect_and_chain_audit_events(session: Session, flush_context, instances) -> None:
    mutated_existing_events = [
        obj
        for obj in session.dirty
        if isinstance(obj, AuditLogEvent) and obj not in session.new and session.is_modified(obj, include_collections=False)
    ]
    deleted_events = [obj for obj in session.deleted if isinstance(obj, AuditLogEvent)]

    if mutated_existing_events or deleted_events:
        raise RuntimeError("Audit log events are append-only and cannot be updated or deleted.")

    _prepare_new_audit_events(session)
