from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, NotFoundException
from app.models.artifact import ArtifactProductLink
from app.models.enums import (
    ArtifactReviewDecision,
    AuditStatus,
    EntityType,
    ReleaseGateItemCode,
    ReleaseGateWorkflowStatus,
    ReleaseStatus,
)
from app.models.product import ProductRelease
from app.models.release_gate import ReleaseGate, ReleaseGateEvidenceLink, ReleaseGateItem
from app.services.artifact_service import ArtifactService
from app.repositories.artifact_repository import ArtifactRevisionRepository
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.release_gate_repository import (
    ReleaseGateEvidenceLinkRepository,
    ReleaseGateRepository,
)
from app.schemas.product_release import ProductReleaseRead


DEFAULT_GATE_ITEMS: list[tuple[ReleaseGateItemCode, str, str]] = [
    (
        ReleaseGateItemCode.technical_documentation,
        "Technical Documentation",
        "Upload the release-ready CRA technical documentation package or a versioned equivalent.",
    ),
    (
        ReleaseGateItemCode.risk_assessment,
        "Risk Assessment",
        "Provide the current risk assessment covering this release and its residual risks.",
    ),
    (
        ReleaseGateItemCode.sbom,
        "SBOM",
        "Attach an SBOM for this release in a machine-readable format or approved equivalent.",
    ),
    (
        ReleaseGateItemCode.test_report,
        "Security Test Reports",
        "Attach verification evidence such as SAST, DAST, fuzzing, penetration, or integration test results.",
    ),
    (
        ReleaseGateItemCode.declaration_of_conformity,
        "Declaration of Conformity",
        "Attach the draft or final declaration of conformity for review and release packaging.",
    ),
    (
        ReleaseGateItemCode.annex_mapping,
        "Annex Mapping",
        "Provide the release-specific Annex I requirement mapping and supporting traceability notes.",
    ),
]


class ReleaseGateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.release_repository = ProductReleaseRepository(db)
        self.gate_repository = ReleaseGateRepository(db)
        self.revision_repository = ArtifactRevisionRepository(db)
        self.link_repository = ReleaseGateEvidenceLinkRepository(db)
        self.artifact_service = ArtifactService(db)

    def get_or_create_by_release(self, product_release_id: UUID) -> dict:
        release = self.release_repository.get_or_404(product_release_id)
        gate = self.gate_repository.get_by_product_release_id(product_release_id)
        if gate is None:
            gate = self._create_gate(release)
            self.db.commit()
            self.db.refresh(gate)
        return self._detail_payload(release, gate)

    def submit_gate(
        self,
        product_release_id: UUID,
        *,
        actor_user_id: UUID,
    ) -> dict:
        release = self.release_repository.get_or_404(product_release_id)
        gate = self.gate_repository.get_by_product_release_id(product_release_id)
        if gate is None:
            gate = self._create_gate(release)

        self._refresh_gate_status(gate)
        gate.status = ReleaseGateWorkflowStatus.in_review
        gate.submitted_at = datetime.now(UTC)
        gate.submitted_by_user_id = actor_user_id
        release.release_status = ReleaseStatus.in_review
        self.db.flush()
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="release_gate.submitted",
            entity_type=EntityType.product_release,
            entity_id=release.id,
            status=AuditStatus.success,
            details_json={
                "action": "submit_release_gate",
                "product_id": str(release.product_id),
                "product_release_id": str(release.id),
                "release_version": release.version,
                "gate_status": gate.status.value,
            },
        )
        self.db.commit()
        return self._detail_payload(release, gate)

    def approve_gate(
        self,
        product_release_id: UUID,
        *,
        actor_user_id: UUID,
    ) -> dict:
        release = self.release_repository.get_or_404(product_release_id)
        gate = self.gate_repository.get_or_404_by_product_release_id(product_release_id)
        self._refresh_gate_status(gate)
        if any(item.is_required and item.status not in {ArtifactReviewDecision.accepted, ArtifactReviewDecision.waived} for item in gate.items):
            raise ConflictException("All required gate items must be accepted or waived before gate approval.")

        gate.status = ReleaseGateWorkflowStatus.approved
        gate.approved_at = datetime.now(UTC)
        gate.approved_by_user_id = actor_user_id
        release.release_status = ReleaseStatus.approved
        self.db.flush()
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="release_gate.approved",
            entity_type=EntityType.product_release,
            entity_id=release.id,
            status=AuditStatus.success,
            details_json={
                "action": "approve_release_gate",
                "product_id": str(release.product_id),
                "product_release_id": str(release.id),
                "release_version": release.version,
                "gate_status": gate.status.value,
            },
        )
        self.db.commit()
        return self._detail_payload(release, gate)

    def detach_revision(
        self,
        link_id: UUID,
        *,
        actor_user_id: UUID,
    ) -> dict:
        link = self.link_repository.get_or_404(link_id)
        gate_item = link.release_gate_item
        gate = gate_item.release_gate
        release = gate.product_release

        if gate.status == ReleaseGateWorkflowStatus.approved:
            raise ConflictException("Gate is approved and frozen. Evidence cannot be removed.")

        self.db.delete(link)
        self.db.flush()
        self.db.refresh(gate)
        self._refresh_gate_status(gate)
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="artifact.detached_from_gate",
            entity_type=EntityType.product_release,
            entity_id=release.id,
            status=AuditStatus.success,
            details_json={
                "action": "detach_artifact_revision",
                "product_id": str(release.product_id),
                "product_release_id": str(release.id),
                "release_version": release.version,
                "gate_item_id": str(gate_item.id),
                "link_id": str(link_id),
            },
        )
        self.db.commit()
        return self._detail_payload(release, gate)

    def attach_revision(
        self,
        product_release_id: UUID,
        gate_item_id: UUID,
        artifact_revision_id: UUID,
        *,
        actor_user_id: UUID,
    ) -> dict:
        gate = self.gate_repository.get_or_404_by_product_release_id(product_release_id)

        if gate.status == ReleaseGateWorkflowStatus.approved:
            raise ConflictException("Gate is approved and frozen. New evidence cannot be attached.")

        gate_item = next((item for item in gate.items if item.id == gate_item_id), None)
        if gate_item is None:
            raise NotFoundException("Release gate item not found for release.")

        revision = self.revision_repository.get_or_404(artifact_revision_id)
        existing = next((link for link in gate_item.evidence_links if link.artifact_revision_id == revision.id), None)
        if existing is not None:
            raise ConflictException("Artifact revision is already linked to this gate item.")

        link = ReleaseGateEvidenceLink(
            release_gate_item_id=gate_item.id,
            artifact_revision_id=revision.id,
            linked_by_user_id=actor_user_id,
            decision=ArtifactReviewDecision.pending_review,
        )
        self.db.add(link)
        self._ensure_artifact_product_link(revision.artifact_id, gate.product_release.product_id)
        self.db.flush()
        self.db.refresh(gate)
        self._refresh_gate_status(gate)
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="artifact.attached_to_gate",
            entity_type=EntityType.product_release,
            entity_id=product_release_id,
            status=AuditStatus.success,
            details_json={
                "action": "attach_artifact_revision",
                "product_id": str(gate.product_release.product_id),
                "product_release_id": str(product_release_id),
                "release_version": gate.product_release.version,
                "gate_item_id": str(gate_item.id),
                "artifact_title": revision.artifact.title,
                "artifact_revision_id": str(revision.id),
            },
        )
        self.db.commit()
        return self._detail_payload(gate.product_release, gate)

    def review_link(
        self,
        link_id: UUID,
        *,
        decision: ArtifactReviewDecision,
        rationale: str | None,
        actor_user_id: UUID,
    ) -> dict:
        link = self.link_repository.get_or_404(link_id)
        gate_item = link.release_gate_item
        gate = gate_item.release_gate
        release = gate.product_release

        if gate.status == ReleaseGateWorkflowStatus.approved:
            raise ConflictException("Gate is approved and frozen. Evidence decisions cannot be changed.")

        link.decision = decision
        link.rationale = rationale
        link.reviewed_by_user_id = actor_user_id
        link.reviewed_at = datetime.now(UTC)
        self.db.flush()
        self._refresh_gate_status(gate)

        if gate.status == ReleaseGateWorkflowStatus.approved and any(
            item.is_required and item.status not in {ArtifactReviewDecision.accepted, ArtifactReviewDecision.waived} for item in gate.items
        ):
            gate.status = ReleaseGateWorkflowStatus.blocked
            release.release_status = ReleaseStatus.blocked

        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="artifact.reviewed",
            entity_type=EntityType.product_release,
            entity_id=release.id,
            status=AuditStatus.success,
            details_json={
                "action": "review_release_gate_evidence",
                "product_id": str(release.product_id),
                "product_release_id": str(release.id),
                "release_version": release.version,
                "link_id": str(link.id),
                "artifact_title": link.artifact_revision.artifact.title,
                "decision": decision.value,
            },
        )
        self.db.commit()
        return self._detail_payload(release, gate)

    async def upload_and_attach_evidence(
        self,
        product_release_id: UUID,
        gate_item_id: UUID,
        *,
        actor_user_id: UUID,
        title: str,
        artifact_type,
        upload,
        description: str | None = None,
        change_summary: str | None = None,
    ) -> dict:
        release = self.release_repository.get_or_404(product_release_id)
        _, revision = await self.artifact_service.create_with_upload_record(
            title=title,
            artifact_type=artifact_type,
            created_by_user_id=actor_user_id,
            upload=upload,
            description=description,
            change_summary=change_summary,
            product_id=release.product_id,
            commit=False,
        )
        return self.attach_revision(
            product_release_id,
            gate_item_id,
            revision.id,
            actor_user_id=actor_user_id,
        )

    def create_and_attach_external_evidence(
        self,
        product_release_id: UUID,
        gate_item_id: UUID,
        *,
        actor_user_id: UUID,
        title: str,
        artifact_type,
        external_url: str,
        description: str | None = None,
        change_summary: str | None = None,
    ) -> dict:
        release = self.release_repository.get_or_404(product_release_id)
        _, revision = self.artifact_service.create_external_link_record(
            title=title,
            artifact_type=artifact_type,
            created_by_user_id=actor_user_id,
            external_url=external_url,
            description=description,
            change_summary=change_summary,
            product_id=release.product_id,
            commit=False,
        )
        return self.attach_revision(
            product_release_id,
            gate_item_id,
            revision.id,
            actor_user_id=actor_user_id,
        )

    def _create_gate(self, release: ProductRelease) -> ReleaseGate:
        gate = ReleaseGate(product_release_id=release.id)
        self.db.add(gate)
        self.db.flush()
        for index, (code, title, description) in enumerate(DEFAULT_GATE_ITEMS):
            self.db.add(
                ReleaseGateItem(
                    release_gate_id=gate.id,
                    code=code,
                    title=title,
                    description=description,
                    sort_order=index,
                    status=ArtifactReviewDecision.pending_review,
                )
            )
        self.db.flush()
        self.db.refresh(gate)
        return gate

    def _ensure_artifact_product_link(self, artifact_id: UUID, product_id: UUID) -> None:
        stmt = select(ArtifactProductLink).where(
            ArtifactProductLink.artifact_id == artifact_id,
            ArtifactProductLink.product_id == product_id,
        )
        if self.db.scalar(stmt) is None:
            self.db.add(ArtifactProductLink(artifact_id=artifact_id, product_id=product_id))
            self.db.flush()

    def _refresh_gate_status(self, gate: ReleaseGate) -> None:
        for item in gate.items:
            item.status = self._derive_item_status(item)

        if any(item.is_required and item.status in {ArtifactReviewDecision.rejected, ArtifactReviewDecision.needs_update}
               for item in gate.items):
            gate.status = ReleaseGateWorkflowStatus.blocked
            gate.product_release.release_status = ReleaseStatus.blocked
        elif all(
            item.status in {ArtifactReviewDecision.accepted, ArtifactReviewDecision.waived}
            for item in gate.items
            if item.is_required
        ):
            gate.status = ReleaseGateWorkflowStatus.approved
        elif any(item.evidence_links for item in gate.items):
            gate.status = ReleaseGateWorkflowStatus.in_review
        else:
            gate.status = ReleaseGateWorkflowStatus.draft

    def _derive_item_status(self, item: ReleaseGateItem) -> ArtifactReviewDecision:
        if not item.evidence_links:
            return ArtifactReviewDecision.pending_review
        decisions = [link.decision for link in item.evidence_links]
        if ArtifactReviewDecision.accepted in decisions:
            return ArtifactReviewDecision.accepted
        if ArtifactReviewDecision.rejected in decisions:
            return ArtifactReviewDecision.rejected
        if ArtifactReviewDecision.needs_update in decisions:
            return ArtifactReviewDecision.needs_update
        if ArtifactReviewDecision.waived in decisions:
            return ArtifactReviewDecision.waived
        return ArtifactReviewDecision.pending_review

    def _detail_payload(self, release: ProductRelease, gate: ReleaseGate) -> dict:
        required_items = [item for item in gate.items if item.is_required]
        accepted_items = [
            item for item in required_items if item.status in {ArtifactReviewDecision.accepted, ArtifactReviewDecision.waived}
        ]
        pending_items = [
            item for item in required_items if item.status not in {ArtifactReviewDecision.accepted, ArtifactReviewDecision.waived}
        ]
        return {
            "release": ProductReleaseRead.model_validate(release),
            "gate": {
                "id": gate.id,
                "product_release_id": gate.product_release_id,
                "status": gate.status,
                "submitted_at": gate.submitted_at,
                "submitted_by_user_id": gate.submitted_by_user_id,
                "submitted_by_user": self._user_summary_payload(gate.submitted_by_user),
                "approved_at": gate.approved_at,
                "approved_by_user_id": gate.approved_by_user_id,
                "approved_by_user": self._user_summary_payload(gate.approved_by_user),
                "created_at": gate.created_at,
                "updated_at": gate.updated_at,
                "items": [
                    {
                        "id": item.id,
                        "code": item.code,
                        "title": item.title,
                        "description": item.description,
                        "is_required": item.is_required,
                        "sort_order": item.sort_order,
                        "status": item.status,
                        "evidence_links": [
                            {
                                "id": link.id,
                                "decision": link.decision,
                                "rationale": link.rationale,
                                "linked_by_user_id": link.linked_by_user_id,
                                "linked_by_user": self._user_summary_payload(link.linked_by_user),
                                "reviewed_by_user_id": link.reviewed_by_user_id,
                                "reviewed_by_user": self._user_summary_payload(link.reviewed_by_user),
                                "reviewed_at": link.reviewed_at,
                                "created_at": link.created_at,
                                "updated_at": link.updated_at,
                                "artifact_revision": {
                                    "id": link.artifact_revision.id,
                                    "artifact_id": link.artifact_revision.artifact_id,
                                    "revision_number": link.artifact_revision.revision_number,
                                    "source_type": link.artifact_revision.source_type,
                                    "original_filename": link.artifact_revision.original_filename,
                                    "content_type": link.artifact_revision.content_type,
                                    "file_size_bytes": link.artifact_revision.file_size_bytes,
                                    "sha256": link.artifact_revision.sha256,
                                    "storage_path": link.artifact_revision.storage_path,
                                    "external_url": link.artifact_revision.external_url,
                                    "change_summary": link.artifact_revision.change_summary,
                                    "uploaded_by_user_id": link.artifact_revision.uploaded_by_user_id,
                                    "uploaded_by_user": self._user_summary_payload(link.artifact_revision.uploaded_by_user),
                                    "created_at": link.artifact_revision.created_at,
                                    "updated_at": link.artifact_revision.updated_at,
                                },
                            }
                            for link in item.evidence_links
                        ],
                    }
                    for item in gate.items
                ],
                "required_items_count": len(required_items),
                "accepted_items_count": len(accepted_items),
                "pending_items_count": len(pending_items),
            },
        }

    def _user_summary_payload(self, user) -> dict | None:
        if user is None:
            return None
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
        }
