"""support period notification recipients and configurable eos lead time

Revision ID: 20260404_0006
Revises: 20260403_0005
Create Date: 2026-04-04 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260404_0006"
down_revision = "20260403_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "support_period_records",
        sa.Column("notify_before_days", sa.Integer(), nullable=False, server_default="180"),
    )

    op.create_table(
        "support_period_notification_recipients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "support_period_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_period_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "support_period_record_id",
            "user_id",
            name="uq_support_period_notification_recipients_record_user",
        ),
    )
    op.create_index(
        "ix_spnr_support_period_record_id",
        "support_period_notification_recipients",
        ["support_period_record_id"],
        unique=False,
    )
    op.create_index(
        "ix_spnr_user_id",
        "support_period_notification_recipients",
        ["user_id"],
        unique=False,
    )

    op.drop_constraint(
        "uq_lifecycle_notifications_record_type",
        "lifecycle_notifications",
        type_="unique",
    )
    op.add_column(
        "lifecycle_notifications",
        sa.Column(
            "recipient_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_lifecycle_notifications_recipient_user_id",
        "lifecycle_notifications",
        ["recipient_user_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_lifecycle_notifications_record_type_recipient",
        "lifecycle_notifications",
        ["support_period_record_id", "notification_type", "recipient_user_id"],
    )

    op.alter_column("support_period_records", "notify_before_days", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "uq_lifecycle_notifications_record_type_recipient",
        "lifecycle_notifications",
        type_="unique",
    )
    op.drop_index(
        "ix_lifecycle_notifications_recipient_user_id",
        table_name="lifecycle_notifications",
    )
    op.drop_column("lifecycle_notifications", "recipient_user_id")
    op.create_unique_constraint(
        "uq_lifecycle_notifications_record_type",
        "lifecycle_notifications",
        ["support_period_record_id", "notification_type"],
    )

    op.drop_index(
        "ix_spnr_user_id",
        table_name="support_period_notification_recipients",
    )
    op.drop_index(
        "ix_spnr_support_period_record_id",
        table_name="support_period_notification_recipients",
    )
    op.drop_table("support_period_notification_recipients")

    op.drop_column("support_period_records", "notify_before_days")
