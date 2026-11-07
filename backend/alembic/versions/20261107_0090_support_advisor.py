"""Persist support advisor assessment and review snapshots.

Revision ID: 20261107_0090
Revises: 20261009_0089
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "20261107_0090"
down_revision = "20261009_0089"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "support_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_release_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_releases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("inputs", postgresql.JSONB(), nullable=False),
        sa.Column("context_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("review_reason", sa.Text()),
    )
    for column in ("product_id", "product_release_id"):
        op.create_index(f"ix_support_assessments_{column}", "support_assessments", [column])


def downgrade():
    op.drop_table("support_assessments")
