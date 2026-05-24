"""update substantial modification criteria to Art. 3(30) / §103 alignment

Replaces the three old criteria fields on substantial_modification_assessments
with the four Commission guidance §103 criteria, retaining alters_intended_use.

Old criteria (removed):
  increases_cybersecurity_risk, changes_hazard_nature, expands_attack_surface

New criteria (added):
  introduces_new_threat_vectors  — §103 criterion 1
  enables_new_attack_scenarios   — §103 criterion 2
  changes_attack_likelihood      — §103 criterion 3
  changes_attack_impact          — §103 criterion 4

Data migration (best-effort mapping for existing rows):
  introduces_new_threat_vectors  ← expands_attack_surface
  enables_new_attack_scenarios   ← increases_cybersecurity_risk
  changes_attack_likelihood      ← FALSE (no direct predecessor)
  changes_attack_impact          ← changes_hazard_nature

is_substantial is recomputed after the rename so existing decisions remain
valid (any criterion still True → still substantial).

Revision ID: 20260524_0037
Revises: 20260524_0036
Create Date: 2026-05-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260524_0037"
down_revision = "20260524_0036"
branch_labels = None
depends_on = None

TABLE = "substantial_modification_assessments"


def upgrade() -> None:
    # 1. Add the four new criteria columns (nullable during migration)
    op.add_column(TABLE, sa.Column("introduces_new_threat_vectors", sa.Boolean(), nullable=True))
    op.add_column(TABLE, sa.Column("enables_new_attack_scenarios", sa.Boolean(), nullable=True))
    op.add_column(TABLE, sa.Column("changes_attack_likelihood", sa.Boolean(), nullable=True))
    op.add_column(TABLE, sa.Column("changes_attack_impact", sa.Boolean(), nullable=True))

    # 2. Migrate existing data using the closest-fit mapping
    op.execute(
        """
        UPDATE substantial_modification_assessments
        SET
            introduces_new_threat_vectors = expands_attack_surface,
            enables_new_attack_scenarios  = increases_cybersecurity_risk,
            changes_attack_likelihood     = FALSE,
            changes_attack_impact         = changes_hazard_nature
        """
    )

    # 3. Make new columns NOT NULL now that all rows are populated
    op.alter_column(TABLE, "introduces_new_threat_vectors", nullable=False)
    op.alter_column(TABLE, "enables_new_attack_scenarios", nullable=False)
    op.alter_column(TABLE, "changes_attack_likelihood", nullable=False)
    op.alter_column(TABLE, "changes_attack_impact", nullable=False)

    # 4. Recompute is_substantial based on the updated criteria
    op.execute(
        """
        UPDATE substantial_modification_assessments
        SET is_substantial = (
            alters_intended_use
            OR introduces_new_threat_vectors
            OR enables_new_attack_scenarios
            OR changes_attack_likelihood
            OR changes_attack_impact
        )
        """
    )

    # 5. Drop the three old criteria columns
    op.drop_column(TABLE, "increases_cybersecurity_risk")
    op.drop_column(TABLE, "changes_hazard_nature")
    op.drop_column(TABLE, "expands_attack_surface")


def downgrade() -> None:
    # 1. Re-add old columns (nullable during migration)
    op.add_column(TABLE, sa.Column("increases_cybersecurity_risk", sa.Boolean(), nullable=True))
    op.add_column(TABLE, sa.Column("changes_hazard_nature", sa.Boolean(), nullable=True))
    op.add_column(TABLE, sa.Column("expands_attack_surface", sa.Boolean(), nullable=True))

    # 2. Reverse-migrate (best-effort)
    op.execute(
        """
        UPDATE substantial_modification_assessments
        SET
            increases_cybersecurity_risk = enables_new_attack_scenarios,
            changes_hazard_nature        = changes_attack_impact,
            expands_attack_surface       = introduces_new_threat_vectors
        """
    )

    # 3. Restore NOT NULL
    op.alter_column(TABLE, "increases_cybersecurity_risk", nullable=False)
    op.alter_column(TABLE, "changes_hazard_nature", nullable=False)
    op.alter_column(TABLE, "expands_attack_surface", nullable=False)

    # 4. Drop the new columns
    op.drop_column(TABLE, "introduces_new_threat_vectors")
    op.drop_column(TABLE, "enables_new_attack_scenarios")
    op.drop_column(TABLE, "changes_attack_likelihood")
    op.drop_column(TABLE, "changes_attack_impact")
