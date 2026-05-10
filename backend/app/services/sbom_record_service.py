from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, NotFoundException
from app.models.enums import AuditStatus, EntityType
from app.models.sbom_record import SbomRecord
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.sbom_record_repository import SbomRecordRepository
from app.schemas.sbom_record import SbomRecordCreate, SbomRecordRead, SbomRecordUpdate
from app.models.enums import SbomFormat
from app.services import sbom_analyzer


class SbomRecordService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SbomRecordRepository(db)
        self.release_repository = ProductReleaseRepository(db)

    def list_sbom_records(
        self,
        *,
        product_release_id: UUID | None = None,
        product_id: UUID | None = None,
    ) -> list[SbomRecordRead]:
        records = self.repository.list_all(
            product_release_id=product_release_id,
            product_id=product_id,
        )
        return [SbomRecordRead.model_validate(r) for r in records]

    def get_sbom_record(self, sbom_id: UUID) -> SbomRecordRead:
        return SbomRecordRead.model_validate(self.repository.get_or_404(sbom_id))

    def create_sbom_record(self, payload: SbomRecordCreate, actor: object) -> SbomRecordRead:
        release = self.release_repository.get_or_404(payload.product_release_id)

        data = payload.model_dump()
        # Auto-derive component_count if not supplied but components_json is provided.
        if data.get("component_count") is None and data.get("components_json"):
            data["component_count"] = len(data["components_json"])

        record = SbomRecord(**data)
        try:
            self.repository.add(record)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="sbom_record.created",
                entity_type=EntityType.sbom_record,
                entity_id=record.id,
                status=AuditStatus.success,
                details_json={
                    "product_release_id": str(record.product_release_id),
                    "product_id": str(release.product_id),
                    "format": record.format,
                    "component_count": record.component_count,
                },
            )
            self.db.commit()
            self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create SBOM record") from exc
        return SbomRecordRead.model_validate(record)

    def update_sbom_record(
        self, sbom_id: UUID, payload: SbomRecordUpdate, actor: object
    ) -> SbomRecordRead:
        record = self.repository.get_or_404(sbom_id)
        release = self.release_repository.get_or_404(record.product_release_id)
        updates = payload.model_dump(exclude_unset=True)

        # Keep component_count in sync when components_json is updated.
        if "components_json" in updates and updates.get("component_count") is None:
            updates["component_count"] = len(updates["components_json"])

        for field, value in updates.items():
            setattr(record, field, value)
        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="sbom_record.updated",
                entity_type=EntityType.sbom_record,
                entity_id=record.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(release.product_id),
                    "updated_fields": sorted(updates.keys()),
                },
            )
            self.db.commit()
            self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to update SBOM record") from exc
        return SbomRecordRead.model_validate(record)

    def upload_and_analyze(
        self,
        *,
        product_release_id: UUID,
        sbom_content: str,
        file_name: str | None,
        notes: str | None,
        actor: object,
    ) -> SbomRecordRead:
        """Create a new SBOM record from raw file content, running sbom-tools analysis."""
        release = self.release_repository.get_or_404(product_release_id)

        # Find previous SBOM for this release to enable diff analysis.
        existing = self.repository.list_all(product_release_id=product_release_id)
        previous_content = existing[0].sbom_content if existing and existing[0].sbom_content else None

        findings = sbom_analyzer.analyze(sbom_content, previous_content=previous_content)
        quality_score = findings.pop("quality_score", None)

        # Parse SBOM document to populate structured metadata fields.
        meta = sbom_analyzer.parse_metadata(sbom_content)

        # Convert ISO-8601 string to datetime if present.
        generated_at_dt = None
        if meta.generated_at:
            from datetime import datetime, timezone
            try:
                generated_at_dt = datetime.fromisoformat(
                    meta.generated_at.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        record = SbomRecord(
            product_release_id=product_release_id,
            file_name=file_name,
            notes=notes,
            sbom_content=sbom_content,
            quality_score=quality_score,
            analysis_findings=findings,
            # Metadata extracted from the SBOM document itself
            format=SbomFormat(meta.format) if meta.format else SbomFormat.cyclonedx,
            spec_version=meta.spec_version,
            tool_name=meta.tool_name,
            tool_version=meta.tool_version,
            generated_at=generated_at_dt,
            component_count=meta.component_count,
            components_json=meta.components_json or [],
        )
        try:
            self.repository.add(record)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="sbom_record.uploaded",
                entity_type=EntityType.sbom_record,
                entity_id=record.id,
                status=AuditStatus.success,
                details_json={
                    "product_release_id": str(product_release_id),
                    "product_id": str(release.product_id),
                    "quality_score": quality_score,
                    "file_name": file_name,
                },
            )
            self.db.commit()
            self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create SBOM record") from exc
        return SbomRecordRead.model_validate(record)

    def reanalyze(self, sbom_id: UUID, actor: object) -> SbomRecordRead:
        """Re-run sbom-tools analysis on a stored SBOM record."""
        record = self.repository.get_or_404(sbom_id)
        if not record.sbom_content:
            raise NotFoundException("No stored SBOM content available for re-analysis")

        findings = sbom_analyzer.analyze(record.sbom_content)
        quality_score = findings.pop("quality_score", None)

        # Re-parse metadata so existing records pick up all structured fields.
        meta = sbom_analyzer.parse_metadata(record.sbom_content)
        generated_at_dt = None
        if meta.generated_at:
            from datetime import datetime
            try:
                generated_at_dt = datetime.fromisoformat(
                    meta.generated_at.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        record.quality_score = quality_score
        record.analysis_findings = findings
        record.format = SbomFormat(meta.format) if meta.format else record.format
        record.spec_version = meta.spec_version or record.spec_version
        record.tool_name = meta.tool_name or record.tool_name
        record.tool_version = meta.tool_version or record.tool_version
        if generated_at_dt:
            record.generated_at = generated_at_dt
        if meta.component_count is not None:
            record.component_count = meta.component_count
        if meta.components_json:
            record.components_json = meta.components_json
        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="sbom_record.reanalyzed",
                entity_type=EntityType.sbom_record,
                entity_id=record.id,
                status=AuditStatus.success,
                details_json={"quality_score": quality_score},
            )
            self.db.commit()
            self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to save analysis results") from exc
        return SbomRecordRead.model_validate(record)

    def delete_sbom_record(self, sbom_id: UUID, actor: object) -> None:
        record = self.repository.get_or_404(sbom_id)
        release = self.release_repository.get_or_404(record.product_release_id)
        self.repository.delete(record)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="sbom_record.deleted",
            entity_type=EntityType.sbom_record,
            entity_id=sbom_id,
            status=AuditStatus.success,
            details_json={"product_id": str(release.product_id), "format": record.format},
        )
        self.db.commit()
