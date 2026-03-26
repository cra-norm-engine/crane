"""rbac permissions and role permission mappings

Revision ID: 20260402_0004
Revises: 20260401_0003
Create Date: 2026-04-02 00:00:00
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260402_0004"
down_revision = "20260401_0003"
branch_labels = None
depends_on = None


PERMISSION_KEYS: list[str] = [
    "product_read",
    "product_write",
    "release_read",
    "release_write",
    "release_lifecycle_write",
    "remote_processing_element_read",
    "remote_processing_element_write",
    "scope_evaluation_read",
    "scope_evaluation_write",
    "risk_assessment_read",
    "risk_assessment_write",
    "risk_item_read",
    "risk_item_write",
    "annex_requirement_read",
    "annex_requirement_write",
    "requirement_mapping_read",
    "requirement_mapping_write",
    "evidence_item_read",
    "evidence_item_write",
    "audit_read",
    "authority_package_generate",
    "admin_manage_users",
]

ROLE_PERMISSION_MAP: dict[str, set[str]] = {
    "admin": set(PERMISSION_KEYS),
    "cybersecurity_engineer": {
        "product_read",
        "release_read",
        "remote_processing_element_read",
        "remote_processing_element_write",
        "scope_evaluation_read",
        "scope_evaluation_write",
        "risk_assessment_read",
        "risk_assessment_write",
        "risk_item_read",
        "risk_item_write",
        "annex_requirement_read",
        "annex_requirement_write",
        "requirement_mapping_read",
        "requirement_mapping_write",
        "evidence_item_read",
        "evidence_item_write",
        "audit_read",
    },
    "development_team": {
        "product_read",
        "release_read",
        "remote_processing_element_read",
    },
    "product_owner": {
        "product_read",
        "product_write",
        "release_read",
        "release_write",
        "remote_processing_element_read",
        "remote_processing_element_write",
        "scope_evaluation_read",
        "risk_assessment_read",
        "risk_item_read",
        "annex_requirement_read",
        "requirement_mapping_read",
        "evidence_item_read",
    },
    "lifecycle_manager": {
        "product_read",
        "release_read",
        "release_lifecycle_write",
        "remote_processing_element_read",
        "scope_evaluation_read",
        "risk_assessment_read",
        "risk_item_read",
        "annex_requirement_read",
        "requirement_mapping_read",
        "evidence_item_read",
    },
    "legal_team": {
        "product_read",
        "release_read",
        "remote_processing_element_read",
        "scope_evaluation_read",
        "risk_assessment_read",
        "risk_item_read",
        "annex_requirement_read",
        "requirement_mapping_read",
        "evidence_item_read",
    },
    "product_management": {
        "product_read",
        "product_write",
        "release_read",
        "release_write",
        "remote_processing_element_read",
        "remote_processing_element_write",
        "scope_evaluation_read",
        "risk_assessment_read",
        "risk_item_read",
        "annex_requirement_read",
        "requirement_mapping_read",
        "evidence_item_read",
    },
}


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("key", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_permissions_key", "permissions", ["key"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "permission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"], unique=False)
    op.create_index(
        "ix_role_permissions_permission_id",
        "role_permissions",
        ["permission_id"],
        unique=False,
    )

    now_value = datetime.now(UTC)

    permissions_table = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("key", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    conn = op.get_bind()

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

    op.drop_index("ix_role_permissions_permission_id", table_name="role_permissions")
    op.drop_index("ix_role_permissions_role_id", table_name="role_permissions")
    op.drop_table("role_permissions")

    op.drop_index("ix_permissions_key", table_name="permissions")
    op.drop_table("permissions")