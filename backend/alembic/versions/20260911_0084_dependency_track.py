"""Built-in Dependency-Track connections."""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "20260911_0084"
down_revision = "20260910_0083"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dependency_track_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("server_url", sa.String(2000), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_name", sa.String(500), nullable=False),
        sa.Column("sbom_record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sbom_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("automatic_sync", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("last_result", postgresql.JSONB()),
        sa.UniqueConstraint("server_url", "project_id", "sbom_record_id", name="uq_dtrack_mapping"),
    )


def downgrade() -> None:
    op.drop_table("dependency_track_connections")
