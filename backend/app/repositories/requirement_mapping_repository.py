from __future__ import annotations

from uuid import UUID

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.artifact import Artifact
from app.models.requirement_mapping import (
    ProductRequirementDecision,
    RequirementMapping,
    RequirementMappingArtifactLink,
)
from app.repositories.base import BaseRepository


class RequirementMappingRepository(BaseRepository[RequirementMapping]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RequirementMapping)

    def artifact_links_available(self) -> bool:
        bind = self.db.get_bind()
        return inspect(bind).has_table("requirement_mapping_artifact_links")

    def _matrix_options(self):
        options = [
            selectinload(RequirementMapping.annex_requirement),
            selectinload(RequirementMapping.risk_item),
            selectinload(RequirementMapping.evidence_items),
        ]
        if self.artifact_links_available():
            options.extend(
                [
                    selectinload(RequirementMapping.artifact_links)
                    .selectinload(RequirementMappingArtifactLink.artifact)
                    .selectinload(Artifact.revisions),
                    selectinload(RequirementMapping.artifact_links)
                    .selectinload(RequirementMappingArtifactLink.artifact)
                    .selectinload(Artifact.product_links),
                ]
            )
        return options

    def list_by_risk_item(self, risk_item_id: UUID) -> list[RequirementMapping]:
        stmt = (
            select(RequirementMapping)
            .where(RequirementMapping.risk_item_id == risk_item_id)
            .order_by(RequirementMapping.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_annex_requirement(self, annex_requirement_id: UUID) -> list[RequirementMapping]:
        stmt = (
            select(RequirementMapping)
            .where(RequirementMapping.annex_requirement_id == annex_requirement_id)
            .order_by(RequirementMapping.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_release(self, release_id: UUID) -> list[RequirementMapping]:
        """Return all trace records for a specific release."""
        stmt = (
            select(RequirementMapping)
            .where(RequirementMapping.product_release_id == release_id)
            .options(*self._matrix_options())
            .order_by(RequirementMapping.created_at.desc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def list_for_matrix(self) -> list[RequirementMapping]:
        stmt = (
            select(RequirementMapping)
            .options(*self._matrix_options())
            .order_by(RequirementMapping.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_with_relations(self, mapping_id: UUID) -> RequirementMapping | None:
        stmt = (
            select(RequirementMapping)
            .where(RequirementMapping.id == mapping_id)
            .options(*self._matrix_options())
        )
        return self.db.scalar(stmt)

    def get_or_404(self, mapping_id: UUID) -> RequirementMapping:
        mapping = self.get_by_id(mapping_id)
        if mapping is None:
            raise NotFoundException("Requirement mapping not found")
        return mapping

    def list_release_decisions(self, release_id: UUID) -> list[ProductRequirementDecision]:
        """Return all applicability decisions for a specific release."""
        stmt = select(ProductRequirementDecision).where(
            ProductRequirementDecision.product_release_id == release_id
        )
        return list(self.db.scalars(stmt).all())

    def copy_decisions_from_release(
        self,
        source_release_id: UUID,
        target_release_id: UUID,
    ) -> list[ProductRequirementDecision]:
        """Copy applicability decisions from a parent release to a new release."""
        source_decisions = self.list_release_decisions(source_release_id)
        copied: list[ProductRequirementDecision] = []
        for decision in source_decisions:
            new_decision = ProductRequirementDecision(
                product_release_id=target_release_id,
                annex_requirement_id=decision.annex_requirement_id,
                applicability_decision=decision.applicability_decision,
                rationale=decision.rationale,
            )
            self.db.add(new_decision)
            copied.append(new_decision)
        if copied:
            self.db.flush()
        return copied
