"""add supplier component support lifecycle fields and alerts

Revision ID: 20260925_0086
Revises: 20260912_0085
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260925_0086"
down_revision = "20260912_0085"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("third_party_components", sa.Column("support_start_date", sa.Date(), nullable=True))
    op.add_column("third_party_components", sa.Column("support_basis", sa.String(length=40), nullable=True))
    op.add_column("third_party_components", sa.Column("support_scope", sa.Text(), nullable=True))
    op.add_column("third_party_components", sa.Column("support_reference_url", sa.String(length=2048), nullable=True))
    op.add_column("third_party_components", sa.Column("support_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "third_party_components",
        sa.Column("support_verified_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "third_party_components",
        sa.Column("support_notify_before_days", sa.Integer(), nullable=False, server_default="180"),
    )
    op.add_column("third_party_components", sa.Column("support_unknown_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_third_party_components_support_verified_by",
        "third_party_components",
        "users",
        ["support_verified_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "lifecycle_notifications",
        sa.Column("third_party_component_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("lifecycle_notifications", sa.Column("support_end_date_snapshot", sa.Date(), nullable=True))
    op.create_index(
        "ix_lifecycle_notifications_third_party_component_id",
        "lifecycle_notifications",
        ["third_party_component_id"],
    )
    op.create_foreign_key(
        "fk_lifecycle_notifications_third_party_component_id",
        "lifecycle_notifications",
        "third_party_components",
        ["third_party_component_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_lifecycle_notif_component_eos
        ON lifecycle_notifications
            (third_party_component_id, notification_type, recipient_user_id, support_end_date_snapshot)
        WHERE third_party_component_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_lifecycle_notif_component_eos")
    op.drop_constraint(
        "fk_lifecycle_notifications_third_party_component_id",
        "lifecycle_notifications",
        type_="foreignkey",
    )
    op.drop_index("ix_lifecycle_notifications_third_party_component_id", table_name="lifecycle_notifications")
    op.drop_column("lifecycle_notifications", "support_end_date_snapshot")
    op.drop_column("lifecycle_notifications", "third_party_component_id")

    op.drop_constraint(
        "fk_third_party_components_support_verified_by",
        "third_party_components",
        type_="foreignkey",
    )
    op.drop_column("third_party_components", "support_unknown_reason")
    op.drop_column("third_party_components", "support_notify_before_days")
    op.drop_column("third_party_components", "support_verified_by_user_id")
    op.drop_column("third_party_components", "support_verified_at")
    op.drop_column("third_party_components", "support_reference_url")
    op.drop_column("third_party_components", "support_scope")
    op.drop_column("third_party_components", "support_basis")
    op.drop_column("third_party_components", "support_start_date")
