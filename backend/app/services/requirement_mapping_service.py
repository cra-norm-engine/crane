from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.annex_i_catalog import sync_annex_i_requirements
from app.core.exceptions import AppException
from app.models.audit_log_event import AuditLogEvent
from app.models.enums import (
    AuditActionType,
    AuditStatus,
    EntityType,
    RequirementApplicabilityDecision,
)
from app.models.requirement_mapping import (
    ProductRequirementDecision,
    RequirementMapping,
    RequirementMappingArtifactLink,
)
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.annex_requirement_repository import AnnexRequirementRepository
from app.repositories.requirement_mapping_repository import RequirementMappingRepository
from app.repositories.risk_item_repository import RiskItemRepository
from app.schemas.annex_matrix import ProductRequirementDecisionUpdate, ProductRequirementMatrixRowRead
from app.schemas.requirement_mapping import RequirementMappingCreate, RequirementMappingUpdate

logger = logging.getLogger(__name__)


class RequirementMappingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.requirement_mapping_repository = RequirementMappingRepository(db)
        self.annex_requirement_repository = AnnexRequirementRepository(db)
        self.risk_item_repository = RiskItemRepository(db)
        self.artifact_repository = ArtifactRepository(db)

    def _artifact_links_available(self) -> bool:
        return self.requirement_mapping_repository.artifact_links_available()

    def list(
        self,
        *,
        risk_item_id: UUID | None = None,
        annex_requirement_id: UUID | None = None,
        release_id: UUID | None = None,
        matrix: bool = False,
    ) -> list[RequirementMapping]:
        sync_annex_i_requirements(self.db)
        self.db.flush()
        if release_id is not None:
            return list(self.requirement_mapping_repository.list_by_release(release_id))
        if matrix:
            return list(self.requirement_mapping_repository.list_for_matrix())
        if risk_item_id is not None:
            return list(self.requirement_mapping_repository.list_by_risk_item(risk_item_id))
        if annex_requirement_id is not None:
            return list(self.requirement_mapping_repository.list_by_annex_requirement(annex_requirement_id))
        return list(self.requirement_mapping_repository.list_for_matrix())

    def release_matrix(self, release_id: UUID) -> list[ProductRequirementMatrixRowRead]:
        """Build the full requirement matrix for a specific product release."""
        sync_annex_i_requirements(self.db)
        self.db.flush()

        artifact_traceability_available = self._artifact_links_available()
        requirements = list(self.annex_requirement_repository.list_active())
        mappings = self.requirement_mapping_repository.list_by_release(release_id)
        decisions = self.requirement_mapping_repository.list_release_decisions(release_id)

        mappings_by_requirement: dict[UUID, list[RequirementMapping]] = {}
        decisions_by_requirement = {
            decision.annex_requirement_id: decision for decision in decisions
        }
        for mapping in mappings:
            mappings_by_requirement.setdefault(mapping.annex_requirement_id, []).append(mapping)

        rows: list[ProductRequirementMatrixRowRead] = []
        for requirement in requirements:
            grouped_mappings = mappings_by_requirement.get(requirement.id, [])
            decision = decisions_by_requirement.get(requirement.id)
            applicability_decision = (
                decision.applicability_decision
                if decision is not None
                else RequirementApplicabilityDecision.undecided
            )
            rows.append(
                ProductRequirementMatrixRowRead(
                    annex_requirement=requirement,
                    artifact_traceability_available=artifact_traceability_available,
                    applicability_decision=applicability_decision,
                    applicability_rationale=decision.rationale if decision is not None else None,
                    mapping_ids=[mapping.id for mapping in grouped_mappings],
                    trace_records=[self._matrix_mapping_payload(mapping) for mapping in grouped_mappings],
                    risk_items=self._unique_risk_items(grouped_mappings),
                    artifacts=self._unique_artifacts(grouped_mappings),
                    engineering_requirement_refs=sorted(
                        {
                            mapping.engineering_requirement_ref.strip()
                            for mapping in grouped_mappings
                            if mapping.engineering_requirement_ref and mapping.engineering_requirement_ref.strip()
                        }
                    ),
                    sdl_activities=sorted(
                        {mapping.sdl_activity for mapping in grouped_mappings},
                        key=lambda value: value.value,
                    ),
                    notes=sorted(
                        {
                            mapping.evidence_summary.strip()
                            for mapping in grouped_mappings
                            if mapping.evidence_summary and mapping.evidence_summary.strip()
                        }
                    ),
                    overall_status=self._aggregate_status(grouped_mappings),
                    applicability=self._applicability(applicability_decision),
                    traceability_strength=self._traceability_strength(grouped_mappings),
                )
            )
        return rows

    def update_release_requirement_decision(
        self,
        release_id: UUID,
        annex_requirement_id: UUID,
        payload: ProductRequirementDecisionUpdate,
        *,
        actor_user_id: UUID | None,
    ) -> ProductRequirementDecision:
        requirement = self.annex_requirement_repository.get_by_id(annex_requirement_id)
        if requirement is None:
            raise ValueError("Annex requirement not found.")

        existing = next(
            (
                decision
                for decision in self.requirement_mapping_repository.list_release_decisions(release_id)
                if decision.annex_requirement_id == annex_requirement_id
            ),
            None,
        )
        if existing is None:
            existing = ProductRequirementDecision(
                product_release_id=release_id,
                annex_requirement_id=annex_requirement_id,
            )
            self.db.add(existing)

        existing.applicability_decision = payload.applicability_decision
        existing.rationale = payload.rationale
        self.db.flush()

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.update,
            entity_type=EntityType.requirement_mapping,
            entity_id=annex_requirement_id,
            status=AuditStatus.success,
            details_json={
                "action": "update_release_requirement_decision",
                "release_id": str(release_id),
                "annex_requirement_id": str(annex_requirement_id),
                "applicability_decision": payload.applicability_decision.value,
                "rationale": payload.rationale,
            },
        )
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def copy_decisions_from_parent(
        self,
        new_release_id: UUID,
        parent_release_id: UUID,
        *,
        actor_user_id: UUID | None,
    ) -> int:
        """Copy applicability decisions from a parent release to a newly created release."""
        copied = self.requirement_mapping_repository.copy_decisions_from_release(
            source_release_id=parent_release_id,
            target_release_id=new_release_id,
        )
        if copied:
            self._write_audit_log(
                actor_user_id=actor_user_id,
                action_type=AuditActionType.create,
                entity_type=EntityType.requirement_mapping,
                entity_id=new_release_id,
                status=AuditStatus.success,
                details_json={
                    "action": "copy_decisions_from_parent",
                    "new_release_id": str(new_release_id),
                    "parent_release_id": str(parent_release_id),
                    "decisions_copied": len(copied),
                },
            )
            self.db.commit()
        return len(copied)

    def get(self, mapping_id: UUID) -> RequirementMapping:
        mapping = self.requirement_mapping_repository.get_with_relations(mapping_id)
        if mapping is None:
            raise ValueError("Requirement mapping not found.")
        return mapping

    def create(
        self,
        payload: RequirementMappingCreate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RequirementMapping:
        annex_requirement = self.annex_requirement_repository.get_by_id(payload.annex_requirement_id)
        if annex_requirement is None:
            raise ValueError("Annex requirement not found.")

        if payload.risk_item_id is not None:
            risk_item = self.risk_item_repository.get_by_id(payload.risk_item_id)
            if risk_item is None:
                raise ValueError("Risk item not found.")

        mapping = RequirementMapping(
            product_release_id=payload.product_release_id,
            risk_item_id=payload.risk_item_id,
            annex_requirement_id=payload.annex_requirement_id,
            engineering_requirement_ref=payload.engineering_requirement_ref,
            sdl_activity=payload.sdl_activity,
            implementation_status=payload.implementation_status,
            evidence_summary=payload.evidence_summary,
        )
        mapping = self.requirement_mapping_repository.add(mapping)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.create,
            entity_type=EntityType.requirement_mapping,
            entity_id=mapping.id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=self._snapshot(mapping),
        )

        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def update(
        self,
        mapping_id: UUID,
        payload: RequirementMappingUpdate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RequirementMapping:
        mapping = self.get(mapping_id)
        before = self._snapshot(mapping)

        update_data = payload.model_dump(exclude_unset=True)

        if "annex_requirement_id" in update_data and update_data["annex_requirement_id"] is not None:
            annex_requirement = self.annex_requirement_repository.get_by_id(update_data["annex_requirement_id"])
            if annex_requirement is None:
                raise ValueError("Annex requirement not found.")

        if "risk_item_id" in update_data and update_data["risk_item_id"] is not None:
            risk_item = self.risk_item_repository.get_by_id(update_data["risk_item_id"])
            if risk_item is None:
                raise ValueError("Risk item not found.")

        for field_name, value in update_data.items():
            setattr(mapping, field_name, value)

        self.db.flush()
        self.db.refresh(mapping)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.update,
            entity_type=EntityType.requirement_mapping,
            entity_id=mapping.id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "before": before,
                "after": self._snapshot(mapping),
                "updated_fields": sorted(update_data.keys()),
            },
        )

        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def delete(
        self,
        mapping_id: UUID,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        mapping = self.get(mapping_id)
        before = self._snapshot(mapping)

        self.requirement_mapping_repository.delete(mapping)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.delete,
            entity_type=EntityType.requirement_mapping,
            entity_id=mapping_id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={"deleted": before},
        )

        self.db.commit()

    def attach_artifact(
        self,
        mapping_id: UUID,
        artifact_id: UUID,
        *,
        actor_user_id: UUID | None,
    ) -> dict[str, Any]:
        if not self._artifact_links_available():
            raise AppException(
                "Artifact traceability links are not available yet. Apply the latest database migration and retry."
            )
        mapping = self.get(mapping_id)
        artifact = self.artifact_repository.get_or_404(artifact_id)

        existing = self.db.scalar(
            select(RequirementMappingArtifactLink).where(
                RequirementMappingArtifactLink.requirement_mapping_id == mapping_id,
                RequirementMappingArtifactLink.artifact_id == artifact_id,
            )
        )
        if existing is None:
            self.db.add(
                RequirementMappingArtifactLink(
                    requirement_mapping_id=mapping_id,
                    artifact_id=artifact_id,
                )
            )
            self.db.flush()

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.update,
            entity_type=EntityType.requirement_mapping,
            entity_id=mapping.id,
            status=AuditStatus.success,
            details_json={
                "action": "attach_artifact",
                "mapping_id": str(mapping.id),
                "artifact_id": str(artifact.id),
            },
        )
        self.db.commit()
        return self._matrix_mapping_payload(self.get(mapping_id))

    def detach_artifact(
        self,
        mapping_id: UUID,
        artifact_id: UUID,
        *,
        actor_user_id: UUID | None,
    ) -> dict[str, Any]:
        if not self._artifact_links_available():
            raise AppException(
                "Artifact traceability links are not available yet. Apply the latest database migration and retry."
            )
        mapping = self.get(mapping_id)
        link = self.db.scalar(
            select(RequirementMappingArtifactLink).where(
                RequirementMappingArtifactLink.requirement_mapping_id == mapping_id,
                RequirementMappingArtifactLink.artifact_id == artifact_id,
            )
        )
        if link is not None:
            self.db.delete(link)
            self.db.flush()

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.update,
            entity_type=EntityType.requirement_mapping,
            entity_id=mapping.id,
            status=AuditStatus.success,
            details_json={
                "action": "detach_artifact",
                "mapping_id": str(mapping.id),
                "artifact_id": str(artifact_id),
            },
        )
        self.db.commit()
        return self._matrix_mapping_payload(self.get(mapping_id))

    def _snapshot(self, mapping: RequirementMapping) -> dict[str, Any]:
        return {
            "id": str(mapping.id),
            "product_release_id": str(mapping.product_release_id),
            "risk_item_id": str(mapping.risk_item_id) if mapping.risk_item_id else None,
            "annex_requirement_id": str(mapping.annex_requirement_id),
            "engineering_requirement_ref": mapping.engineering_requirement_ref,
            "sdl_activity": mapping.sdl_activity,
            "implementation_status": mapping.implementation_status.value,
            "evidence_summary": mapping.evidence_summary,
        }

    def _matrix_mapping_payload(self, mapping: RequirementMapping) -> dict[str, Any]:
        artifact_links = mapping.artifact_links if self._artifact_links_available() else []
        return {
            **self._snapshot(mapping),
            "created_at": mapping.created_at,
            "updated_at": mapping.updated_at,
            "risk_item": mapping.risk_item,
            "artifacts": [self._artifact_payload(link.artifact) for link in artifact_links if link.artifact],
        }

    def _artifact_payload(self, artifact) -> dict[str, Any]:
        revisions = list(artifact.revisions)
        latest_revision = revisions[0] if revisions else None
        return {
            "id": artifact.id,
            "title": artifact.title,
            "description": artifact.description,
            "artifact_type": artifact.artifact_type,
            "created_by_user_id": artifact.created_by_user_id,
            "created_by_user": getattr(artifact, "created_by_user", None),
            "created_at": artifact.created_at,
            "updated_at": artifact.updated_at,
            "latest_revision": latest_revision,
            "linked_product_ids": [link.product_id for link in artifact.product_links],
        }

    def _unique_risk_items(self, mappings: list[RequirementMapping]) -> list[Any]:
        unique: dict[UUID, Any] = {}
        for mapping in mappings:
            if mapping.risk_item is not None:
                unique[mapping.risk_item.id] = mapping.risk_item
        return list(unique.values())

    def _unique_artifacts(self, mappings: list[RequirementMapping]) -> list[dict[str, Any]]:
        if not self._artifact_links_available():
            return []
        unique: dict[UUID, dict[str, Any]] = {}
        for mapping in mappings:
            for link in mapping.artifact_links:
                if link.artifact is not None:
                    unique[link.artifact.id] = self._artifact_payload(link.artifact)
        return list(unique.values())

    def _aggregate_status(
        self, mappings: list[RequirementMapping]
    ) -> Any:
        if not mappings:
            return None
        statuses = {mapping.implementation_status for mapping in mappings}
        enum_cls = type(next(iter(statuses)))
        applicable_statuses = {status for status in statuses if status != enum_cls.not_applicable}
        if not applicable_statuses:
            return next(iter(statuses))
        if applicable_statuses == {enum_cls.verified}:
            return enum_cls.verified
        if applicable_statuses.issubset(
            {
                enum_cls.implemented,
                enum_cls.verified,
            }
        ):
            return enum_cls.implemented
        if enum_cls.in_progress in applicable_statuses:
            return enum_cls.in_progress
        return enum_cls.planned

    def _applicability(self, decision: RequirementApplicabilityDecision) -> str:
        if decision == RequirementApplicabilityDecision.not_applicable:
            return "not_applicable"
        if decision == RequirementApplicabilityDecision.applicable:
            return "applicable"
        return "needs_decision"

    def _traceability_strength(self, mappings: list[RequirementMapping]) -> str:
        if not mappings:
            return "missing"
        has_risks = any(mapping.risk_item is not None for mapping in mappings)
        has_artifacts = self._artifact_links_available() and any(mapping.artifact_links for mapping in mappings)
        if has_risks and has_artifacts:
            return "complete"
        if has_risks or has_artifacts:
            return "partial"
        return "weak"

    def _write_audit_log(
        self,
        *,
        actor_user_id: UUID | None,
        action_type: AuditActionType,
        entity_type: EntityType,
        entity_id: UUID | None,
        status: AuditStatus,
        details_json: dict[str, Any],
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        event = AuditLogEvent(
            actor_user_id=actor_user_id,
            action_type=action_type.value,
            entity_type=entity_type.value,
            entity_id=entity_id,
            status=status.value,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=details_json,
        )
        event.set_checksum()
        self.db.add(event)
        self.db.flush()
