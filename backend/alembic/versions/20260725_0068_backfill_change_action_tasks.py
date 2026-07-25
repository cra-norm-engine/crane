"""backfill action task assignment and deadlines from parent changes"""
from __future__ import annotations

from alembic import op

revision = "20260725_0068"
down_revision = "20260725_0067"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE change_compliance_actions AS action
        SET assigned_to_user_id = COALESCE(action.assigned_to_user_id, change.assigned_to_user_id, assessment.assessor_user_id),
            due_date = COALESCE(action.due_date, change.due_date)
        FROM substantial_modification_assessments AS assessment
        JOIN changes AS change ON change.id = assessment.change_id
        WHERE action.assessment_id = assessment.id
          AND (action.assigned_to_user_id IS NULL OR action.due_date IS NULL)
        """
    )


def downgrade() -> None:
    # Backfilled values are valid user data and cannot be distinguished safely
    # from assignments changed after the migration, so downgrade preserves them.
    pass
