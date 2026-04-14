from __future__ import annotations

import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.config import settings
from app.core.exceptions import ConflictException, NotFoundException
from app.models.artifact import Artifact, ArtifactProductLink, ArtifactRevision
from app.models.enums import ArtifactSourceType, AuditStatus, EntityType, EvidenceType
from app.repositories.artifact_repository import ArtifactRepository, ArtifactRevisionRepository


class ArtifactService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.artifact_repository = ArtifactRepository(db)
        self.artifact_revision_repository = ArtifactRevisionRepository(db)

    def list(self, *, product_id: UUID | None = None, query: str | None = None) -> list[dict]:
        artifacts = self.artifact_repository.list_all(product_id=product_id)
        if query:
            query_lower = query.lower().strip()
            artifacts = [
                artifact
                for artifact in artifacts
                if query_lower in artifact.title.lower()
                or (artifact.description and query_lower in artifact.description.lower())
            ]
        return [self._artifact_list_payload(artifact) for artifact in artifacts]

    def get(self, artifact_id: UUID) -> dict:
        artifact = self.artifact_repository.get_or_404(artifact_id)
        return self._artifact_payload(artifact)

    async def create_with_upload(
        self,
        *,
        title: str,
        artifact_type: EvidenceType,
        created_by_user_id: UUID,
        upload: UploadFile,
        description: str | None = None,
        change_summary: str | None = None,
        product_id: UUID | None = None,
        commit: bool = True,
    ) -> dict:
        artifact, _ = await self.create_with_upload_record(
            title=title,
            artifact_type=artifact_type,
            created_by_user_id=created_by_user_id,
            upload=upload,
            description=description,
            change_summary=change_summary,
            product_id=product_id,
            commit=commit,
        )
        return self.get(artifact.id)

    async def create_with_upload_record(
        self,
        *,
        title: str,
        artifact_type: EvidenceType,
        created_by_user_id: UUID,
        upload: UploadFile,
        description: str | None = None,
        change_summary: str | None = None,
        product_id: UUID | None = None,
        commit: bool = True,
    ) -> tuple[Artifact, ArtifactRevision]:
        artifact = Artifact(
            title=title,
            description=description,
            artifact_type=artifact_type,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(artifact)
        self.db.flush()
        self._ensure_product_link(artifact.id, product_id)

        revision = await self._store_uploaded_revision(
            artifact=artifact,
            uploaded_by_user_id=created_by_user_id,
            upload=upload,
            change_summary=change_summary,
        )
        self.db.flush()
        create_audit_event(
            self.db,
            actor_user_id=created_by_user_id,
            action_type="artifact.uploaded",
            entity_type=EntityType.evidence_item,
            entity_id=artifact.id,
            status=AuditStatus.success,
            details_json={
                "artifact_id": str(artifact.id),
                "revision_id": str(revision.id),
                "artifact_title": artifact.title,
                "artifact_type": artifact.artifact_type.value,
                "product_id": str(product_id) if product_id else None,
                "original_filename": revision.original_filename,
                "revision_number": revision.revision_number,
            },
        )
        if commit:
            self.db.commit()
        return artifact, revision

    def create_external_link(
        self,
        *,
        title: str,
        artifact_type: EvidenceType,
        created_by_user_id: UUID,
        external_url: str,
        description: str | None = None,
        change_summary: str | None = None,
        product_id: UUID | None = None,
        commit: bool = True,
    ) -> dict:
        artifact, _ = self.create_external_link_record(
            title=title,
            artifact_type=artifact_type,
            created_by_user_id=created_by_user_id,
            external_url=external_url,
            description=description,
            change_summary=change_summary,
            product_id=product_id,
            commit=commit,
        )
        return self.get(artifact.id)

    def create_external_link_record(
        self,
        *,
        title: str,
        artifact_type: EvidenceType,
        created_by_user_id: UUID,
        external_url: str,
        description: str | None = None,
        change_summary: str | None = None,
        product_id: UUID | None = None,
        commit: bool = True,
    ) -> tuple[Artifact, ArtifactRevision]:
        artifact = Artifact(
            title=title,
            description=description,
            artifact_type=artifact_type,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(artifact)
        self.db.flush()
        self._ensure_product_link(artifact.id, product_id)

        revision = ArtifactRevision(
            artifact_id=artifact.id,
            revision_number=1,
            source_type=ArtifactSourceType.external_link,
            external_url=external_url,
            change_summary=change_summary,
            uploaded_by_user_id=created_by_user_id,
        )
        self.db.add(revision)
        self.db.flush()
        create_audit_event(
            self.db,
            actor_user_id=created_by_user_id,
            action_type="artifact.linked",
            entity_type=EntityType.evidence_item,
            entity_id=artifact.id,
            status=AuditStatus.success,
            details_json={
                "artifact_id": str(artifact.id),
                "revision_id": str(revision.id),
                "artifact_title": artifact.title,
                "artifact_type": artifact.artifact_type.value,
                "product_id": str(product_id) if product_id else None,
                "external_url": external_url,
            },
        )
        if commit:
            self.db.commit()
        return artifact, revision

    async def upload_revision(
        self,
        artifact_id: UUID,
        *,
        uploaded_by_user_id: UUID,
        upload: UploadFile,
        change_summary: str | None = None,
        product_id: UUID | None = None,
    ) -> dict:
        artifact = self.artifact_repository.get_or_404(artifact_id)
        self._ensure_product_link(artifact.id, product_id)
        revision = await self._store_uploaded_revision(
            artifact=artifact,
            uploaded_by_user_id=uploaded_by_user_id,
            upload=upload,
            change_summary=change_summary,
        )
        create_audit_event(
            self.db,
            actor_user_id=uploaded_by_user_id,
            action_type="artifact.revision_uploaded",
            entity_type=EntityType.evidence_item,
            entity_id=artifact.id,
            status=AuditStatus.success,
            details_json={
                "artifact_id": str(artifact.id),
                "artifact_title": artifact.title,
                "product_id": str(product_id) if product_id else None,
                "revision_id": str(revision.id),
                "revision_number": revision.revision_number,
                "original_filename": revision.original_filename,
            },
        )
        self.db.commit()
        return self.get(artifact.id)

    def _ensure_product_link(self, artifact_id: UUID, product_id: UUID | None) -> None:
        if product_id is None:
            return
        stmt = select(ArtifactProductLink).where(
            ArtifactProductLink.artifact_id == artifact_id,
            ArtifactProductLink.product_id == product_id,
        )
        existing = self.db.scalar(stmt)
        if existing is None:
            self.db.add(ArtifactProductLink(artifact_id=artifact_id, product_id=product_id))
            self.db.flush()

    async def _store_uploaded_revision(
        self,
        *,
        artifact: Artifact,
        uploaded_by_user_id: UUID,
        upload: UploadFile,
        change_summary: str | None,
    ) -> ArtifactRevision:
        filename = upload.filename or "artifact.bin"
        upload_root = Path(settings.artifact_upload_dir)
        upload_root.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4()}-{filename}"
        destination = upload_root / stored_name

        hasher = hashlib.sha256()
        size = 0
        with destination.open("wb") as buffer:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                hasher.update(chunk)
                buffer.write(chunk)

        await upload.close()

        current_revision_count = len(artifact.revisions)
        revision = ArtifactRevision(
            artifact_id=artifact.id,
            revision_number=current_revision_count + 1,
            source_type=ArtifactSourceType.upload,
            original_filename=filename,
            content_type=upload.content_type,
            file_size_bytes=size,
            sha256=hasher.hexdigest(),
            storage_path=str(destination),
            change_summary=change_summary,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        self.db.add(revision)
        self.db.flush()
        return revision

    def _artifact_payload(self, artifact: Artifact) -> dict:
        revisions = list(artifact.revisions)
        latest_revision = revisions[0] if revisions else None
        payload = {
            "id": artifact.id,
            "title": artifact.title,
            "description": artifact.description,
            "artifact_type": artifact.artifact_type,
            "created_by_user_id": artifact.created_by_user_id,
            "created_by_user": self._user_summary_payload(artifact.created_by_user),
            "created_at": artifact.created_at,
            "updated_at": artifact.updated_at,
            "latest_revision": self._revision_payload(latest_revision) if latest_revision else None,
            "revisions": [self._revision_payload(revision) for revision in revisions],
            "linked_product_ids": [link.product_id for link in artifact.product_links],
        }
        return payload

    def _artifact_list_payload(self, artifact: Artifact) -> dict:
        revisions = list(artifact.revisions)
        latest_revision = revisions[0] if revisions else None
        payload = {
            "id": artifact.id,
            "title": artifact.title,
            "description": artifact.description,
            "artifact_type": artifact.artifact_type,
            "created_by_user_id": artifact.created_by_user_id,
            "created_by_user": self._user_summary_payload(artifact.created_by_user),
            "created_at": artifact.created_at,
            "updated_at": artifact.updated_at,
            "latest_revision": self._revision_payload(latest_revision) if latest_revision else None,
            "linked_product_ids": [link.product_id for link in artifact.product_links],
        }
        return payload

    def _revision_payload(self, revision: ArtifactRevision) -> dict:
        return {
            "id": revision.id,
            "artifact_id": revision.artifact_id,
            "revision_number": revision.revision_number,
            "source_type": revision.source_type,
            "original_filename": revision.original_filename,
            "content_type": revision.content_type,
            "file_size_bytes": revision.file_size_bytes,
            "sha256": revision.sha256,
            "storage_path": revision.storage_path,
            "external_url": revision.external_url,
            "change_summary": revision.change_summary,
            "uploaded_by_user_id": revision.uploaded_by_user_id,
            "uploaded_by_user": self._user_summary_payload(revision.uploaded_by_user),
            "created_at": revision.created_at,
            "updated_at": revision.updated_at,
        }

    def _user_summary_payload(self, user) -> dict | None:
        if user is None:
            return None
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
        }
