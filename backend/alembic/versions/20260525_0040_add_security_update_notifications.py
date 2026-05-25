"""add security_update_id to lifecycle_notifications

Revision ID: 20260525_0040
Revises: 20260525_0039
Create Date: 2026-05-25

Changes:
- lifecycle_notifications: make support_period_record_id nullable
- lifecycle_notifications: add security_update_id (nullable FK → security_updates)
- Replace old unique constraint with two partial unique indexes
  (one for EOS notifications, one for security update notifications)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260525_0040"
down_revision = "20260525_0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make support_period_record_id nullable (was NOT NULL).
    op.alter_column(
        "lifecycle_notifications",
        "support_period_record_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )

    # Add security_update_id column.
    op.add_column(
        "lifecycle_notifications",
        sa.Column(
            "security_update_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_lifecycle_notifications_security_update_id",
        "lifecycle_notifications",
        ["security_update_id"],
    )
    op.create_foreign_key(
        "fk_lifecycle_notifications_security_update_id",
        "lifecycle_notifications",
        "security_updates",
        ["security_update_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Drop the old single unique constraint.
    op.drop_constraint(
        "uq_lifecycle_notifications_record_type_recipient",
        "lifecycle_notifications",
        type_="unique",
    )

    # Create two partial unique indexes to replace it.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_lifecycle_notif_eos
        ON lifecycle_notifications (support_period_record_id, notification_type, recipient_user_id)
        WHERE support_period_record_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_lifecycle_notif_security_update
        ON lifecycle_notifications (security_update_id, notification_type, recipient_user_id)
        WHERE security_update_id IS NOT NULL
        """
    )


def downgrade() -> None:
    # Remove partial indexes.
    op.execute("DROP INDEX IF EXISTS uq_lifecycle_notif_eos")
    op.execute("DROP INDEX IF EXISTS uq_lifecycle_notif_security_update")

    # Re-create original unique constraint (only works if all rows have support_period_record_id set).
    op.create_unique_constraint(
        "uq_lifecycle_notifications_record_type_recipient",
        "lifecycle_notifications",
        ["support_period_record_id", "notification_type", "recipient_user_id"],
    )

    # Drop security_update_id.
    op.drop_constraint(
        "fk_lifecycle_notifications_security_update_id",
        "lifecycle_notifications",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_lifecycle_notifications_security_update_id",
        table_name="lifecycle_notifications",
    )
    op.drop_column("lifecycle_notifications", "security_update_id")

    # Restore NOT NULL on support_period_record_id.
    op.alter_column(
        "lifecycle_notifications",
        "support_period_record_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
