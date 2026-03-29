"""support period records, security updates, and lifecycle notifications

Revision ID: 20260403_0005
Revises: 20260402_0004
Create Date: 2026-04-03 00:00:00
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260403_0005"
down_revision = "20260402_0004"
branch_labels = None
depends_on = None


PERMISSION_KEYS: list[str] = [
    "support_period_read",
    "support_period_write",
    "security_update_read",
    "security_update_write",
    "lifecycle_notification_read",
    "lifecycle_notification_write",
]

ROLE_PERMISSION_MAP: dict[str, set[str]] = {
    "admin": set(PERMISSION_KEYS),
    "development_team": {
        "security_update_read",
        "security_update_write",
        "lifecycle_notification_read",
    },
    "lifecycle_manager": {
        "support_period_read",
        "support_period_write",
        "security_update_read",
        "lifecycle_notification_read",
        "lifecycle_notification_write",
    },
    "legal_team": {
        "support_period_read",
        "security_update_read",
        "lifecycle_notification_read",
    },
    "product_management": {
        "support_period_read",
        "support_period_write",
        "security_update_read",
        "lifecycle_notification_read",
    },
}


def upgrade() -> None:
    op.create_table(
        "support_period_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("support_start_date", sa.Date(), nullable=False),
        sa.Column("support_end_date", sa.Date(), nullable=False),
        sa.Column("support_type", sa.String(length=50), nullable=False),
        sa.Column("justification_text", sa.Text(), nullable=False),
        sa.Column("expected_use_time_text", sa.Text(), nullable=True),
        sa.Column("comparable_products_text", sa.Text(), nullable=True),
        sa.Column("third_party_support_constraints_text", sa.Text(), nullable=True),
        sa.Column("user_facing_summary", sa.Text(), nullable=True),
        sa.Column("packaging_summary", sa.Text(), nullable=True),
        sa.Column("eos_notification_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "superseded_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_period_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "support_end_date >= support_start_date",
            name="ck_support_period_records_date_range",
        ),
        sa.UniqueConstraint(
            "product_id",
            "is_active",
            name="uq_support_period_records_product_active",
        ),
    )
    op.create_index(
        "ix_support_period_records_product_id",
        "support_period_records",
        ["product_id"],
        unique=False,
    )
    op.create_index(
        "ix_support_period_records_is_active",
        "support_period_records",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "ix_support_period_records_superseded_by_id",
        "support_period_records",
        ["superseded_by_id"],
        unique=False,
    )

    op.create_table(
        "security_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "product_release_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_releases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cves_addressed_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("affected_versions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("distribution_mechanism", sa.String(length=50), nullable=False),
        sa.Column("available_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_security_updates_product_release_id",
        "security_updates",
        ["product_release_id"],
        unique=False,
    )

    op.create_table(
        "lifecycle_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "support_period_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_period_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "support_period_record_id",
            "notification_type",
            name="uq_lifecycle_notifications_record_type",
        ),
    )
    op.create_index(
        "ix_lifecycle_notifications_support_period_record_id",
        "lifecycle_notifications",
        ["support_period_record_id"],
        unique=False,
    )
    op.create_index(
        "ix_lifecycle_notifications_scheduled_for",
        "lifecycle_notifications",
        ["scheduled_for"],
        unique=False,
    )

    now_value = datetime.now(UTC)
    conn = op.get_bind()

    permissions_table = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("key", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    existing_permission_rows = conn.execute(sa.text("SELECT id, key FROM permissions")).fetchall()
    permission_id_by_key: dict[str, uuid.UUID] = {row[1]: row[0] for row in existing_permission_rows}

    permission_rows: list[dict[str, object]] = []
    for key in PERMISSION_KEYS:
        if key not in permission_id_by_key:
            permission_id = uuid.uuid4()
            permission_id_by_key[key] = permission_id
            permission_rows.append(
                {
                    "id": permission_id,
                    "key": key,
                    "description": None,
                    "created_at": now_value,
                    "updated_at": now_value,
                }
            )

    if permission_rows:
        op.bulk_insert(permissions_table, permission_rows)

    role_rows = conn.execute(sa.text("SELECT id, name FROM roles")).fetchall()
    role_id_by_name: dict[str, uuid.UUID] = {row[1]: row[0] for row in role_rows}

    existing_role_permission_pairs = {
        (row[0], row[1])
        for row in conn.execute(sa.text("SELECT role_id, permission_id FROM role_permissions")).fetchall()
    }

    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )

    role_permission_rows: list[dict[str, object]] = []
    for role_name, permission_keys in ROLE_PERMISSION_MAP.items():
        role_id = role_id_by_name.get(role_name)
        if role_id is None:
            continue

        for permission_key in permission_keys:
            permission_id = permission_id_by_key.get(permission_key)
            if permission_id is None:
                continue

            pair = (role_id, permission_id)
            if pair in existing_role_permission_pairs:
                continue

            role_permission_rows.append(
                {
                    "id": uuid.uuid4(),
                    "role_id": role_id,
                    "permission_id": permission_id,
                }
            )
            existing_role_permission_pairs.add(pair)

    if role_permission_rows:
        op.bulk_insert(role_permissions_table, role_permission_rows)


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE permission_id IN (
                SELECT id FROM permissions WHERE key IN :permission_keys
            )
            """
        ).bindparams(sa.bindparam("permission_keys", expanding=True)),
        {"permission_keys": PERMISSION_KEYS},
    )

    conn.execute(
        sa.text("DELETE FROM permissions WHERE key IN :permission_keys").bindparams(
            sa.bindparam("permission_keys", expanding=True)
        ),
        {"permission_keys": PERMISSION_KEYS},
    )

    op.drop_index("ix_lifecycle_notifications_scheduled_for", table_name="lifecycle_notifications")
    op.drop_index(
        "ix_lifecycle_notifications_support_period_record_id",
        table_name="lifecycle_notifications",
    )
    op.drop_table("lifecycle_notifications")

    op.drop_index("ix_security_updates_product_release_id", table_name="security_updates")
    op.drop_table("security_updates")

    op.drop_index("ix_support_period_records_superseded_by_id", table_name="support_period_records")
    op.drop_index("ix_support_period_records_is_active", table_name="support_period_records")
    op.drop_index("ix_support_period_records_product_id", table_name="support_period_records")
    op.drop_table("support_period_records")