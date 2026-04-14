"""harden audit chain

Revision ID: 20260414_0011
Revises: 20260412_0010
Create Date: 2026-04-14 12:00:00
"""

from __future__ import annotations

import hashlib
import hmac
import json
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.config import settings

revision = "20260414_0011"
down_revision = "20260412_0010"
branch_labels = None
depends_on = None


audit_log_events = sa.table(
    "audit_log_events",
    sa.column("id", postgresql.UUID(as_uuid=True)),
    sa.column("occurred_at", sa.DateTime(timezone=True)),
    sa.column("actor_user_id", postgresql.UUID(as_uuid=True)),
    sa.column("action_type", sa.String(length=120)),
    sa.column("entity_type", sa.String(length=120)),
    sa.column("entity_id", postgresql.UUID(as_uuid=True)),
    sa.column("sequence_number", sa.BigInteger()),
    sa.column("previous_event_id", postgresql.UUID(as_uuid=True)),
    sa.column("previous_checksum", sa.String(length=64)),
    sa.column("status", sa.String(length=50)),
    sa.column("ip_address", sa.String(length=64)),
    sa.column("user_agent", sa.String(length=255)),
    sa.column("details_json", postgresql.JSONB(astext_type=sa.Text())),
    sa.column("checksum", sa.String(length=64)),
)


def _compute_checksum(row: dict, *, sequence_number: int, previous_event_id: UUID | None, previous_checksum: str | None) -> str:
    payload = {
        "occurred_at": row["occurred_at"].isoformat(),
        "actor_user_id": str(row["actor_user_id"]) if row["actor_user_id"] else None,
        "action_type": row["action_type"],
        "entity_type": row["entity_type"],
        "entity_id": str(row["entity_id"]) if row["entity_id"] else None,
        "sequence_number": sequence_number,
        "previous_event_id": str(previous_event_id) if previous_event_id else None,
        "previous_checksum": previous_checksum,
        "status": row["status"],
        "ip_address": row["ip_address"],
        "user_agent": row["user_agent"],
        "details_json": row["details_json"] or {},
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    hmac_key = (settings.audit_hmac_key or settings.secret_key).encode("utf-8")
    return hmac.new(hmac_key, serialized.encode("utf-8"), hashlib.sha256).hexdigest()


def upgrade() -> None:
    op.add_column("audit_log_events", sa.Column("sequence_number", sa.BigInteger(), nullable=True))
    op.add_column("audit_log_events", sa.Column("previous_event_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("audit_log_events", sa.Column("previous_checksum", sa.String(length=64), nullable=True))

    bind = op.get_bind()
    rows = bind.execute(
        sa.select(audit_log_events).order_by(audit_log_events.c.occurred_at.asc(), audit_log_events.c.id.asc())
    ).mappings().all()

    previous_event_id = None
    previous_checksum = None

    for sequence_number, row in enumerate(rows, start=1):
        checksum = _compute_checksum(
            row,
            sequence_number=sequence_number,
            previous_event_id=previous_event_id,
            previous_checksum=previous_checksum,
        )
        bind.execute(
            audit_log_events.update()
            .where(audit_log_events.c.id == row["id"])
            .values(
                sequence_number=sequence_number,
                previous_event_id=previous_event_id,
                previous_checksum=previous_checksum,
                checksum=checksum,
            )
        )
        previous_event_id = row["id"]
        previous_checksum = checksum

    op.alter_column("audit_log_events", "sequence_number", nullable=False)
    op.create_unique_constraint("uq_audit_log_events_sequence_number", "audit_log_events", ["sequence_number"])
    op.create_foreign_key(
        "fk_audit_log_events_previous_event_id",
        "audit_log_events",
        "audit_log_events",
        ["previous_event_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint("uq_audit_log_events_previous_event_id", "audit_log_events", ["previous_event_id"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_log_events_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log_events is append-only and cannot be modified';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_events_no_update
        BEFORE UPDATE ON audit_log_events
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_events_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_events_no_delete
        BEFORE DELETE ON audit_log_events
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_events_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_events_no_delete ON audit_log_events;")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_log_events_no_update ON audit_log_events;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_events_mutation();")

    op.drop_constraint("uq_audit_log_events_previous_event_id", "audit_log_events", type_="unique")
    op.drop_constraint("fk_audit_log_events_previous_event_id", "audit_log_events", type_="foreignkey")
    op.drop_constraint("uq_audit_log_events_sequence_number", "audit_log_events", type_="unique")
    op.drop_column("audit_log_events", "previous_checksum")
    op.drop_column("audit_log_events", "previous_event_id")
    op.drop_column("audit_log_events", "sequence_number")
