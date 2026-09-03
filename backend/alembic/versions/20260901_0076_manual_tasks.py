"""add manually created tasks"""
from alembic import op
import sqlalchemy as sa

revision = "20260901_0076"
down_revision = "20260809_0075"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "manual_tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("related_route", sa.String(80)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("due_date", sa.Date()),
        sa.Column("assigned_to_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
    )
    op.create_index("ix_manual_tasks_status", "manual_tasks", ["status"])
    op.create_index("ix_manual_tasks_assigned_to_user_id", "manual_tasks", ["assigned_to_user_id"])


def downgrade() -> None:
    op.drop_table("manual_tasks")
