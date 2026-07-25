"""assign substantial-change compliance actions to users"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260725_0067"
down_revision = "20260725_0066"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "change_compliance_actions",
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_change_compliance_actions_assigned_user",
        "change_compliance_actions",
        "users",
        ["assigned_to_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_change_compliance_actions_assigned_to_user_id",
        "change_compliance_actions",
        ["assigned_to_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_change_compliance_actions_assigned_to_user_id", table_name="change_compliance_actions")
    op.drop_constraint("fk_change_compliance_actions_assigned_user", "change_compliance_actions", type_="foreignkey")
    op.drop_column("change_compliance_actions", "assigned_to_user_id")
