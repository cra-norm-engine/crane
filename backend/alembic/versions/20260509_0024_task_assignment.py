"""Task assignment — adds assigned_to_user_id and due_date to key entities.

Phase 2 of multi-stakeholder collaboration (FR-COLLAB-2).
Adds task assignment fields to the four entity types that represent
actionable work items:

  • vulnerability_reports  — assigned_to_user_id, due_date
  • changes               — assigned_to_user_id, due_date
  • release_gate_items    — assigned_to_user_id, due_date
  • risk_items            — due_date only (already has owner_user_id)

Revision ID: 20260509_0024
Revises: 20260509_0023
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260509_0024"
down_revision = "20260509_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── vulnerability_reports ─────────────────────────────────────────────────
    op.add_column(
        "vulnerability_reports",
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "vulnerability_reports",
        sa.Column("due_date", sa.Date(), nullable=True),
    )
    op.create_foreign_key(
        "fk_vulnerability_reports_assigned_to_user",
        "vulnerability_reports", "users",
        ["assigned_to_user_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_vulnerability_reports_assigned_to_user_id",
        "vulnerability_reports", ["assigned_to_user_id"],
    )

    # ── changes ───────────────────────────────────────────────────────────────
    op.add_column(
        "changes",
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "changes",
        sa.Column("due_date", sa.Date(), nullable=True),
    )
    op.create_foreign_key(
        "fk_changes_assigned_to_user",
        "changes", "users",
        ["assigned_to_user_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_changes_assigned_to_user_id",
        "changes", ["assigned_to_user_id"],
    )

    # ── release_gate_items ────────────────────────────────────────────────────
    op.add_column(
        "release_gate_items",
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "release_gate_items",
        sa.Column("due_date", sa.Date(), nullable=True),
    )
    op.create_foreign_key(
        "fk_release_gate_items_assigned_to_user",
        "release_gate_items", "users",
        ["assigned_to_user_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_release_gate_items_assigned_to_user_id",
        "release_gate_items", ["assigned_to_user_id"],
    )

    # ── risk_items ────────────────────────────────────────────────────────────
    op.add_column(
        "risk_items",
        sa.Column("due_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("risk_items", "due_date")

    op.drop_index("ix_release_gate_items_assigned_to_user_id", "release_gate_items")
    op.drop_constraint("fk_release_gate_items_assigned_to_user", "release_gate_items", type_="foreignkey")
    op.drop_column("release_gate_items", "due_date")
    op.drop_column("release_gate_items", "assigned_to_user_id")

    op.drop_index("ix_changes_assigned_to_user_id", "changes")
    op.drop_constraint("fk_changes_assigned_to_user", "changes", type_="foreignkey")
    op.drop_column("changes", "due_date")
    op.drop_column("changes", "assigned_to_user_id")

    op.drop_index("ix_vulnerability_reports_assigned_to_user_id", "vulnerability_reports")
    op.drop_constraint("fk_vulnerability_reports_assigned_to_user", "vulnerability_reports", type_="foreignkey")
    op.drop_column("vulnerability_reports", "due_date")
    op.drop_column("vulnerability_reports", "assigned_to_user_id")
