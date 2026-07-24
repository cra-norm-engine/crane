"""Add FOSS to the product classification enum

CRA: free & open-source software made available in the course of a commercial
activity is a distinct product category. It follows the self-assessment route
unless it is itself categorised as a critical product. This adds a "foss" value
to the existing productclassification PostgreSQL enum so products can be tagged
as FOSS in the product inventory.

Revision ID: 20260715_0064
Revises: 20260713_0063
Create Date: 2026-07-15
"""

from __future__ import annotations

from alembic import op

revision = "20260715_0064"
down_revision = "20260713_0063"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block, so commit
    # the ambient migration transaction before issuing it. IF NOT EXISTS makes
    # the migration idempotent if the value was already added out of band.
    op.execute("COMMIT")
    op.execute("ALTER TYPE productclassification ADD VALUE IF NOT EXISTS 'foss'")


def downgrade() -> None:
    # PostgreSQL provides no supported way to drop a single enum value, so this
    # migration is not reversible. Removing "foss" would require recreating the
    # productclassification type and rewriting every column that uses it, which
    # is unsafe to automate here. Left intentionally as a no-op.
    pass
