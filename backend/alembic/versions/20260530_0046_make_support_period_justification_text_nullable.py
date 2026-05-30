"""make support_period justification_text nullable

Revision ID: 20260530_0046
Revises: 20260529_0045
Create Date: 2026-05-30

justification_text was NOT NULL but is displayed in an optional collapsible
section in the UI. Users who don't fill it in get a constraint violation.
"""
from alembic import op

revision = "20260530_0046"
down_revision = "20260529_0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "support_period_records",
        "justification_text",
        nullable=True,
    )


def downgrade() -> None:
    # Fill NULLs before restoring NOT NULL constraint
    op.execute(
        "UPDATE support_period_records SET justification_text = '' WHERE justification_text IS NULL"
    )
    op.alter_column(
        "support_period_records",
        "justification_text",
        nullable=False,
    )
