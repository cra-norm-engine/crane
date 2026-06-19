# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import hashlib
import logging
import os
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.config import settings
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.artifact import Artifact, ArtifactProductLink, ArtifactRevision
from app.models.enums import (
    ArtifactSourceType,
    AuditStatus,
    EntityType,
    EvidenceType,
    ReleaseGateWorkflowStatus,
)
from app.repositories.artifact_repository import ArtifactRepository, ArtifactRevisionRepository

logger = logging.getLogger(__name__)


def _retention_date(years: int) -> date:
    """Return today + ``years`` years, guarding the 29 Feb edge case."""
    today = date.today()
    try:
        return today.replace(year=today.year + years)
    except ValueError:
        # 29 Feb in a non-leap target year → fall back to 1 Mar.
        return today.replace(year=today.year + years, month=3, day=1)


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
            retention_until=_retention_date(settings.artifact_retention_years),
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
            retention_until=_retention_date(settings.artifact_retention_years),
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
            # External links hold no file in CRANE — nothing to hash/verify.
            integrity_status="external",
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
        # SECURITY: never build the storage path from the client-supplied filename.
        # Keep the original name only as a sanitized basename for display/download,
        # and derive the on-disk name purely from a server-generated UUID so a
        # malicious name (e.g. "../../etc/foo") cannot traverse out of the upload
        # directory. See pentest finding H-01 (arbitrary file write / RCE).
        original_filename = os.path.basename(upload.filename or "artifact.bin") or "artifact.bin"
        upload_root = Path(settings.artifact_upload_dir).resolve()
        upload_root.mkdir(parents=True, exist_ok=True)

        # The extension is taken from the sanitized basename only; the stem is a UUID.
        stored_name = f"{uuid4()}{Path(original_filename).suffix}"
        destination = (upload_root / stored_name).resolve()

        # Defense in depth: the resolved file must stay directly inside upload_root.
        if destination.parent != upload_root:
            raise ValidationException("Invalid upload filename")

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
            original_filename=original_filename,
            content_type=upload.content_type,
            file_size_bytes=size,
            sha256=hasher.hexdigest(),
            storage_path=str(destination),
            change_summary=change_summary,
            uploaded_by_user_id=uploaded_by_user_id,
            # The hash was just computed from the bytes written — verified by construction.
            integrity_status="verified",
            last_verified_at=datetime.now(UTC),
        )
        self.db.add(revision)
        self.db.flush()
        return revision

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_file(path: Path) -> str:
        """Stream a file from disk and return its SHA-256 hex digest."""
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _verify_revision(self, revision: ArtifactRevision) -> str:
        """
        Re-hash a stored revision and update its integrity status in place.

        Returns one of: "verified", "failed", "missing", "external". Does not
        commit — the caller decides when to persist.
        """
        if revision.source_type != ArtifactSourceType.upload or not revision.storage_path:
            revision.integrity_status = "external"
            return "external"
        path = Path(revision.storage_path)
        if not path.exists():
            status_value = "missing"
        elif revision.sha256 and self._hash_file(path) == revision.sha256:
            status_value = "verified"
        else:
            status_value = "failed"
        revision.integrity_status = status_value
        revision.last_verified_at = datetime.now(UTC)
        return status_value

    def get_revision_for_download(self, revision_id: UUID, *, actor_user_id: UUID) -> ArtifactRevision:
        """
        Return a revision ready to stream, after verifying its on-disk integrity.

        Raises ValidationException for external links, NotFoundException if the
        file is gone, and ConflictException if the bytes no longer match the
        recorded SHA-256 (tamper/corruption) — auditing the failure either way.
        """
        revision = self.artifact_revision_repository.get_or_404(revision_id)
        if revision.source_type != ArtifactSourceType.upload or not revision.storage_path:
            raise ValidationException("External link revisions cannot be downloaded.")

        result = self._verify_revision(revision)
        self.db.commit()
        if result == "missing":
            create_audit_event(
                self.db,
                actor_user_id=actor_user_id,
                action_type="artifact.integrity_failed",
                entity_type=EntityType.evidence_item,
                entity_id=revision.artifact_id,
                status=AuditStatus.failure,
                details_json={"revision_id": str(revision.id), "reason": "file_missing"},
                commit=True,
            )
            raise NotFoundException("Stored artifact file not found.")
        if result == "failed":
            create_audit_event(
                self.db,
                actor_user_id=actor_user_id,
                action_type="artifact.integrity_failed",
                entity_type=EntityType.evidence_item,
                entity_id=revision.artifact_id,
                status=AuditStatus.failure,
                details_json={"revision_id": str(revision.id), "reason": "hash_mismatch"},
                commit=True,
            )
            raise ConflictException(
                "Integrity check failed: the stored file no longer matches its recorded "
                "checksum and may have been altered. Download blocked."
            )
        return revision

    def verify_all(self, *, actor_user_id: UUID) -> dict:
        """
        Re-hash every uploaded revision and record the result (integrity sweep).

        Mirrors the manual-trigger pattern used for lifecycle notifications; can
        be invoked on a schedule via an external cron hitting the endpoint.
        """
        revisions = list(
            self.db.scalars(
                select(ArtifactRevision).where(
                    ArtifactRevision.source_type == ArtifactSourceType.upload
                )
            ).all()
        )
        counts = {"verified": 0, "failed": 0, "missing": 0, "external": 0}
        failures: list[str] = []
        for revision in revisions:
            result = self._verify_revision(revision)
            counts[result] = counts.get(result, 0) + 1
            if result in ("failed", "missing"):
                failures.append(str(revision.id))
        self.db.commit()
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="artifact.integrity_sweep",
            entity_type=EntityType.evidence_item,
            entity_id=None,
            status=AuditStatus.success if not failures else AuditStatus.failure,
            details_json={"checked": len(revisions), **counts, "failed_revision_ids": failures},
            commit=True,
        )
        return {"checked": len(revisions), **counts, "failed_revision_ids": failures}

    # ------------------------------------------------------------------
    # Retention, legal hold, deletion
    # ------------------------------------------------------------------

    def set_legal_hold(
        self, artifact_id: UUID, *, hold: bool, reason: str | None, actor_user_id: UUID
    ) -> dict:
        """Place or release a legal hold on an artifact (blocks deletion)."""
        artifact = self.artifact_repository.get_or_404(artifact_id)
        artifact.legal_hold = hold
        artifact.legal_hold_reason = reason if hold else None
        self.db.flush()
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="artifact.legal_hold_set" if hold else "artifact.legal_hold_released",
            entity_type=EntityType.evidence_item,
            entity_id=artifact.id,
            status=AuditStatus.success,
            details_json={"artifact_id": str(artifact.id), "reason": reason},
        )
        self.db.commit()
        return self.get(artifact.id)

    def delete_artifact(self, artifact_id: UUID, *, actor_user_id: UUID) -> None:
        """
        Permanently delete an artifact and its files — only when allowed.

        Refuses while under legal hold, before the retention deadline, or while
        any revision is evidence on an approved (frozen) release gate.
        """
        artifact = self.artifact_repository.get_or_404(artifact_id)

        if artifact.legal_hold:
            raise ConflictException("Artifact is under legal hold and cannot be deleted.")
        if artifact.retention_until and date.today() < artifact.retention_until:
            raise ConflictException(
                f"Artifact is within its retention period (until {artifact.retention_until.isoformat()}) "
                "and cannot be deleted."
            )
        for revision in artifact.revisions:
            for link in revision.release_gate_links:
                gate = link.release_gate_item.release_gate
                if gate.status == ReleaseGateWorkflowStatus.approved:
                    raise ConflictException(
                        "Artifact is evidence on an approved (frozen) release gate and cannot be deleted."
                    )

        # Capture file paths before the DB rows are removed.
        stored_paths = [
            r.storage_path for r in artifact.revisions if r.storage_path
        ]
        title = artifact.title
        self.db.delete(artifact)  # cascades revisions, gate links, product links
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="artifact.deleted",
            entity_type=EntityType.evidence_item,
            entity_id=artifact_id,
            status=AuditStatus.success,
            details_json={"artifact_id": str(artifact_id), "title": title, "files": len(stored_paths)},
        )
        self.db.commit()

        # Remove files only after the DB delete committed, so a failed commit
        # never orphans the database from its files.
        for path_str in stored_paths:
            try:
                Path(path_str).unlink(missing_ok=True)
            except OSError:
                logger.exception("Failed to remove artifact file %s after delete", path_str)

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
            "retention_until": artifact.retention_until,
            "legal_hold": artifact.legal_hold,
            "legal_hold_reason": artifact.legal_hold_reason,
            # True when CRANE retains an actual file (not just an external link).
            "is_retained": self._is_retained(revisions),
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
            "retention_until": artifact.retention_until,
            "legal_hold": artifact.legal_hold,
            "is_retained": self._is_retained(revisions),
            "latest_revision": self._revision_payload(latest_revision) if latest_revision else None,
            "linked_product_ids": [link.product_id for link in artifact.product_links],
        }
        return payload

    @staticmethod
    def _is_retained(revisions: list[ArtifactRevision]) -> bool:
        """True when at least one revision is an uploaded file held in CRANE."""
        return any(
            r.source_type == ArtifactSourceType.upload and r.storage_path for r in revisions
        )

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
            "integrity_status": revision.integrity_status,
            "last_verified_at": revision.last_verified_at,
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
