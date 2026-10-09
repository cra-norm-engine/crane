# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.annex_i_catalog import sync_annex_i_requirements
from app.core.exceptions import (
    AppException,
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.annex_requirement import AnnexRequirement, ReleaseRequirementBaseline
from app.models.audit_log_event import AuditLogEvent
from app.models.enums import (
    AuditActionType,
    AuditStatus,
    EntityType,
    RequirementApplicabilityDecision,
    RequirementAssessmentStatus,
    RequirementProgressStatus,
)
from app.models.product import ProductRelease
from app.models.requirement_assessment import (
    ReleaseRequirementAssessment,
    ReleaseRequirementAssessmentSnapshot,
)
from app.models.requirement_mapping import (
    ProductRequirementDecision,
    RequirementMapping,
    RequirementMappingArtifactLink,
)
from app.repositories.annex_requirement_repository import AnnexRequirementRepository
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.requirement_mapping_repository import RequirementMappingRepository
from app.repositories.risk_item_repository import RiskItemRepository
from app.schemas.annex_matrix import (
    ProductRequirementDecisionUpdate,
    ProductRequirementMatrixRowRead,
    SupportingRequirementRead,
)
from app.schemas.annex_requirement import AnnexRequirementRead
from app.schemas.requirement_mapping import RequirementMappingCreate, RequirementMappingUpdate

logger = logging.getLogger(__name__)


def _validate_applicability_decision(
    is_mandatory: bool,
    decision: RequirementApplicabilityDecision,
    rationale: str | None,
) -> None:
    """Apply CRA applicability guardrails before persisting a decision."""
    if decision != RequirementApplicabilityDecision.not_applicable:
        return
    if is_mandatory:
        raise ValidationException("This requirement is mandatory and cannot be marked not applicable.")
    if not rationale or not rationale.strip():
        raise ValidationException(
            "A clear risk-based rationale is required for a non-applicable requirement."
        )


class RequirementMappingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.requirement_mapping_repository = RequirementMappingRepository(db)
        self.annex_requirement_repository = AnnexRequirementRepository(db)
        self.risk_item_repository = RiskItemRepository(db)
        self.artifact_repository = ArtifactRepository(db)

    def _artifact_links_available(self) -> bool:
        return self.requirement_mapping_repository.artifact_links_available()

    def _assert_not_locked(self, release_id: UUID) -> None:
        """Block writes when the release's requirement assessment is approved.

        After approval the assessment is immutable; the only way to change it is to
        reopen it (amendment), which is an append-only re-approval. Queries the
        assessment table directly to avoid a circular import with the assessment
        service.
        """
        stmt = select(ReleaseRequirementAssessment.status).where(
            ReleaseRequirementAssessment.product_release_id == release_id
        )
        status = self.db.scalar(stmt)
        if status == RequirementAssessmentStatus.approved:
            raise ConflictException(
                "Requirement assessment is approved and locked. "
                "Reopen it to make changes."
            )

    def _ensure_catalog_seeded(self) -> None:
        """Lazily seed the Annex I catalog only when it is empty.

        The catalog is normally synced once at application startup. Re-running the
        full sync on every read issued redundant writes (and a flush) on the hot
        path; here we only do work when the table has no active requirements.
        """
        if self.annex_requirement_repository.count_active() == 0:
            if sync_annex_i_requirements(self.db):
                self.db.commit()

    def list(
        self,
        *,
        risk_item_id: UUID | None = None,
        annex_requirement_id: UUID | None = None,
        release_id: UUID | None = None,
        matrix: bool = False,
    ) -> list[RequirementMapping]:
        self._ensure_catalog_seeded()
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
        """Read frozen approval proof, or build the editable release's selected demonstration."""
        self._ensure_catalog_seeded()
        assessment = self.db.scalar(select(ReleaseRequirementAssessment).where(
            ReleaseRequirementAssessment.product_release_id == release_id
        ))
        if assessment and assessment.status == RequirementAssessmentStatus.approved:
            snapshot = self.db.scalar(select(ReleaseRequirementAssessmentSnapshot).where(
                ReleaseRequirementAssessmentSnapshot.release_requirement_assessment_id == assessment.id,
                ReleaseRequirementAssessmentSnapshot.version == assessment.version,
            ))
            if snapshot:
                frozen_rows = []
                for stored_row in snapshot.snapshot_json["matrix"]:
                    row = dict(stored_row)
                    definition = dict(row["annex_requirement"])
                    essential = definition.get("source_identifier") == "CRA-ANNEX-I" or definition["code"].startswith("ANNEX-I-")
                    definition.setdefault("kind", "essential" if essential else "technical")
                    defaults = {"source_id": None, "source_identifier": "CRA-ANNEX-I" if essential else "Historical source",
                        "source_title": "CRA Annex I" if essential else "Source not recorded in this approval",
                        "clause_reference": None, "applicability_guidance": None, "verification_guidance": None,
                        "expected_evidence": None, "revision": 0, "status": "historical", "is_mandatory": False}
                    for key, value in defaults.items():
                        definition.setdefault(key, value)
                    row["annex_requirement"] = definition
                    if "finalized" not in row:
                        # Older approvals predate progress and explicit conclusions.
                        # Reconstruct only their original risk/evidence rule, not today's review.
                        applicable = row["applicability_decision"] == "applicable"
                        row["finalized"] = bool(row["risk_items"]) and (not applicable or bool(row["artifacts"])) and row["applicability_decision"] != "undecided"
                        row.setdefault("implementation_status", "validated" if applicable and row["finalized"] else "planned")
                        row["validation_notes"] = "Historical approval under the previous assessment workflow; detailed review was not recorded."
                    frozen_rows.append(ProductRequirementMatrixRowRead.model_validate(row))
                return frozen_rows

        baselines = list(self.db.scalars(select(ReleaseRequirementBaseline).where(
            ReleaseRequirementBaseline.product_release_id == release_id
        )))
        definitions = []
        for baseline in baselines:
            if baseline.requirement_snapshot:
                definitions.append(AnnexRequirementRead.model_validate(baseline.requirement_snapshot))
            else:
                requirement = self.annex_requirement_repository.get_by_id(baseline.requirement_id)
                if requirement:
                    definitions.append(AnnexRequirementRead.model_validate(requirement))
        if not definitions:
            definitions = [AnnexRequirementRead.model_validate(r) for r in self.annex_requirement_repository.list_active() if r.kind == "essential"]
        mappings = self.requirement_mapping_repository.list_by_release(release_id)
        decisions = {d.annex_requirement_id: d for d in self.requirement_mapping_repository.list_release_decisions(release_id)}
        grouped: dict[UUID, list[RequirementMapping]] = {}
        for mapping in mappings:
            grouped.setdefault(mapping.annex_requirement_id, []).append(mapping)
        rows = [self._build_row(r, grouped.get(r.id, []), decisions.get(r.id), self._artifact_links_available()) for r in definitions]
        self._apply_contributions(rows)
        return rows

    @staticmethod
    def _apply_contributions(rows: list[ProductRequirementMatrixRowRead]) -> None:
        """Only selected, applicable technical requirements contribute proof."""
        by_id = {row.annex_requirement.id: row for row in rows}
        for row in rows:
            row.supporting_requirements = []
            row.supporting_artifacts = []
        for child in rows:
            if child.annex_requirement.kind != "technical":
                continue
            for link in child.annex_requirement.contributions:
                parent = by_id.get(link.essential_requirement_id)
                if parent is None or parent.annex_requirement.kind != "essential":
                    continue
                parent.supporting_requirements.append(SupportingRequirementRead(
                    requirement=child.annex_requirement,
                    contribution=link.contribution,
                    applicability_decision=child.applicability_decision,
                    implementation_status=child.implementation_status,
                    finalized=child.finalized,
                ))
                if child.applicability_decision == RequirementApplicabilityDecision.applicable and child.finalized:
                    parent.supporting_artifacts.extend(child.artifacts)
        for parent in rows:
            parent.supporting_artifacts = list({(a.id, a.latest_revision.id if a.latest_revision else None): a for a in parent.supporting_artifacts}.values())
            if parent.annex_requirement.kind != "essential" or parent.applicability_decision != RequirementApplicabilityDecision.applicable:
                continue
            pending = [c for c in parent.supporting_requirements if not c.finalized]
            evidence = parent.artifacts + parent.supporting_artifacts
            parent.blockers = RequirementMappingService._review_blockers(parent, evidence)
            if pending:
                parent.blockers.append(f"Complete {len(pending)} selected technical requirement(s).")
            parent.finalized = not parent.blockers

    @staticmethod
    def _review_blockers(row: ProductRequirementMatrixRowRead, evidence: list) -> list[str]:
        blockers = []
        if row.applicability_decision == RequirementApplicabilityDecision.undecided:
            blockers.append("Decide applicability.")
        if not row.risk_items:
            blockers.append("Link the risk assessment and rationale.")
        if row.applicability_decision == RequirementApplicabilityDecision.not_applicable:
            if not (row.applicability_rationale or "").strip():
                blockers.append("Explain why this requirement does not apply.")
            return blockers
        if not any(a.latest_revision is not None for a in evidence):
            blockers.append("Link evidence with a pinned revision, directly or through validated technical requirements.")
        if row.implementation_status != RequirementProgressStatus.validated or row.verification_result != "pass" or not row.validated_at or not (row.validation_notes or "").strip():
            blockers.append("Record a validation conclusion after reviewing scope, criteria and evidence.")
        return blockers

    def release_requirement_row(self, release_id: UUID, annex_requirement_id: UUID) -> ProductRequirementMatrixRowRead:
        for row in self.release_matrix(release_id):
            if row.annex_requirement.id == annex_requirement_id:
                return row
        raise NotFoundException("Requirement is not selected for this release.")

    def _baseline_requirement(self, release_id: UUID, requirement_id: UUID) -> AnnexRequirementRead:
        baseline = self.db.scalar(select(ReleaseRequirementBaseline).where(
            ReleaseRequirementBaseline.product_release_id == release_id,
            ReleaseRequirementBaseline.requirement_id == requirement_id,
        ))
        if baseline is None:
            raise ValidationException("Select this requirement for the release before assessing it.")
        return AnnexRequirementRead.model_validate(baseline.requirement_snapshot or self.annex_requirement_repository.get_by_id(requirement_id))

    def invalidate_validation(self, release_id: UUID, requirement_id: UUID, *, include_self: bool = True) -> None:
        """A changed demonstration must be reviewed again, including its CRA conclusions."""
        baselines = list(self.db.scalars(select(ReleaseRequirementBaseline).where(
            ReleaseRequirementBaseline.product_release_id == release_id
        )))
        affected = {requirement_id} if include_self else set()
        for baseline in baselines:
            if baseline.requirement_id == requirement_id:
                affected.update(UUID(c["essential_requirement_id"]) for c in (baseline.requirement_snapshot or {}).get("contributions", []))
        for decision in self.requirement_mapping_repository.list_release_decisions(release_id):
            if decision.annex_requirement_id in affected:
                if decision.implementation_status == RequirementProgressStatus.validated:
                    decision.implementation_status = RequirementProgressStatus.implemented
                decision.validation_notes = None
                decision.verification_result = None
                decision.validated_at = None
                decision.validated_by_user_id = None

    def select_requirements(self, release_id: UUID, requirement_ids: list[UUID], *, actor_user_id: UUID,
                            essential_requirement_id: UUID | None = None,
                            contribution_notes: dict[UUID, str] | None = None) -> list[ProductRequirementMatrixRowRead]:
        self._assert_not_locked(release_id)
        release = self.db.get(ProductRelease, release_id)
        if release is None:
            raise NotFoundException("Release not found.")
        requirements = list(self.db.scalars(select(AnnexRequirement).where(AnnexRequirement.id.in_(requirement_ids))))
        if len(requirements) != len(set(requirement_ids)):
            raise ValidationException("One or more requirements do not exist.")
        for requirement in requirements:
            source = requirement.source
            if requirement.kind != "technical" or source.status != "published" or requirement.status != "published":
                raise ValidationException("Choose technical requirements from a published source.")
            if not source.organization_wide and release.product_id not in source.product_ids:
                raise ValidationException("This requirement source is not assigned to the selected product.")
            for link in requirement.contributions:
                self._baseline_requirement(release_id, link.essential_requirement_id)
        notes = contribution_notes or {}
        if set(notes) - set(requirement_ids) or (notes and essential_requirement_id is None):
            raise ValidationException("Contribution notes must refer to selected requirements and a CRA essential.")
        if essential_requirement_id is not None:
            essential = self._baseline_requirement(release_id, essential_requirement_id)
            if essential.kind != "essential":
                raise ValidationException("Choose a CRA essential requirement as the contribution target.")
        baselines = {baseline.requirement_id: baseline for baseline in self.db.scalars(
            select(ReleaseRequirementBaseline).where(ReleaseRequirementBaseline.product_release_id == release_id)
        )}
        selections = []
        for requirement in requirements:
            baseline = baselines.get(requirement.id)
            definition = dict(baseline.requirement_snapshot) if baseline and baseline.requirement_snapshot else AnnexRequirementRead.model_validate(requirement).model_dump(mode="json")
            contributions = list(definition.get("contributions", []))
            adds_contribution = essential_requirement_id is not None and not any(
                str(link["essential_requirement_id"]) == str(essential_requirement_id) for link in contributions
            )
            if adds_contribution:
                note = notes.get(requirement.id, "").strip()
                if not note or len(note) > 10000:
                    raise ValidationException("Explain how each selected requirement supports this CRA essential (up to 10,000 characters).")
                contributions.append({"essential_requirement_id": str(essential_requirement_id), "contribution": note})
                definition["contributions"] = contributions
            selections.append((requirement, baseline, definition, adds_contribution))
        for requirement, baseline, definition, adds_contribution in selections:
            if baseline is None:
                self.db.add(ReleaseRequirementBaseline(
                    product_release_id=release_id, requirement_id=requirement.id,
                    requirement_revision=requirement.revision, requirement_snapshot=definition,
                ))
                self.db.flush()
                self.invalidate_validation(release_id, requirement.id)
            elif adds_contribution:
                baseline.requirement_snapshot = definition
                self.invalidate_validation(release_id, essential_requirement_id)
        self._write_audit_log(actor_user_id=actor_user_id, action_type=AuditActionType.update,
            entity_type=EntityType.requirement_mapping, entity_id=release_id, status=AuditStatus.success,
            details_json={"action": "select_technical_requirements", "requirement_ids": [str(i) for i in requirement_ids],
                          "essential_requirement_id": str(essential_requirement_id) if essential_requirement_id else None,
                          "contribution_notes": {str(key): value for key, value in notes.items()}})
        self.db.commit()
        return self.release_matrix(release_id)

    def deselect_requirement(self, release_id: UUID, requirement_id: UUID, *, actor_user_id: UUID) -> list[ProductRequirementMatrixRowRead]:
        self._assert_not_locked(release_id)
        requirement = self._baseline_requirement(release_id, requirement_id)
        if requirement.kind != "technical":
            raise ValidationException("CRA essential requirements must remain in the release assessment.")
        self.invalidate_validation(release_id, requirement_id)
        baseline = self.db.scalar(select(ReleaseRequirementBaseline).where(
            ReleaseRequirementBaseline.product_release_id == release_id,
            ReleaseRequirementBaseline.requirement_id == requirement_id,
        ))
        self.db.delete(baseline)
        self._write_audit_log(actor_user_id=actor_user_id, action_type=AuditActionType.update,
            entity_type=EntityType.requirement_mapping, entity_id=release_id, status=AuditStatus.success,
            details_json={"action": "deselect_technical_requirement", "requirement_id": str(requirement_id)})
        self.db.commit()
        return self.release_matrix(release_id)

    def _build_row(
        self,
        requirement: Any,
        grouped_mappings: list[RequirementMapping],
        decision: ProductRequirementDecision | None,
        artifact_traceability_available: bool,
    ) -> ProductRequirementMatrixRowRead:
        applicability_decision = (
            decision.applicability_decision
            if decision is not None
            else RequirementApplicabilityDecision.undecided
        )
        implementation_status = (
            decision.implementation_status
            if decision is not None
            else RequirementProgressStatus.planned
        )
        risk_items = self._unique_risk_items(grouped_mappings)
        artifacts = self._unique_artifacts(grouped_mappings)
        row = ProductRequirementMatrixRowRead(
            annex_requirement=requirement,
            artifact_traceability_available=artifact_traceability_available,
            applicability_decision=applicability_decision,
            applicability_rationale=decision.rationale if decision is not None else None,
            mapping_ids=[mapping.id for mapping in grouped_mappings],
            trace_records=[self._matrix_mapping_payload(mapping) for mapping in grouped_mappings],
            risk_items=risk_items,
            artifacts=artifacts,
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
            implementation_status=implementation_status,
            validation_notes=decision.validation_notes if decision else None,
            verification_result=decision.verification_result if decision else None,
            validated_by_user_id=decision.validated_by_user_id if decision else None,
            validated_at=decision.validated_at if decision else None,
            finalized=self._is_finalized(
                applicability_decision, implementation_status, risk_items, artifacts
            ),
        )

        row.blockers = self._review_blockers(row, row.artifacts)
        row.finalized = not row.blockers
        return row

    @staticmethod
    def _is_finalized(
        applicability_decision: RequirementApplicabilityDecision,
        implementation_status: RequirementProgressStatus,
        risk_items: list[Any],
        artifacts: list[Any],
    ) -> bool:
        """Whether a requirement is fully handled for this release.

        Rule:
          * undecided                → never finalized.
          * any decision             → requires at least one risk justification.
          * additionally if APPLICABLE → requires ≥1 linked artifact and a
            ``validated`` implementation status.
          * NOT_APPLICABLE           → finalized once decided + risk-justified.
        """
        if applicability_decision == RequirementApplicabilityDecision.undecided:
            return False
        if not risk_items:
            return False
        if applicability_decision == RequirementApplicabilityDecision.applicable:
            return bool(artifacts) and implementation_status == RequirementProgressStatus.validated
        return True

    def update_release_requirement_decision(
        self,
        release_id: UUID,
        annex_requirement_id: UUID,
        payload: ProductRequirementDecisionUpdate,
        *,
        actor_user_id: UUID | None,
    ) -> ProductRequirementMatrixRowRead:
        self._assert_not_locked(release_id)
        requirement = self._baseline_requirement(release_id, annex_requirement_id)
        _validate_applicability_decision(
            requirement.is_mandatory,
            payload.applicability_decision,
            payload.rationale,
        )

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

        self.invalidate_validation(release_id, annex_requirement_id)
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
        # Return the freshly rebuilt matrix row so the client can update in place
        # without re-fetching the entire matrix.
        return self.release_requirement_row(release_id, annex_requirement_id)

    def update_release_requirement_status(
        self,
        release_id: UUID,
        annex_requirement_id: UUID,
        implementation_status: RequirementProgressStatus,
        *,
        actor_user_id: UUID | None,
        validation_notes: str | None = None,
        verification_result: str | None = None,
    ) -> ProductRequirementMatrixRowRead:
        """Set the per-requirement implementation progress status for a release."""
        self._assert_not_locked(release_id)
        self._baseline_requirement(release_id, annex_requirement_id)

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

        if implementation_status == RequirementProgressStatus.validated or verification_result:
            if not validation_notes or not validation_notes.strip():
                raise ValidationException("Record what was verified and why the evidence demonstrates this requirement.")
            row = self.release_requirement_row(release_id, annex_requirement_id)
            if row.applicability_decision != RequirementApplicabilityDecision.applicable:
                raise ValidationException("Only applicable requirements can be validated.")
            prerequisite_blockers = [b for b in row.blockers if not b.startswith("Record a validation")]
            if prerequisite_blockers and implementation_status == RequirementProgressStatus.validated:
                raise ValidationException(" ".join(prerequisite_blockers))
            if implementation_status == RequirementProgressStatus.validated and verification_result not in {None, "pass"}:
                raise ValidationException("A demonstrated requirement must have a passing validation result.")
        self.invalidate_validation(release_id, annex_requirement_id)
        existing.implementation_status = implementation_status
        if implementation_status == RequirementProgressStatus.validated or verification_result:
            existing.validation_notes = validation_notes.strip()
            existing.verification_result = verification_result or "pass"
            existing.validated_by_user_id = actor_user_id
            existing.validated_at = datetime.now(UTC)
        self.db.flush()

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.update,
            entity_type=EntityType.requirement_mapping,
            entity_id=annex_requirement_id,
            status=AuditStatus.success,
            details_json={
                "action": "update_release_requirement_status",
                "release_id": str(release_id),
                "annex_requirement_id": str(annex_requirement_id),
                "implementation_status": implementation_status.value,
                "validation_notes": validation_notes,
                "verification_result": verification_result,
            },
        )
        self.db.commit()
        return self.release_requirement_row(release_id, annex_requirement_id)

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

    def _validate_risk_scope(self, release_id: UUID, risk_item) -> None:
        release = self.db.get(ProductRelease, release_id)
        assessment = risk_item.risk_assessment
        if release is None or assessment.product_id != release.product_id:
            raise ValidationException("Choose a risk assessment for this product.")
        if assessment.product_release_id and assessment.product_release_id != release_id:
            raise ValidationException("Choose a risk assessment for this release or the product overall.")

    def create(
        self,
        payload: RequirementMappingCreate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RequirementMapping:
        self._assert_not_locked(payload.product_release_id)
        self._baseline_requirement(payload.product_release_id, payload.annex_requirement_id)
        annex_requirement = self.annex_requirement_repository.get_by_id(payload.annex_requirement_id)
        if annex_requirement is None:
            raise ValueError("Annex requirement not found.")

        if payload.risk_item_id is not None:
            risk_item = self.risk_item_repository.get_by_id(payload.risk_item_id)
            if risk_item is None:
                raise ValueError("Risk item not found.")
            self._validate_risk_scope(payload.product_release_id, risk_item)

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

        self.invalidate_validation(mapping.product_release_id, mapping.annex_requirement_id)
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
        self._assert_not_locked(mapping.product_release_id)
        before = self._snapshot(mapping)
        self.invalidate_validation(mapping.product_release_id, mapping.annex_requirement_id)

        update_data = payload.model_dump(exclude_unset=True)

        if "annex_requirement_id" in update_data and update_data["annex_requirement_id"] is not None:
            annex_requirement = self.annex_requirement_repository.get_by_id(update_data["annex_requirement_id"])
            if annex_requirement is None:
                raise ValueError("Annex requirement not found.")
            self._baseline_requirement(mapping.product_release_id, update_data["annex_requirement_id"])

        if "risk_item_id" in update_data and update_data["risk_item_id"] is not None:
            risk_item = self.risk_item_repository.get_by_id(update_data["risk_item_id"])
            if risk_item is None:
                raise ValueError("Risk item not found.")
            self._validate_risk_scope(mapping.product_release_id, risk_item)

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

        self.invalidate_validation(mapping.product_release_id, mapping.annex_requirement_id)
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
        self._assert_not_locked(mapping.product_release_id)
        before = self._snapshot(mapping)
        self.invalidate_validation(mapping.product_release_id, mapping.annex_requirement_id)

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
        self._assert_not_locked(mapping.product_release_id)
        artifact = self.artifact_repository.get_or_404(artifact_id)
        release = self.db.get(ProductRelease, mapping.product_release_id)
        if release.product_id not in [link.product_id for link in artifact.product_links]:
            raise ValidationException("Choose evidence assigned to this product.")
        if not artifact.revisions:
            raise ValidationException("Upload an evidence revision before linking this artifact.")

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
                    artifact_revision_id=artifact.revisions[0].id,
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
        self.invalidate_validation(mapping.product_release_id, mapping.annex_requirement_id)
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
        self._assert_not_locked(mapping.product_release_id)
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
        self.invalidate_validation(mapping.product_release_id, mapping.annex_requirement_id)
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
            "artifacts": [self._artifact_payload(link.artifact, link.artifact_revision) for link in artifact_links if link.artifact],
        }

    def _artifact_payload(self, artifact, revision=None) -> dict[str, Any]:
        latest_revision = revision
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
        unique: dict[tuple[UUID, UUID | None], dict[str, Any]] = {}
        for mapping in mappings:
            for link in mapping.artifact_links:
                if link.artifact is not None:
                    unique[(link.artifact.id, link.artifact_revision_id)] = self._artifact_payload(link.artifact, link.artifact_revision)
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
