"""Comments table — generic threaded comments for any entity.

Adds the `comments` table which supports Phase 1 of multi-stakeholder
collaboration (FR-COLLAB-1).  A single polymorphic table covers all entity
types so new features gain comment threads without schema changes.

Revision ID: 20260509_0023
Revises: 20260509_0022
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260509_0023"
down_revision = "20260509_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_comments_entity_type", "comments", ["entity_type"])
    op.create_index("ix_comments_entity_id", "comments", ["entity_id"])
    op.create_index("ix_comments_author_user_id", "comments", ["author_user_id"])
    # Composite index for the primary list query (entity_type + entity_id).
    op.create_index(
        "ix_comments_entity_type_entity_id",
        "comments",
        ["entity_type", "entity_id"],
    )


def downgrade() -> None:
    op.drop_table("comments")
