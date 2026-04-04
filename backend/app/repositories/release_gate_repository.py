from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.artifact import ArtifactRevision
from app.models.release_gate import ReleaseGate, ReleaseGateEvidenceLink, ReleaseGateItem
from app.repositories.base import BaseRepository


class ReleaseGateRepository(BaseRepository[ReleaseGate]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ReleaseGate)

    def get_by_product_release_id(self, product_release_id: UUID) -> ReleaseGate | None:
        stmt = (
            select(ReleaseGate)
            .where(ReleaseGate.product_release_id == product_release_id)
            .options(
                selectinload(ReleaseGate.items)
                .selectinload(ReleaseGateItem.evidence_links)
                .selectinload(ReleaseGateEvidenceLink.artifact_revision)
                .selectinload(ArtifactRevision.artifact),
                selectinload(ReleaseGate.product_release),
            )
        )
        return self.db.scalar(stmt)

    def get_or_404_by_product_release_id(self, product_release_id: UUID) -> ReleaseGate:
        gate = self.get_by_product_release_id(product_release_id)
        if gate is None:
            raise NotFoundException("Release gate not found")
        return gate


class ReleaseGateEvidenceLinkRepository(BaseRepository[ReleaseGateEvidenceLink]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ReleaseGateEvidenceLink)

    def get_or_404(self, link_id: UUID) -> ReleaseGateEvidenceLink:
        link = self.get_by_id(link_id)
        if link is None:
            raise NotFoundException("Release gate evidence link not found")
        return link
