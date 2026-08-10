"""supplier assurance Phase 2 operational integration"""
from alembic import op
import sqlalchemy as sa

revision = "20260808_0074"
down_revision = "20260808_0073"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("supplier_assessments", sa.Column("reassessment_required", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("supplier_assessments", sa.Column("reassessment_reason", sa.Text()))
    op.add_column("supplier_assessments", sa.Column("reassessment_triggered_at", sa.DateTime(timezone=True)))
    op.add_column("supplier_assessments", sa.Column("reassessment_due_date", sa.Date()))
    op.create_table("component_maintainer_notifications",
        sa.Column("id",sa.Uuid(),primary_key=True),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),
        sa.Column("vulnerability_report_id",sa.Uuid(),sa.ForeignKey("vulnerability_reports.id",ondelete="CASCADE"),nullable=False),
        sa.Column("component_id",sa.Uuid(),sa.ForeignKey("third_party_components.id",ondelete="RESTRICT"),nullable=False),
        sa.Column("status",sa.String(30),nullable=False),sa.Column("recipient",sa.String(320),nullable=False),sa.Column("notification_method",sa.String(50),nullable=False),
        sa.Column("information_shared",sa.Text(),nullable=False),sa.Column("fix_shared",sa.Boolean(),nullable=False),sa.Column("fix_reference",sa.String(2048)),
        sa.Column("notified_at",sa.DateTime(timezone=True)),sa.Column("acknowledged_at",sa.DateTime(timezone=True)),sa.Column("maintainer_response",sa.Text()),
        sa.Column("assigned_to_user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("due_date",sa.Date()),
        sa.Column("created_by_user_id",sa.Uuid(),sa.ForeignKey("users.id",ondelete="RESTRICT"),nullable=False))
    for col in ("vulnerability_report_id","component_id","status","assigned_to_user_id"): op.create_index(f"ix_component_maintainer_notifications_{col}","component_maintainer_notifications",[col])

def downgrade() -> None:
    op.drop_table("component_maintainer_notifications")
    for col in ("reassessment_due_date","reassessment_triggered_at","reassessment_reason","reassessment_required"): op.drop_column("supplier_assessments",col)
