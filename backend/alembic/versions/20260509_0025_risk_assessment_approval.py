"""Risk assessment approval workflow — adds reviewer_user_id and rejection_reason.

Enables the submit → in_review → approved/rejected cycle for risk assessments.
The reviewer_user_id records who reviewed the assessment; rejection_reason stores
the mandatory explanation when a reviewer sends the assessment back to draft.

Revision ID: 20260509_0025
Revises: 20260509_0024
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260509_0025"
down_revision = "20260509_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add reviewer_user_id — nullable FK to users with SET NULL on delete so
    # that removing a user does not break the assessment record.
    op.add_column(
        "risk_assessments",
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_risk_assessments_reviewer_user",
        "risk_assessments",
        "users",
        ["reviewer_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_risk_assessments_reviewer_user_id",
        "risk_assessments",
        ["reviewer_user_id"],
    )

    # Add rejection_reason — free-text, nullable; populated only on rejection.
    op.add_column(
        "risk_assessments",
        sa.Column("rejection_reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("risk_assessments", "rejection_reason")

    op.drop_index("ix_risk_assessments_reviewer_user_id", "risk_assessments")
    op.drop_constraint("fk_risk_assessments_reviewer_user", "risk_assessments", type_="foreignkey")
    op.drop_column("risk_assessments", "reviewer_user_id")
