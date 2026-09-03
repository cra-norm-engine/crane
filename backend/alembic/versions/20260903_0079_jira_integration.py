"""add Jira Cloud task integration"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260903_0079"
down_revision = "20260902_0078"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jira_connections",
        sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cloud_id", sa.String(100), nullable=False), sa.Column("site_url", sa.String(500), nullable=False), sa.Column("site_name", sa.String(255), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False), sa.Column("refresh_token_encrypted", sa.Text()), sa.Column("access_token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("scopes", sa.Text()), sa.Column("project_key", sa.String(50)), sa.Column("issue_type", sa.String(100), nullable=False, server_default="Task"),
        sa.Column("status_mapping_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")), sa.Column("priority_mapping_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("forge_installation_id", sa.String(255), unique=True), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("last_error", sa.Text()),
        sa.UniqueConstraint("created_by_user_id", "cloud_id", name="uq_jira_connection_owner_cloud"),
    )
    op.create_index("ix_jira_connections_created_by_user_id", "jira_connections", ["created_by_user_id"])
    op.create_index("ix_jira_connections_cloud_id", "jira_connections", ["cloud_id"])
    op.create_table(
        "jira_user_mappings", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("connection_id", sa.Uuid(), sa.ForeignKey("jira_connections.id", ondelete="CASCADE"), nullable=False), sa.Column("crane_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jira_account_id", sa.String(255), nullable=False), sa.Column("jira_display_name", sa.String(255)),
        sa.UniqueConstraint("connection_id", "crane_user_id", name="uq_jira_user_crane"), sa.UniqueConstraint("connection_id", "jira_account_id", name="uq_jira_user_account"),
    )
    op.create_index("ix_jira_user_mappings_connection_id", "jira_user_mappings", ["connection_id"])
    op.create_index("ix_jira_user_mappings_crane_user_id", "jira_user_mappings", ["crane_user_id"])
    op.create_table(
        "jira_task_links", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("connection_id", sa.Uuid(), sa.ForeignKey("jira_connections.id", ondelete="CASCADE"), nullable=False), sa.Column("manual_task_id", sa.Uuid(), sa.ForeignKey("manual_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issue_id", sa.String(100), nullable=False), sa.Column("issue_key", sa.String(100), nullable=False), sa.Column("issue_url", sa.String(700), nullable=False), sa.Column("sync_status", sa.String(30), nullable=False, server_default="synced"),
        sa.Column("jira_updated_at", sa.DateTime(timezone=True)), sa.Column("last_synced_at", sa.DateTime(timezone=True)), sa.Column("last_error", sa.Text()), sa.Column("last_payload_hash", sa.String(64)),
        sa.UniqueConstraint("connection_id", "manual_task_id", name="uq_jira_link_task"), sa.UniqueConstraint("connection_id", "issue_id", name="uq_jira_link_issue"),
    )
    for col in ("connection_id", "manual_task_id", "issue_key", "sync_status"):
        op.create_index(f"ix_jira_task_links_{col}", "jira_task_links", [col])
    op.create_table(
        "jira_sync_events", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("connection_id", sa.Uuid(), sa.ForeignKey("jira_connections.id", ondelete="CASCADE"), nullable=False), sa.Column("manual_task_id", sa.Uuid(), sa.ForeignKey("manual_tasks.id", ondelete="CASCADE")),
        sa.Column("direction", sa.String(20), nullable=False), sa.Column("event_type", sa.String(50), nullable=False), sa.Column("event_key", sa.String(255), nullable=False, unique=True), sa.Column("payload_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"), sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"), sa.Column("next_attempt_at", sa.DateTime(timezone=True)), sa.Column("processed_at", sa.DateTime(timezone=True)), sa.Column("last_error", sa.Text()),
    )
    for col in ("connection_id", "manual_task_id", "status", "next_attempt_at"):
        op.create_index(f"ix_jira_sync_events_{col}", "jira_sync_events", [col])


def downgrade() -> None:
    op.drop_table("jira_sync_events")
    op.drop_table("jira_task_links")
    op.drop_table("jira_user_mappings")
    op.drop_table("jira_connections")
