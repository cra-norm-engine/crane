"""External findings and scoped ingestion credentials."""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "20260910_0083"
down_revision = "20260910_0082"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sbom_vulnerability_findings", sa.Column("external_source", sa.String(100)))
    op.add_column("sbom_vulnerability_findings", sa.Column("external_id", sa.String(500)))
    op.add_column("sbom_vulnerability_findings", sa.Column("external_updated_at", sa.DateTime(timezone=True)))
    op.add_column("sbom_vulnerability_findings", sa.Column("external_payload_json", postgresql.JSONB()))
    op.create_unique_constraint("uq_external_finding", "sbom_vulnerability_findings", ["sbom_record_id", "external_source", "external_id"])
    op.create_table(
        "ingestion_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("sbom_record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sbom_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("ingestion_keys")
    op.drop_constraint("uq_external_finding", "sbom_vulnerability_findings", type_="unique")
    for column in ("external_source", "external_id", "external_updated_at", "external_payload_json"):
        op.drop_column("sbom_vulnerability_findings", column)
