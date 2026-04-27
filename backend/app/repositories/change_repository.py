"""
Repository for Change, SubstantialModificationAssessment, and ChangeComplianceAction.

Handles all database queries for the substantial change tracking feature.
Follows the same pattern as other repositories in this project:
  - Uses SQLAlchemy 2.x select() statements with selectinload for eager loading
  - Raises NotFoundException (404) for missing records
  - Does NOT commit — commits are handled by the service layer
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.change import Change, ChangeComplianceAction, SubstantialModificationAssessment
from app.models.enums import ChangeStatus, ChangeType
from app.repositories.base import BaseRepository


class ChangeRepository(BaseRepository[Change]):
    """Data-access layer for the Change model."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, Change)

    def _base_query(self):
        """
        Returns a base SELECT statement with the assessment and its compliance
        actions eagerly loaded so callers never trigger lazy-load N+1 queries.
        """
        return (
            select(Change)
            .options(
                selectinload(Change.assessment).selectinload(
                    SubstantialModificationAssessment.compliance_actions
                )
            )
        )

    def list_all(
        self,
        *,
        product_version_id: UUID | None = None,
        status: ChangeStatus | None = None,
        change_type: ChangeType | None = None,
        is_substantial: bool | None = None,
    ) -> list[Change]:
        """
        Return all changes, optionally filtered by product version, status,
        type, or whether they were assessed as substantial.
        Results are ordered newest change_date first.
        """
        stmt = self._base_query().order_by(Change.change_date.desc())

        if product_version_id is not None:
            stmt = stmt.where(Change.product_version_id == product_version_id)
        if status is not None:
            stmt = stmt.where(Change.status == status)
        if change_type is not None:
            stmt = stmt.where(Change.change_type == change_type)

        # Filter by is_substantial requires a join to the assessment table
        if is_substantial is not None:
            stmt = stmt.join(
                SubstantialModificationAssessment,
                SubstantialModificationAssessment.change_id == Change.id,
                isouter=(is_substantial is False),  # LEFT JOIN when filtering False
            ).where(SubstantialModificationAssessment.is_substantial == is_substantial)

        return list(self.db.scalars(stmt).all())

    def get_or_404(self, change_id: UUID) -> Change:
        """Fetch a single change by ID, raising 404 if not found."""
        record = self.db.scalar(
            self._base_query().where(Change.id == change_id)
        )
        if record is None:
            raise NotFoundException("Change not found")
        return record

    def get_assessment(
        self, change_id: UUID
    ) -> SubstantialModificationAssessment | None:
        """Fetch the assessment for a change, or None if not yet assessed."""
        return self.db.scalar(
            select(SubstantialModificationAssessment)
            .where(SubstantialModificationAssessment.change_id == change_id)
            .options(
                selectinload(SubstantialModificationAssessment.compliance_actions)
            )
        )

    def get_compliance_action_or_404(
        self, action_id: UUID
    ) -> ChangeComplianceAction:
        """Fetch a compliance action by ID, raising 404 if not found."""
        action = self.db.scalar(
            select(ChangeComplianceAction).where(ChangeComplianceAction.id == action_id)
        )
        if action is None:
            raise NotFoundException("Compliance action not found")
        return action
