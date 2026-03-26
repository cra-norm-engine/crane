from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


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
            "status": status,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details_json": details_json,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def set_checksum(self) -> None:
        if self.occurred_at is None:
            self.occurred_at = utc_now()

        self.checksum = self.compute_checksum(
            occurred_at=self.occurred_at,
            actor_user_id=self.actor_user_id,
            action_type=self.action_type,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            status=self.status,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            details_json=self.details_json,
        )