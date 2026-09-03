"""add parent/subtask links to manual tasks"""
import sqlalchemy as sa

from alembic import op

revision = "20260904_0080"
down_revision = "20260903_0079"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("manual_tasks", sa.Column("parent_task_id", sa.Uuid(), sa.ForeignKey("manual_tasks.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_manual_tasks_parent_task_id", "manual_tasks", ["parent_task_id"])


def downgrade() -> None:
    op.drop_index("ix_manual_tasks_parent_task_id", table_name="manual_tasks")
    op.drop_column("manual_tasks", "parent_task_id")
