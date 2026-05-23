"""certification records for critical products (FR36)

Revision ID: 20260426_0014
Revises: 20260425_0013
Create Date: 2026-04-26 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260426_0014"
down_revision = "20260425_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "certification_records",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "product_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("certification_scheme", sa.String(50), nullable=False, index=True),
        sa.Column("certification_body_name", sa.String(255), nullable=False),
        sa.Column("certificate_number", sa.String(255), nullable=True, index=True),
        sa.Column("scope_description", sa.Text, nullable=False),
        sa.Column("issued_date", sa.Date, nullable=True),
        sa.Column("valid_until_date", sa.Date, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, index=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("recertification_required_by", sa.Date, nullable=True),
    )

    # Grant new permissions to relevant roles
    permission_table = sa.table(
        "permissions",
        sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("key", sa.String),
        sa.column("description", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    role_permission_table = sa.table(
        "role_permissions",
        sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("role_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", sa.dialects.postgresql.UUID(as_uuid=True)),
    )
    roles_table = sa.table(
        "roles",
        sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
    )

    bind = op.get_bind()

    import uuid as _uuid
    from datetime import datetime, timezone

    new_perms = [
        ("certification_record_read", "Read certification records"),
        ("certification_record_write", "Create and update certification records"),
    ]
    perm_ids: dict[str, _uuid.UUID] = {}
    now = datetime.now(timezone.utc)
    for key, description in new_perms:
        existing = bind.execute(
            sa.select(permission_table.c.id).where(permission_table.c.key == key)
        ).scalar()
        if existing is None:
            new_id = _uuid.uuid4()
            bind.execute(
                permission_table.insert().values(id=new_id, key=key, description=description, created_at=now, updated_at=now)
            )
            perm_ids[key] = new_id
        else:
            perm_ids[key] = existing

    # Roles that get read: legal_team, product_owner, cybersecurity_engineer, product_management
    # Roles that get write: legal_team, product_owner, cybersecurity_engineer
    read_roles = ["legal_team", "product_owner", "cybersecurity_engineer", "product_management", "admin"]
    write_roles = ["legal_team", "product_owner", "cybersecurity_engineer", "admin"]

    for role_name in set(read_roles + write_roles):
        role_id = bind.execute(
            sa.select(roles_table.c.id).where(roles_table.c.name == role_name)
        ).scalar()
        if role_id is None:
            continue

        perms_for_role = [perm_ids["certification_record_read"]]
        if role_name in write_roles:
            perms_for_role.append(perm_ids["certification_record_write"])

        for perm_id in perms_for_role:
            existing_rp = bind.execute(
                sa.select(role_permission_table.c.id).where(
                    role_permission_table.c.role_id == role_id,
                    role_permission_table.c.permission_id == perm_id,
                )
            ).scalar()
            if existing_rp is None:
                bind.execute(
                    role_permission_table.insert().values(
                        id=_uuid.uuid4(),
                        role_id=role_id,
                        permission_id=perm_id,
                    )
                )


def downgrade() -> None:
    bind = op.get_bind()
    permission_table = sa.table(
        "permissions",
        sa.column("id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.column("key", sa.String),
    )
    role_permission_table = sa.table(
        "role_permissions",
        sa.column("permission_id", sa.dialects.postgresql.UUID(as_uuid=True)),
    )

    for key in ("certification_record_read", "certification_record_write"):
        perm_id = bind.execute(
            sa.select(permission_table.c.id).where(permission_table.c.key == key)
        ).scalar()
        if perm_id:
            bind.execute(
                role_permission_table.delete().where(role_permission_table.c.permission_id == perm_id)
            )
            bind.execute(permission_table.delete().where(permission_table.c.key == key))

    op.drop_table("certification_records")
