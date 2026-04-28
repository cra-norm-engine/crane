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
from app.models.product import Product, ProductRelease
from app.repositories.base import BaseRepository


class ChangeRepository(BaseRepository[Change]):
    """Data-access layer for the Change model."""

    def __init__(self, db: Session) -> None:
        super().__init__(db, Change)

    def _base_query(self):
        """
        Returns a base SELECT statement with the assessment, compliance actions,
        and the linked product_version→product eagerly loaded so callers never
        trigger lazy-load N+1 queries. product_version and its parent product are
        used to populate product_name and release_version in list summaries.
        """
        return (
            select(Change)
            .options(
                # Load the CRA assessment and its child compliance actions
                selectinload(Change.assessment).selectinload(
                    SubstantialModificationAssessment.compliance_actions
                ),
                # Load the release and the parent product so we can resolve names
                selectinload(Change.product_version).selectinload(ProductRelease.product),
            )
        )

    def list_all(
        self,
        *,
        product_version_id: UUID | None = None,
        product_id: UUID | None = None,
        status: ChangeStatus | None = None,
        change_type: ChangeType | None = None,
        is_substantial: bool | None = None,
    ) -> list[Change]:
        """
        Return all changes, optionally filtered by product version, product,
        status, type, or whether they were assessed as substantial.
        Results are ordered newest change_date first.

        product_id filter joins through product_releases so callers can scope
        the list to changes belonging to a specific product (used in the release
        form dropdown so only changes for the same product are shown).
        """
        stmt = self._base_query().order_by(Change.change_date.desc())

        if product_version_id is not None:
            stmt = stmt.where(Change.product_version_id == product_version_id)

        # product_id requires a join through product_releases
        if product_id is not None:
            stmt = (
                stmt
                .join(ProductRelease, ProductRelease.id == Change.product_version_id)
                .where(ProductRelease.product_id == product_id)
            )

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
