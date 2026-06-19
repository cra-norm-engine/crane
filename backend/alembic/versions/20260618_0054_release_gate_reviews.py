"""Add release_gate_reviews — append-only history of evidence review decisions.

Previously a review (accept/reject/waive/needs-update) overwrote the single
rationale on the evidence link, losing prior reviewer notes. This table records
every review decision + note immutably; the link keeps the latest snapshot.

Revision ID: 20260618_0054
Revises: 20260618_0053
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20260618_0054"
down_revision = "20260618_0053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "release_gate_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "release_gate_evidence_link_id",
            UUID(as_uuid=True),
            sa.ForeignKey("release_gate_evidence_links.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_by_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_release_gate_reviews_link",
        "release_gate_reviews",
        ["release_gate_evidence_link_id"],
    )
    op.create_index(
        "ix_release_gate_reviews_reviewer",
        "release_gate_reviews",
        ["reviewed_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_release_gate_reviews_reviewer", table_name="release_gate_reviews")
    op.drop_index("ix_release_gate_reviews_link", table_name="release_gate_reviews")
    op.drop_table("release_gate_reviews")
