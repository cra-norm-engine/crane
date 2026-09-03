"""task audit metadata, evidence links, and notifications"""
from alembic import op
import sqlalchemy as sa

revision = "20260902_0078"
down_revision = "20260901_0077"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("manual_tasks", sa.Column("priority", sa.String(20), nullable=False, server_default="medium"))
    op.add_column("manual_tasks", sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.add_column("manual_tasks", sa.Column("completed_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")))
    op.add_column("manual_tasks", sa.Column("completion_note", sa.Text()))
    op.add_column("manual_tasks", sa.Column("archived_at", sa.DateTime(timezone=True)))
    op.add_column("manual_tasks", sa.Column("archived_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")))
    op.add_column("manual_tasks", sa.Column("archive_reason", sa.Text()))
    op.create_index("ix_manual_tasks_priority", "manual_tasks", ["priority"])
    op.create_index("ix_manual_tasks_archived_at", "manual_tasks", ["archived_at"])
    op.create_table(
        "manual_task_artifact_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("manual_task_id", sa.Uuid(), sa.ForeignKey("manual_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_revision_id", sa.Uuid(), sa.ForeignKey("artifact_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("linked_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.UniqueConstraint("manual_task_id", "artifact_revision_id", name="uq_manual_task_artifact"),
    )
    op.create_index("ix_manual_task_artifact_links_manual_task_id", "manual_task_artifact_links", ["manual_task_id"])
    op.create_index("ix_manual_task_artifact_links_artifact_revision_id", "manual_task_artifact_links", ["artifact_revision_id"])
    op.create_table(
        "task_notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("manual_task_id", sa.Uuid(), sa.ForeignKey("manual_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("dedupe_key", sa.String(255), unique=True),
        sa.Column("read_at", sa.DateTime(timezone=True)),
    )
    for column in ("manual_task_id", "recipient_user_id", "event_type", "read_at"):
        op.create_index(f"ix_task_notifications_{column}", "task_notifications", [column])


def downgrade() -> None:
    op.drop_table("task_notifications")
    op.drop_table("manual_task_artifact_links")
    op.drop_index("ix_manual_tasks_archived_at", table_name="manual_tasks")
    op.drop_index("ix_manual_tasks_priority", table_name="manual_tasks")
    for column in ("archive_reason", "archived_by_user_id", "archived_at", "completion_note", "completed_by_user_id", "completed_at", "priority"):
        op.drop_column("manual_tasks", column)
