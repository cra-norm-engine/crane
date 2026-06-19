"""Add missing 'substantial_modification_analysis' value to releasegateitemcode.

The ReleaseGateItemCode enum gained this member in the model (it is auto-added as
a gate item for v2+ releases), but the PostgreSQL enum type was never updated —
so creating a release gate for any release with a parent failed. This adds the
value to the DB enum.

Revision ID: 20260618_0055
Revises: 20260618_0054
Create Date: 2026-06-18
"""

from __future__ import annotations

from alembic import op

revision = "20260618_0055"
down_revision = "20260618_0054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block, so use an
    # autocommit block. IF NOT EXISTS makes it safe on databases already patched.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE releasegateitemcode ADD VALUE IF NOT EXISTS 'substantial_modification_analysis'"
        )


def downgrade() -> None:
    # PostgreSQL does not support removing a value from an enum type.
    pass
