from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.artifact import Artifact, ArtifactProductLink, ArtifactRevision
from app.repositories.base import BaseRepository


class ArtifactRepository(BaseRepository[Artifact]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Artifact)

    def list_all(self, *, product_id: UUID | None = None) -> list[Artifact]:
        stmt = (
            select(Artifact)
            .options(selectinload(Artifact.revisions), selectinload(Artifact.product_links))
            .order_by(Artifact.updated_at.desc())
        )
        if product_id is not None:
            stmt = stmt.join(ArtifactProductLink).where(ArtifactProductLink.product_id == product_id)
        return list(self.db.scalars(stmt).unique().all())

    def get_with_relations(self, artifact_id: UUID) -> Artifact | None:
        stmt = (
            select(Artifact)
            .where(Artifact.id == artifact_id)
            .options(selectinload(Artifact.revisions), selectinload(Artifact.product_links))
        )
        return self.db.scalar(stmt)

    def get_or_404(self, artifact_id: UUID) -> Artifact:
        artifact = self.get_with_relations(artifact_id)
        if artifact is None:
            raise NotFoundException("Artifact not found")
        return artifact


class ArtifactRevisionRepository(BaseRepository[ArtifactRevision]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ArtifactRevision)

    def get_with_relations(self, revision_id: UUID) -> ArtifactRevision | None:
        stmt = (
            select(ArtifactRevision)
            .where(ArtifactRevision.id == revision_id)
            .options(selectinload(ArtifactRevision.artifact))
        )
        return self.db.scalar(stmt)

    def get_or_404(self, revision_id: UUID) -> ArtifactRevision:
        revision = self.get_with_relations(revision_id)
        if revision is None:
            raise NotFoundException("Artifact revision not found")
        return revision
