"""Add release gate item prerequisites (dependencies between gate items).

Revision ID: 20260517_0029
Revises: 20260510_0028
Create Date: 2026-05-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260517_0029"
down_revision = "20260510_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "release_gate_item_prerequisites",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dependent_item_id", sa.UUID(), nullable=False),
        sa.Column("prerequisite_item_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dependent_item_id"], ["release_gate_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["prerequisite_item_id"], ["release_gate_items.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "dependent_item_id",
            "prerequisite_item_id",
            name="uq_release_gate_prerequisites_edge",
        ),
    )
    op.create_index(
        "ix_release_gate_item_prerequisites_dependent_item_id",
        "release_gate_item_prerequisites",
        ["dependent_item_id"],
    )
    op.create_index(
        "ix_release_gate_item_prerequisites_prerequisite_item_id",
        "release_gate_item_prerequisites",
        ["prerequisite_item_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_release_gate_item_prerequisites_prerequisite_item_id",
        table_name="release_gate_item_prerequisites",
    )
    op.drop_index(
        "ix_release_gate_item_prerequisites_dependent_item_id",
        table_name="release_gate_item_prerequisites",
    )
    op.drop_table("release_gate_item_prerequisites")
