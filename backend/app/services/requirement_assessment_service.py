# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""Service for the release-level Annex I requirement assessment approval.

Approving an assessment freezes the release's requirement matrix, records the
approver and timestamp, gates the release workflow, and writes an immutable
snapshot. Amendments reopen the assessment to draft; re-approval appends a new
snapshot version, so history is append-only.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException
from app.models.enums import (
    AuditStatus,
    EntityType,
    RequirementAssessmentStatus,
    ReleaseStatus,
)
from app.models.requirement_assessment import (
    ReleaseRequirementAssessment,
    ReleaseRequirementAssessmentSnapshot,
)
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.requirement_mapping_repository import RequirementMappingRepository
from app.services.requirement_mapping_service import RequirementMappingService

logger = logging.getLogger(__name__)

# Once the release has moved past gate approval, its requirement assessment must
# not be silently reopened — the downstream gate would have to be reverted first.
_LOCKED_DOWNSTREAM_RELEASE_STATUSES = {
    ReleaseStatus.approved,
    ReleaseStatus.placed_on_market,
    ReleaseStatus.released,
}


class RequirementAssessmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.release_repository = ProductReleaseRepository(db)
        self.mapping_repository = RequirementMappingRepository(db)
        self.matrix_service = RequirementMappingService(db)

    # ── Queries ──────────────────────────────────────────────────────────────

    def _get_assessment(self, release_id: UUID) -> ReleaseRequirementAssessment | None:
        stmt = select(ReleaseRequirementAssessment).where(
            ReleaseRequirementAssessment.product_release_id == release_id
        )
        return self.db.scalar(stmt)

    def is_locked(self, release_id: UUID) -> bool:
        """True when the release's requirement assessment is approved (read-only)."""
        assessment = self._get_assessment(release_id)
        return assessment is not None and assessment.status == RequirementAssessmentStatus.approved

    def get_status(self, release_id: UUID) -> dict:
        """Return the assessment status payload for the matrix banner."""
        # Validate the release exists so the UI gets a clean 404 rather than a null.
        self.release_repository.get_or_404(release_id)
        assessment = self._get_assessment(release_id)

        unfinalized = self._unfinalized_codes(release_id)
        ready = len(unfinalized) == 0

        if assessment is None:
            return {
                "product_release_id": release_id,
                "status": RequirementAssessmentStatus.draft,
                "version": 0,
                "approved_at": None,
                "approved_by_name": None,
                "is_locked": False,
                "can_approve": ready,
                "unfinalized_codes": unfinalized,
            }

        return {
            "product_release_id": release_id,
            "status": assessment.status,
            "version": assessment.version,
            "approved_at": assessment.approved_at,
            "approved_by_name": (
                assessment.approved_by.full_name if assessment.approved_by else None
            ),
            "is_locked": assessment.status == RequirementAssessmentStatus.approved,
            "can_approve": (
                assessment.status != RequirementAssessmentStatus.approved and ready
            ),
            "unfinalized_codes": unfinalized,
        }

    def _unfinalized_codes(self, release_id: UUID) -> list[str]:
        """Codes of requirements that are not yet finalized for this release.

        A requirement is finalized when it is decided and risk-justified, plus
        (if applicable) has a linked artifact and a ``validated`` implementation
        status. The assessment can only be approved when every requirement is
        finalized. The per-requirement rule lives in
        ``RequirementMappingService._is_finalized`` (surfaced as ``row.finalized``).
        """
        rows = self.matrix_service.release_matrix(release_id)
        return [row.annex_requirement.code for row in rows if not row.finalized]

    # ── Mutations ────────────────────────────────────────────────────────────

    def approve(self, release_id: UUID, *, actor_user_id: UUID | None) -> dict:
        """Finalise (approve) the release's requirement assessment.

        Requires every requirement to be finalized (decided + risk-justified, and
        for applicable ones, artifact-linked + validated). Records the
        approver/timestamp, bumps the version, and writes an immutable snapshot.
        """
        self.release_repository.get_or_404(release_id)

        unfinalized = self._unfinalized_codes(release_id)
        if unfinalized:
            raise ConflictException(
                "The assessment can only be approved once every requirement is "
                f"finalized. {len(unfinalized)} requirement(s) are not finalized "
                f"yet: {', '.join(unfinalized)}"
            )

        assessment = self._get_assessment(release_id)
        if assessment is None:
            assessment = ReleaseRequirementAssessment(
                product_release_id=release_id,
                status=RequirementAssessmentStatus.draft,
                version=0,
            )
            self.db.add(assessment)
            self.db.flush()

        if assessment.status == RequirementAssessmentStatus.approved:
            raise ConflictException("Requirement assessment is already approved.")

        now = datetime.now(UTC)
        assessment.status = RequirementAssessmentStatus.approved
        assessment.version += 1
        assessment.approved_at = now
        assessment.approved_by_user_id = actor_user_id

        # Build and freeze an immutable snapshot of the whole assessment.
        snapshot_payload = self._build_snapshot_payload(release_id, assessment.version, now)
        content_sha256 = self._hash_payload(snapshot_payload)
        self.db.add(
            ReleaseRequirementAssessmentSnapshot(
                release_requirement_assessment_id=assessment.id,
                version=assessment.version,
                approved_at=now,
                approved_by_user_id=actor_user_id,
                snapshot_json=snapshot_payload,
                content_sha256=content_sha256,
            )
        )
        self.db.flush()

        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="requirement_assessment.approved",
            entity_type=EntityType.product_release.value,
            entity_id=release_id,
            status=AuditStatus.success.value,
            details_json={
                "action": "approve_requirement_assessment",
                "product_release_id": str(release_id),
                "version": assessment.version,
                "content_sha256": content_sha256,
            },
        )
        self.db.commit()
        return self.get_status(release_id)

    def reopen(self, release_id: UUID, *, actor_user_id: UUID | None) -> dict:
        """Reopen an approved assessment for amendment (back to draft).

        Refused while the release itself is gate-approved or already on the
        market — that downstream state must be reverted first.
        """
        release = self.release_repository.get_or_404(release_id)
        assessment = self._get_assessment(release_id)
        if assessment is None or assessment.status != RequirementAssessmentStatus.approved:
            raise ConflictException("Only an approved assessment can be reopened.")

        if release.release_status in _LOCKED_DOWNSTREAM_RELEASE_STATUSES:
            raise ConflictException(
                "Cannot reopen the requirement assessment while the release is "
                f"'{release.release_status.value}'. Revert the release gate first."
            )

        assessment.status = RequirementAssessmentStatus.draft
        self.db.flush()

        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="requirement_assessment.reopened",
            entity_type=EntityType.product_release.value,
            entity_id=release_id,
            status=AuditStatus.success.value,
            details_json={
                "action": "reopen_requirement_assessment",
                "product_release_id": str(release_id),
                "version": assessment.version,
            },
        )
        self.db.commit()
        return self.get_status(release_id)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _build_snapshot_payload(self, release_id: UUID, version: int, approved_at: datetime) -> dict:
        """Serialise the full matrix into a JSON-safe frozen snapshot."""
        rows = self.matrix_service.release_matrix(release_id)
        return {
            "product_release_id": str(release_id),
            "version": version,
            "approved_at": approved_at.isoformat(),
            "matrix": [row.model_dump(mode="json") for row in rows],
        }

    @staticmethod
    def _hash_payload(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
