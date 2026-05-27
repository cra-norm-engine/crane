from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, NotFoundException
from app.models.enums import AuditStatus, EntityType, RiskAssessmentStatus
from app.models.evidence_item import EvidenceItem
from app.models.requirement_mapping import RequirementMapping
from app.models.risk_assessment import RiskAssessment
from app.models.risk_item import RiskItem
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.repositories.risk_item_repository import RiskItemRepository
from app.repositories.user_repository import UserRepository
from app.schemas.risk_assessment import (
    RiskAssessmentApproveRequest,
    RiskAssessmentCreate,
    RiskAssessmentDetailRead,
    RiskAssessmentDuplicateVersionRequest,
    RiskAssessmentRead,
    RiskAssessmentUpdate,
    RiskAssessmentRejectRequest,
)


class RiskAssessmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.risk_assessment_repository = RiskAssessmentRepository(db)
        self.risk_item_repository = RiskItemRepository(db)
        self.product_repository = ProductRepository(db)
        self.product_release_repository = ProductReleaseRepository(db)
        self.user_repository = UserRepository(db)

    def list(
        self,
        *,
        product_id: UUID | None = None,
        product_release_id: UUID | None = None,
    ) -> list[RiskAssessmentRead]:
        if product_id is None and product_release_id is None:
            assessments = self.risk_assessment_repository.list_all()
            return [RiskAssessmentRead.model_validate(item) for item in assessments]

        if product_release_id is not None:
            assessments = self.risk_assessment_repository.list_by_product_release(product_release_id)
            return [RiskAssessmentRead.model_validate(item) for item in assessments]

        if product_id is not None:
            assessments = self.risk_assessment_repository.list_by_product(product_id)
            return [RiskAssessmentRead.model_validate(item) for item in assessments]

    def get(self, assessment_id: UUID) -> RiskAssessmentDetailRead:
        assessment = self.risk_assessment_repository.get_with_relations(assessment_id)
        if assessment is None:
            raise NotFoundException("Risk assessment not found")

        return RiskAssessmentDetailRead.model_validate(
            {
                **RiskAssessmentRead.model_validate(assessment).model_dump(),
                "risk_items_count": len(assessment.risk_items),
                "evidence_items_count": len(assessment.evidence_items),
                "risk_items": assessment.risk_items,
                "evidence_items": assessment.evidence_items,
            }
        )

    def create(
        self,
        payload: RiskAssessmentCreate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RiskAssessmentRead:
        self.product_repository.get_or_404(payload.product_id)

        if payload.product_release_id is not None:
            self.product_release_repository.get_or_404(payload.product_release_id)

        if self.user_repository.get_by_id(payload.owner_user_id) is None:
            raise NotFoundException("Owner user not found")

        # Auto-generate system_version: find the maximum system_version for this product and increment
        from sqlalchemy import select
        max_system_version = self.db.scalar(
            select(func.max(RiskAssessment.system_version)).where(RiskAssessment.product_id == payload.product_id)
        ) or 0
        next_system_version = max_system_version + 1

        # Create assessment with auto-generated system_version
        assessment = RiskAssessment(
            product_id=payload.product_id,
            product_release_id=payload.product_release_id,
            title=payload.title,
            user_version=payload.user_version,
            system_version=next_system_version,
            status=payload.status,
            methodology=payload.methodology,
            summary=payload.summary,
            owner_user_id=payload.owner_user_id,
            approved_at=None,
        )

        if assessment.status == RiskAssessmentStatus.approved:
            assessment.approved_at = datetime.now(UTC)

        try:
            assessment = self.risk_assessment_repository.add(assessment)

            create_audit_event(
                self.db,
                actor_user_id=actor_user_id,
                action_type="risk_assessment.created",
                entity_type=EntityType.risk_assessment.value,
                entity_id=assessment.id,
                status=AuditStatus.success.value,
                ip_address=ip_address,
                user_agent=user_agent,
                details_json={
                    "product_id": str(assessment.product_id),
                    "product_release_id": str(assessment.product_release_id) if assessment.product_release_id else None,
                    "title": assessment.title,
                    "system_version": assessment.system_version,
                    "system_version_label": f"v{assessment.system_version}",
                    "user_version": assessment.user_version,
                    "assessment_status": assessment.status.value,
                },
            )
            self.db.commit()
            self.db.refresh(assessment)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create risk assessment due to uniqueness conflict") from exc

        return RiskAssessmentRead.model_validate(assessment)

    def update(
        self,
        assessment_id: UUID,
        payload: RiskAssessmentUpdate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RiskAssessmentRead:
        assessment = self.risk_assessment_repository.get_or_404(assessment_id)
        before = self._assessment_snapshot(assessment)
        updates = payload.model_dump(exclude_unset=True)

        if "product_release_id" in updates and updates["product_release_id"] is not None:
            self.product_release_repository.get_or_404(updates["product_release_id"])

        if "owner_user_id" in updates and updates["owner_user_id"] is not None:
            if self.user_repository.get_by_id(updates["owner_user_id"]) is None:
                raise NotFoundException("Owner user not found")

        # system_version is immutable and cannot be updated from the client
        if "system_version" in updates:
            raise ConflictException("system_version cannot be updated; it is auto-generated and immutable")

        for field_name, value in updates.items():
            setattr(assessment, field_name, value)

        if assessment.status != RiskAssessmentStatus.approved:
            assessment.approved_at = None
        elif assessment.approved_at is None:
            assessment.approved_at = datetime.now(UTC)

        try:
            self.db.flush()
            self.db.refresh(assessment)

            create_audit_event(
                self.db,
                actor_user_id=actor_user_id,
                action_type="risk_assessment.updated",
                entity_type=EntityType.risk_assessment.value,
                entity_id=assessment.id,
                status=AuditStatus.success.value,
                ip_address=ip_address,
                user_agent=user_agent,
                details_json={
                    "product_id": str(assessment.product_id),
                    "product_release_id": str(assessment.product_release_id) if assessment.product_release_id else None,
                    "title": assessment.title,
                    "system_version": assessment.system_version,
                    "system_version_label": f"v{assessment.system_version}",
                    "user_version": assessment.user_version,
                    "before": before,
                    "after": self._assessment_snapshot(assessment),
                    "updated_fields": sorted(updates.keys()),
                },
            )

            self.db.commit()
            self.db.refresh(assessment)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to update risk assessment due to uniqueness conflict") from exc

        return RiskAssessmentRead.model_validate(assessment)

    def approve(
        self,
        assessment_id: UUID,
        payload: RiskAssessmentApproveRequest,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RiskAssessmentRead:
        assessment = self.risk_assessment_repository.get_or_404(assessment_id)
        before = self._assessment_snapshot(assessment)

        assessment.status = RiskAssessmentStatus.approved
        assessment.approved_at = payload.approved_at or datetime.now(UTC)

        self.db.flush()
        self.db.refresh(assessment)

        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="risk_assessment.approved",
            entity_type=EntityType.risk_assessment.value,
            entity_id=assessment.id,
            status=AuditStatus.success.value,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "product_id": str(assessment.product_id),
                "product_release_id": str(assessment.product_release_id) if assessment.product_release_id else None,
                "title": assessment.title,
                "system_version": assessment.system_version,
                "system_version_label": f"v{assessment.system_version}",
                "user_version": assessment.user_version,
                "before": before,
                "after": self._assessment_snapshot(assessment),
                "approved_at": assessment.approved_at.isoformat() if assessment.approved_at else None,
            },
        )

        self.db.commit()
        self.db.refresh(assessment)
        return RiskAssessmentRead.model_validate(assessment)

    def submit_for_review(
        self,
        assessment_id: UUID,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RiskAssessmentRead:
        """
        Transition a risk assessment from draft → in_review.

        Only assessments currently in 'draft' status may be submitted.
        Clears any prior rejection_reason so the reviewer sees a clean slate.
        Emits an audit event for traceability.
        """
        assessment = self.risk_assessment_repository.get_or_404(assessment_id)

        if assessment.status != RiskAssessmentStatus.draft:
            raise ConflictException("Only draft assessments can be submitted for review.")

        before = self._assessment_snapshot(assessment)
        assessment.status = RiskAssessmentStatus.in_review
        assessment.rejection_reason = None  # clear any previous rejection text

        self.db.flush()
        self.db.refresh(assessment)

        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="risk_assessment.submitted_for_review",
            entity_type=EntityType.risk_assessment.value,
            entity_id=assessment.id,
            status=AuditStatus.success.value,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "product_id": str(assessment.product_id),
                "title": assessment.title,
                "system_version": assessment.system_version,
                "system_version_label": f"v{assessment.system_version}",
                "user_version": assessment.user_version,
                "before": before,
                "after": self._assessment_snapshot(assessment),
            },
        )

        self.db.commit()
        self.db.refresh(assessment)
        return RiskAssessmentRead.model_validate(assessment)

    def reject_assessment(
        self,
        assessment_id: UUID,
        reason: str,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RiskAssessmentRead:
        """
        Transition a risk assessment from in_review → draft with a rejection reason.

        Only assessments currently 'in_review' may be rejected.  The rejection
        reason is persisted so the owner can see the reviewer's feedback.
        Emits an audit event for traceability.
        """
        assessment = self.risk_assessment_repository.get_or_404(assessment_id)

        if assessment.status != RiskAssessmentStatus.in_review:
            raise ConflictException("Only assessments under review can be rejected.")

        before = self._assessment_snapshot(assessment)
        assessment.status = RiskAssessmentStatus.draft
        assessment.rejection_reason = reason

        self.db.flush()
        self.db.refresh(assessment)

        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="risk_assessment.rejected",
            entity_type=EntityType.risk_assessment.value,
            entity_id=assessment.id,
            status=AuditStatus.success.value,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "product_id": str(assessment.product_id),
                "title": assessment.title,
                "system_version": assessment.system_version,
                "system_version_label": f"v{assessment.system_version}",
                "user_version": assessment.user_version,
                "rejection_reason": reason,
                "before": before,
                "after": self._assessment_snapshot(assessment),
            },
        )

        self.db.commit()
        self.db.refresh(assessment)
        return RiskAssessmentRead.model_validate(assessment)

    def duplicate_version(
        self,
        assessment_id: UUID,
        payload: RiskAssessmentDuplicateVersionRequest,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RiskAssessmentRead:
        source = self.risk_assessment_repository.get_with_relations(assessment_id)
        if source is None:
            raise NotFoundException("Risk assessment not found")

        if payload.product_release_id is not None:
            self.product_release_repository.get_or_404(payload.product_release_id)

        new_owner_user_id = payload.owner_user_id or source.owner_user_id
        if self.user_repository.get_by_id(new_owner_user_id) is None:
            raise NotFoundException("Owner user not found")

        # Auto-generate system_version for the duplicate: find max and increment
        from sqlalchemy import select
        max_system_version = self.db.scalar(
            select(func.max(RiskAssessment.system_version)).where(RiskAssessment.product_id == source.product_id)
        ) or 0
        next_system_version = max_system_version + 1

        duplicate_status = (
            RiskAssessmentStatus.draft
            if payload.reset_status_to_draft
            else source.status
        )
        duplicate_approved_at = None if payload.reset_status_to_draft else source.approved_at

        duplicate = RiskAssessment(
            product_id=source.product_id,
            product_release_id=payload.product_release_id if payload.product_release_id is not None else source.product_release_id,
            title=payload.title or source.title,
            user_version=payload.user_version,
            system_version=next_system_version,
            status=duplicate_status,
            methodology=source.methodology,
            summary=payload.summary if payload.summary is not None else source.summary,
            owner_user_id=new_owner_user_id,
            approved_at=duplicate_approved_at,
        )

        copied_risk_items = 0
        copied_requirement_mappings = 0
        copied_evidence_items = 0

        try:
            duplicate = self.risk_assessment_repository.add(duplicate)

            source_item_id_to_duplicate_item_id: dict[UUID, UUID] = {}

            if payload.copy_risk_items:
                for risk_item in source.risk_items:
                    duplicated_risk_item = RiskItem(
                        risk_assessment_id=duplicate.id,
                        title=risk_item.title,
                        description=risk_item.description,
                        threat_scenario=risk_item.threat_scenario,
                        asset_affected=risk_item.asset_affected,
                        likelihood=risk_item.likelihood,
                        impact=risk_item.impact,
                        risk_level=risk_item.risk_level,
                        mitigation_plan=risk_item.mitigation_plan,
                        residual_risk_level=risk_item.residual_risk_level,
                        status=risk_item.status,
                        owner_user_id=risk_item.owner_user_id,
                    )
                    duplicated_risk_item = self.risk_item_repository.add(duplicated_risk_item)
                    source_item_id_to_duplicate_item_id[risk_item.id] = duplicated_risk_item.id
                    copied_risk_items += 1

                    if payload.copy_requirement_mappings:
                        for mapping in risk_item.requirement_mappings:
                            duplicated_mapping = RequirementMapping(
                                risk_item_id=duplicated_risk_item.id,
                                annex_requirement_id=mapping.annex_requirement_id,
                                engineering_requirement_ref=mapping.engineering_requirement_ref,
                                sdl_activity=mapping.sdl_activity,
                                implementation_status=mapping.implementation_status,
                                evidence_summary=mapping.evidence_summary,
                            )
                            self.db.add(duplicated_mapping)
                            self.db.flush()
                            copied_requirement_mappings += 1

            if payload.copy_evidence_links:
                for evidence_item in source.evidence_items:
                    duplicated_evidence = EvidenceItem(
                        product_release_id=evidence_item.product_release_id,
                        risk_assessment_id=duplicate.id,
                        requirement_mapping_id=None,
                        title=evidence_item.title,
                        description=evidence_item.description,
                        evidence_type=evidence_item.evidence_type,
                        file_path=evidence_item.file_path,
                        external_url=evidence_item.external_url,
                        uploaded_by_user_id=evidence_item.uploaded_by_user_id,
                    )
                    self.db.add(duplicated_evidence)
                    copied_evidence_items += 1

            self.db.flush()
            self.db.refresh(duplicate)

            create_audit_event(
                self.db,
                actor_user_id=actor_user_id,
                action_type="risk_assessment.duplicated",
                entity_type=EntityType.risk_assessment.value,
                entity_id=duplicate.id,
                status=AuditStatus.success.value,
                ip_address=ip_address,
                user_agent=user_agent,
                details_json={
                    "product_id": str(duplicate.product_id),
                    "product_release_id": str(duplicate.product_release_id) if duplicate.product_release_id else None,
                    "title": duplicate.title,
                    "system_version": duplicate.system_version,
                    "system_version_label": f"v{duplicate.system_version}",
                    "user_version": duplicate.user_version,
                    "source_assessment_id": str(source.id),
                    "source_system_version": source.system_version,
                    "source_system_version_label": f"v{source.system_version}",
                    "source_user_version": source.user_version,
                    "new_assessment_id": str(duplicate.id),
                    "new_system_version": duplicate.system_version,
                    "new_system_version_label": f"v{duplicate.system_version}",
                    "new_user_version": duplicate.user_version,
                    "copied_risk_items": copied_risk_items,
                    "copied_requirement_mappings": copied_requirement_mappings,
                    "copied_evidence_items": copied_evidence_items,
                    "new_product_release_id": str(duplicate.product_release_id) if duplicate.product_release_id else None,
                    "reset_status_to_draft": payload.reset_status_to_draft,
                },
            )

            self.db.commit()
            self.db.refresh(duplicate)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to duplicate risk assessment due to uniqueness conflict") from exc

        return RiskAssessmentRead.model_validate(duplicate)

    def delete(
        self,
        assessment_id: UUID,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        assessment = self.risk_assessment_repository.get_or_404(assessment_id)
        snapshot = self._assessment_snapshot(assessment)

        self.risk_assessment_repository.delete(assessment)

        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="risk_assessment.deleted",
            entity_type=EntityType.risk_assessment.value,
            entity_id=assessment.id,
            status=AuditStatus.success.value,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=snapshot,
        )

        self.db.commit()

    def _assessment_snapshot(self, assessment: RiskAssessment) -> dict[str, Any]:
        # Include approval-workflow fields so before/after diffs capture reviewer changes.
        return {
            "id": str(assessment.id),
            "product_id": str(assessment.product_id),
            "product_release_id": str(assessment.product_release_id) if assessment.product_release_id else None,
            "title": assessment.title,
            "system_version": assessment.system_version,
            "system_version_label": f"v{assessment.system_version}",
            "user_version": assessment.user_version,
            "status": assessment.status.value,
            "methodology": assessment.methodology,
            "summary": assessment.summary,
            "owner_user_id": str(assessment.owner_user_id),
            "approved_at": assessment.approved_at.isoformat() if assessment.approved_at else None,
            "reviewer_user_id": str(assessment.reviewer_user_id) if assessment.reviewer_user_id else None,
            "rejection_reason": assessment.rejection_reason,
        }
