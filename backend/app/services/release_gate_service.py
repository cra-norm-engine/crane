from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.config import settings
from app.core.exceptions import ConflictException, NotFoundException
from app.models.artifact import ArtifactProductLink
from app.models.enums import (
    ArtifactReviewDecision,
    ArtifactSourceType,
    AuditStatus,
    EntityType,
    ReleaseGateItemCode,
    ReleaseGateWorkflowStatus,
    ReleaseStatus,
)
from app.models.product import ProductRelease
from app.models.release_gate import ReleaseGate, ReleaseGateEvidenceLink, ReleaseGateItem, ReleaseGateItemPrerequisite
from app.services.artifact_service import ArtifactService
from app.repositories.artifact_repository import ArtifactRevisionRepository
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.release_gate_repository import (
    ReleaseGateEvidenceLinkRepository,
    ReleaseGateRepository,
)
from app.schemas.product_release import ProductReleaseRead
from app.services.sbom_record_service import SbomRecordService


DEFAULT_GATE_ITEMS: list[tuple[ReleaseGateItemCode, str, str]] = [
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
                "release_version": f"v{release.system_version}",
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

        # CRA Art. 13(2) + Annex I Part I §2(a): block approval if any exploitable vulnerabilities remain.
        if release.has_known_exploitable_vulnerabilities:
            raise ConflictException(
                "Release cannot be approved: it has known exploitable vulnerabilities. "
                "Resolve all exploitable findings (set VEX status to 'fixed' or 'not_affected') "
                "before approving the release gate. "
                f"Blocking issues: {release.kev_notes or 'see vulnerability reports'}"
            )

        gate.status = ReleaseGateWorkflowStatus.approved
        gate.approved_at = datetime.now(UTC)
        gate.approved_by_user_id = actor_user_id
        release.release_status = ReleaseStatus.approved
        self.db.flush()

        _, bundle_sha256 = self._generate_bundle(release, gate)
        gate.bundle_sha256 = bundle_sha256
        gate.bundle_generated_at = datetime.now(UTC)

        # Generate and store the compliance snapshot
        gate.snapshot_json = self._generate_snapshot(gate)
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
                "release_version": f"v{release.system_version}",
                "gate_status": gate.status.value,
                "bundle_sha256": bundle_sha256,
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
                "release_version": f"v{release.system_version}",
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
                "release_version": f"v{gate.product_release.system_version}",
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
                "release_version": f"v{release.system_version}",
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
        from app.models.enums import EvidenceType

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
        result = self.attach_revision(
            product_release_id,
            gate_item_id,
            revision.id,
            actor_user_id=actor_user_id,
        )

        # Auto-create an SbomRecord when an SBOM artifact is uploaded via the release gate.
        # The file is already on disk at revision.storage_path; read it and run analysis.
        if artifact_type == EvidenceType.sbom and revision.storage_path:
            try:
                sbom_content = Path(revision.storage_path).read_text(encoding="utf-8")
                # Use a fresh service instance so analysis runs in its own transaction.
                SbomRecordService(self.db).upload_and_analyze(
                    product_release_id=product_release_id,
                    sbom_content=sbom_content,
                    file_name=revision.original_filename,
                    notes=f"Auto-created from release gate artifact: {title}",
                    actor=type("_Actor", (), {"id": actor_user_id})(),
                )
            except Exception:
                # Analysis failure must never block the gate upload.
                import logging
                logging.getLogger(__name__).warning(
                    "SBOM auto-analysis failed for release %s — gate upload succeeded.",
                    product_release_id,
                    exc_info=True,
                )

        return result

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

    def add_custom_gate_item(
        self,
        product_release_id: UUID,
        *,
        title: str,
        description: str | None,
        actor_user_id: UUID,
    ) -> dict:
        release = self.release_repository.get_or_404(product_release_id)
        gate = self.gate_repository.get_by_product_release_id(product_release_id)
        if gate is None:
            gate = self._create_gate(release)

        if gate.status == ReleaseGateWorkflowStatus.approved:
            raise ConflictException("Gate is approved and frozen. Checklist cannot be modified.")

        max_order = max((item.sort_order for item in gate.items), default=-1)
        new_item = ReleaseGateItem(
            release_gate_id=gate.id,
            code=None,
            title=title.strip(),
            description=description,
            sort_order=max_order + 1,
            status=ArtifactReviewDecision.pending_review,
        )
        self.db.add(new_item)
        self.db.flush()
        self.db.refresh(gate)
        self._refresh_gate_status(gate)
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="release_gate.item_added",
            entity_type=EntityType.product_release,
            entity_id=release.id,
            status=AuditStatus.success,
            details_json={
                "action": "add_custom_gate_item",
                "product_release_id": str(release.id),
                "item_title": title,
            },
        )
        self.db.commit()
        return self._detail_payload(release, gate)

    def remove_gate_item(
        self,
        product_release_id: UUID,
        gate_item_id: UUID,
        *,
        actor_user_id: UUID,
    ) -> dict:
        release = self.release_repository.get_or_404(product_release_id)
        gate = self.gate_repository.get_or_404_by_product_release_id(product_release_id)

        if gate.status == ReleaseGateWorkflowStatus.approved:
            raise ConflictException("Gate is approved and frozen. Checklist cannot be modified.")

        gate_item = next((item for item in gate.items if item.id == gate_item_id), None)
        if gate_item is None:
            raise NotFoundException("Gate checklist item not found for this release.")

        item_title = gate_item.title
        self.db.delete(gate_item)
        self.db.flush()
        self.db.refresh(gate)
        self._refresh_gate_status(gate)
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="release_gate.item_removed",
            entity_type=EntityType.product_release,
            entity_id=release.id,
            status=AuditStatus.success,
            details_json={
                "action": "remove_gate_item",
                "product_release_id": str(release.id),
                "gate_item_id": str(gate_item_id),
                "item_title": item_title,
            },
        )
        self.db.commit()
        return self._detail_payload(release, gate)

    def get_bundle(self, product_release_id: UUID) -> tuple[bytes, str, str]:
        """Return (zip_bytes, sha256_hex, filename). Raises ConflictException on hash mismatch."""
        release = self.release_repository.get_or_404(product_release_id)
        gate = self.gate_repository.get_or_404_by_product_release_id(product_release_id)

        if gate.status != ReleaseGateWorkflowStatus.approved:
            raise ConflictException("Bundle is only available for approved gates.")

        if gate.bundle_sha256 is None:
            raise ConflictException("Bundle hash not available. Re-approve the gate to generate it.")

        zip_bytes, computed_sha256 = self._generate_bundle(release, gate)

        if computed_sha256 != gate.bundle_sha256:
            raise ConflictException(
                "Bundle integrity check failed: the stored hash does not match the current files. "
                "An unauthorized change to the documentation may have occurred."
            )

        product_name = getattr(release, "product", None)
        if product_name is not None:
            product_name = getattr(product_name, "name", None) or str(release.product_id)
        else:
            product_name = str(release.product_id)

        release_date = (gate.approved_at or gate.created_at).strftime("%Y-%m-%d")
        safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in f"{product_name}+{release_date}")
        filename = f"{safe_name}.zip"

        return zip_bytes, computed_sha256, filename

    def _generate_bundle(self, release: ProductRelease, gate: ReleaseGate) -> tuple[bytes, str]:
        """Build an in-memory ZIP and return (zip_bytes, sha256_hex).

        The ZIP must be byte-for-byte identical on every call so the stored SHA-256
        can be verified on download.  Two sources of non-determinism are suppressed:
        - writestr() timestamps are pinned to a fixed value (2020-01-01 00:00:00).
        - manifest.json never contains the bundle hash itself (circular reference).
        """
        buf = io.BytesIO()
        external_refs: list[dict] = []
        # Fixed timestamp used for all generated text entries so ZIP is deterministic.
        _fixed_ts = (2020, 1, 1, 0, 0, 0)

        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            seen_names: set[str] = set()

            for item in gate.items:
                for link in item.evidence_links:
                    rev = link.artifact_revision
                    if rev.source_type == ArtifactSourceType.external_link:
                        external_refs.append({
                            "checklist_item": item.title,
                            "title": rev.artifact.title if rev.artifact else rev.original_filename or "unknown",
                            "url": rev.external_url or "",
                            "added_at": str(rev.created_at),
                        })
                    elif rev.storage_path:
                        file_path = Path(rev.storage_path)
                        if file_path.exists():
                            base_name = rev.original_filename or file_path.name
                            arc_name = self._unique_arc_name(base_name, seen_names)
                            seen_names.add(arc_name)
                            # Pin the ZIP entry timestamp to the revision creation time
                            # so the file entry is deterministic regardless of call time.
                            ct = rev.created_at
                            zi = zipfile.ZipInfo(arc_name, date_time=(ct.year, ct.month, ct.day, ct.hour, ct.minute, ct.second))
                            zi.compress_type = zipfile.ZIP_DEFLATED
                            zf.writestr(zi, file_path.read_bytes())

            if external_refs:
                lines = ["# External References\n\n"]
                for ref in external_refs:
                    lines.append(f"## {ref['title']}\n")
                    lines.append(f"- **Checklist item:** {ref['checklist_item']}\n")
                    lines.append(f"- **URL:** {ref['url']}\n")
                    lines.append(f"- **Added:** {ref['added_at']}\n\n")
                zi = zipfile.ZipInfo("external_references.md", date_time=_fixed_ts)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(zi, "".join(lines))

            manifest = self._build_manifest(release, gate, external_refs)
            zi = zipfile.ZipInfo("manifest.json", date_time=_fixed_ts)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, manifest)

        zip_bytes = buf.getvalue()
        sha256 = hashlib.sha256(zip_bytes).hexdigest()
        return zip_bytes, sha256

    def _unique_arc_name(self, base_name: str, seen: set[str]) -> str:
        if base_name not in seen:
            return base_name
        stem, _, ext = base_name.rpartition(".")
        counter = 1
        while True:
            candidate = f"{stem}_{counter}.{ext}" if ext else f"{base_name}_{counter}"
            if candidate not in seen:
                return candidate
            counter += 1

    def _build_manifest(self, release: ProductRelease, gate: ReleaseGate, external_refs: list[dict]) -> str:
        import json
        files = []
        for item in gate.items:
            for link in item.evidence_links:
                rev = link.artifact_revision
                files.append({
                    "checklist_item": item.title,
                    "title": rev.artifact.title if rev.artifact else (rev.original_filename or "unknown"),
                    "source_type": rev.source_type,
                    "filename": rev.original_filename,
                    "sha256": rev.sha256,
                    "external_url": rev.external_url,
                    "added_at": str(rev.created_at),
                })
        return json.dumps({
            "product_release_id": str(release.id),
            "release_version": f"v{release.system_version}",
            "approved_at": str(gate.approved_at),
            "files": files,
        }, indent=2)

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

        # Art. 13(7) + Art. 3(30): v2+ releases (those with a parent_release_id) must
        # include a substantiality analysis documenting whether the change constitutes
        # a substantial modification. The first release of a product is a new placement
        # and has no prior version to compare against, so this item is skipped for v1.
        if release.parent_release_id is not None:
            self.db.add(
                ReleaseGateItem(
                    release_gate_id=gate.id,
                    code=ReleaseGateItemCode.substantial_modification_analysis,
                    title="Substantiality Analysis",
                    description=(
                        "Document whether this release constitutes a substantial modification "
                        "under CRA Art. 3(30). Link the formal assessment to this release via "
                        "the 'Substantiality analysis' field on the release record. "
                        "Required for all releases that follow a prior version (Art. 13(7))."
                    ),
                    sort_order=len(DEFAULT_GATE_ITEMS),
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

        # Only the explicit approve_gate() call may set status to "approved".
        # Here we handle transitions for blocked, in_review, and draft only.
        if gate.status == ReleaseGateWorkflowStatus.approved:
            # Gate was formally approved — only revert to blocked if evidence is rejected.
            if any(item.is_required and item.status in {ArtifactReviewDecision.rejected, ArtifactReviewDecision.needs_update}
                   for item in gate.items):
                gate.status = ReleaseGateWorkflowStatus.blocked
                gate.product_release.release_status = ReleaseStatus.blocked
            return

        if any(item.is_required and item.status in {ArtifactReviewDecision.rejected, ArtifactReviewDecision.needs_update}
               for item in gate.items):
            gate.status = ReleaseGateWorkflowStatus.blocked
            gate.product_release.release_status = ReleaseStatus.blocked
        elif any(item.evidence_links for item in gate.items):
            gate.status = ReleaseGateWorkflowStatus.in_review
        else:
            gate.status = ReleaseGateWorkflowStatus.draft

    def _derive_item_status(self, item: ReleaseGateItem) -> ArtifactReviewDecision:
        # Check if any unmet prerequisites exist
        unmet_prereqs = self._get_unmet_prerequisites(item)
        if unmet_prereqs:
            return ArtifactReviewDecision.pending_review

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

    def _get_unmet_prerequisites(self, item: ReleaseGateItem) -> list[ReleaseGateItem]:
        """Return prerequisites of this item that are not yet accepted."""
        unmet = []
        for prereq in item.prerequisites:
            if prereq.status not in {ArtifactReviewDecision.accepted, ArtifactReviewDecision.waived}:
                unmet.append(prereq)
        return unmet

    def _generate_snapshot(self, gate: ReleaseGate) -> dict:
        """Generate a compliance snapshot capturing the frozen state of all gate items and evidence at approval time."""
        import json
        snapshot = {
            "approved_at": gate.approved_at.isoformat() if gate.approved_at else None,
            "approved_by_user_id": str(gate.approved_by_user_id) if gate.approved_by_user_id else None,
            "bundle_sha256": gate.bundle_sha256,
            "items": [],
        }

        for item in gate.items:
            item_snapshot = {
                "id": str(item.id),
                "code": item.code.value if item.code else None,
                "title": item.title,
                "status": item.status.value,
                "evidence": [],
            }

            for link in item.evidence_links:
                rev = link.artifact_revision
                evidence_snapshot = {
                    "artifact_title": rev.artifact.title if rev.artifact else rev.original_filename or "unknown",
                    "revision_number": rev.revision_number,
                    "sha256": rev.sha256,
                    "decision": link.decision.value,
                    "reviewed_by_user_id": str(link.reviewed_by_user_id) if link.reviewed_by_user_id else None,
                    "reviewed_at": link.reviewed_at.isoformat() if link.reviewed_at else None,
                }
                item_snapshot["evidence"].append(evidence_snapshot)

            snapshot["items"].append(item_snapshot)

        return snapshot

    def add_prerequisite(
        self,
        product_release_id: UUID,
        dependent_item_id: UUID,
        prerequisite_item_id: UUID,
        *,
        actor_user_id: UUID,
    ) -> dict:
        """Add a prerequisite dependency: dependent_item depends on prerequisite_item."""
        release = self.release_repository.get_or_404(product_release_id)
        gate = self.gate_repository.get_or_404_by_product_release_id(product_release_id)

        if gate.status == ReleaseGateWorkflowStatus.approved:
            raise ConflictException("Gate is approved and frozen. Dependencies cannot be modified.")

        dependent = next((item for item in gate.items if item.id == dependent_item_id), None)
        prerequisite = next((item for item in gate.items if item.id == prerequisite_item_id), None)

        if dependent is None or prerequisite is None:
            raise NotFoundException("One or both gate items not found in this release's gate.")

        if dependent_item_id == prerequisite_item_id:
            raise ConflictException("An item cannot be a prerequisite of itself.")

        # Check if this prerequisite already exists
        existing = self.db.query(ReleaseGateItemPrerequisite).filter(
            ReleaseGateItemPrerequisite.dependent_item_id == dependent_item_id,
            ReleaseGateItemPrerequisite.prerequisite_item_id == prerequisite_item_id,
        ).first()

        if existing is not None:
            raise ConflictException("This prerequisite relationship already exists.")

        prereq_link = ReleaseGateItemPrerequisite(
            dependent_item_id=dependent_item_id,
            prerequisite_item_id=prerequisite_item_id,
        )
        self.db.add(prereq_link)
        self.db.flush()
        self.db.refresh(gate)
        self._refresh_gate_status(gate)

        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="release_gate.prerequisite_added",
            entity_type=EntityType.product_release,
            entity_id=product_release_id,
            status=AuditStatus.success,
            details_json={
                "action": "add_gate_item_prerequisite",
                "product_release_id": str(product_release_id),
                "dependent_item_id": str(dependent_item_id),
                "dependent_item_title": dependent.title,
                "prerequisite_item_id": str(prerequisite_item_id),
                "prerequisite_item_title": prerequisite.title,
            },
        )
        self.db.commit()
        return self._detail_payload(release, gate)

    def remove_prerequisite(
        self,
        product_release_id: UUID,
        dependent_item_id: UUID,
        prerequisite_item_id: UUID,
        *,
        actor_user_id: UUID,
    ) -> dict:
        """Remove a prerequisite dependency."""
        release = self.release_repository.get_or_404(product_release_id)
        gate = self.gate_repository.get_or_404_by_product_release_id(product_release_id)

        if gate.status == ReleaseGateWorkflowStatus.approved:
            raise ConflictException("Gate is approved and frozen. Dependencies cannot be modified.")

        prereq_link = self.db.query(ReleaseGateItemPrerequisite).filter(
            ReleaseGateItemPrerequisite.dependent_item_id == dependent_item_id,
            ReleaseGateItemPrerequisite.prerequisite_item_id == prerequisite_item_id,
        ).first()

        if prereq_link is None:
            raise NotFoundException("Prerequisite relationship not found.")

        dependent = next((item for item in gate.items if item.id == dependent_item_id), None)
        prerequisite = next((item for item in gate.items if item.id == prerequisite_item_id), None)

        self.db.delete(prereq_link)
        self.db.flush()
        self.db.refresh(gate)
        self._refresh_gate_status(gate)

        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="release_gate.prerequisite_removed",
            entity_type=EntityType.product_release,
            entity_id=product_release_id,
            status=AuditStatus.success,
            details_json={
                "action": "remove_gate_item_prerequisite",
                "product_release_id": str(product_release_id),
                "dependent_item_id": str(dependent_item_id),
                "dependent_item_title": dependent.title if dependent else None,
                "prerequisite_item_id": str(prerequisite_item_id),
                "prerequisite_item_title": prerequisite.title if prerequisite else None,
            },
        )
        self.db.commit()
        return self._detail_payload(release, gate)

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
                "bundle_sha256": gate.bundle_sha256,
                "bundle_generated_at": gate.bundle_generated_at,
                "snapshot_json": gate.snapshot_json,
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
                        "prerequisites": [
                            {
                                "id": prereq.id,
                                "code": prereq.code,
                                "title": prereq.title,
                                "status": prereq.status,
                            }
                            for prereq in item.prerequisites
                        ],
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
