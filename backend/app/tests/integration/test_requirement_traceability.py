from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.annex_i_catalog import sync_annex_i_requirements
from app.core.exceptions import ConflictException, ValidationException
from app.models.artifact import Artifact, ArtifactProductLink, ArtifactRevision
from app.models.enums import (
    ArtifactSourceType,
    EvidenceType,
    RequirementApplicabilityDecision,
    RequirementProgressStatus,
    RiskAssessmentStatus,
    RiskItemStatus,
    RiskLevel,
)
from app.models.product import Product
from app.models.requirement_assessment import (
    ReleaseRequirementAssessment,
    ReleaseRequirementAssessmentSnapshot,
)
from app.models.risk_assessment import RiskAssessment
from app.models.risk_item import RiskItem
from app.models.user import User
from app.schemas.annex_matrix import ProductRequirementDecisionUpdate
from app.schemas.annex_requirement import (
    AnnexRequirementCreate,
    AnnexRequirementUpdate,
    RequirementContributionRead,
)
from app.schemas.product_release import ProductReleaseCreate
from app.schemas.requirement_mapping import RequirementMappingCreate
from app.schemas.requirement_source import RequirementSourceCreate
from app.services.annex_requirement_service import AnnexRequirementService
from app.services.product_release_service import ProductReleaseService
from app.services.requirement_assessment_service import RequirementAssessmentService
from app.services.requirement_mapping_service import RequirementMappingService
from app.services.requirement_source_service import RequirementSourceService


@pytest.fixture
def trace_context(db_session):
    db = db_session
    sync_annex_i_requirements(db)
    owner = User(email=f"trace-{uuid4()}@example.com", full_name="Reviewer", hashed_password="test", is_active=True)
    product = Product(product_code=str(uuid4()), name="Traceability test", manufacturer_name="Test", intended_use="Connected product", product_type="software")
    db.add_all([owner, product])
    db.flush()
    release = ProductReleaseService(db).create_release(ProductReleaseCreate(product_id=product.id), actor=owner)
    risk_assessment = RiskAssessment(product_id=product.id, product_release_id=release.id, title="Release risk assessment", system_version=1, status=RiskAssessmentStatus.draft, methodology="STRIDE", summary="Release scope and threats.", owner_user_id=owner.id)
    db.add(risk_assessment)
    db.flush()
    risk = RiskItem(risk_assessment_id=risk_assessment.id, title="Unauthorized access", description="Scope justification", threat_scenario="Remote attack", asset_affected="Product", likelihood=RiskLevel.medium, impact=RiskLevel.high, risk_level=RiskLevel.high, mitigation_plan="Technical controls", status=RiskItemStatus.open)
    artifact = Artifact(title="Release security review", artifact_type=EvidenceType.test_report, created_by_user_id=owner.id)
    db.add_all([risk, artifact])
    db.flush()
    db.add(ArtifactProductLink(artifact_id=artifact.id, product_id=product.id))
    db.add(ArtifactRevision(artifact_id=artifact.id, revision_number=1, source_type=ArtifactSourceType.upload, original_filename="review.txt", storage_path="test-review.txt", sha256="a" * 64, uploaded_by_user_id=owner.id))
    db.flush()
    essentials = [row.annex_requirement for row in RequirementMappingService(db).release_matrix(release.id)]
    return db, owner, product, release, risk, artifact, essentials


def technical(context, *, targets=None, publish=True, edition="1", identifier=None):
    db, owner, _, _, _, _, essentials = context
    source = RequirementSourceService(db).create(RequirementSourceCreate(
        identifier=identifier or f"TEST-{uuid4()}", edition=edition, title="Technical standard", source_type="standard", organization_wide=True,
    ))
    requirement = AnnexRequirementService(db).create(AnnexRequirementCreate(
        source_id=source.id, code="SEC-001", title="Authenticate privileged operations", description="Prevent unauthenticated administration.",
        acceptance_criteria="Unauthorized operations are rejected and logged.",
        contributions=[RequirementContributionRead(essential_requirement_id=target.id, contribution="Provides authenticated administration; review other interfaces separately.") for target in (targets if targets is not None else essentials[:2])],
    ), actor_user_id=owner.id)
    if publish:
        RequirementSourceService(db).set_status(source.id, "published")
    return source, requirement


def scope_and_risk(context, requirement_id, *, evidence=True):
    db, owner, _, release, risk, artifact, _ = context
    service = RequirementMappingService(db)
    service.update_release_requirement_decision(release.id, requirement_id, ProductRequirementDecisionUpdate(applicability_decision=RequirementApplicabilityDecision.applicable, rationale="Applies to the assessed interfaces."), actor_user_id=owner.id)
    trace = service.create(RequirementMappingCreate(product_release_id=release.id, annex_requirement_id=requirement_id, risk_item_id=risk.id, sdl_activity="verification", evidence_summary="Reviewed against this release's attack surface."), actor_user_id=owner.id)
    if evidence:
        service.attach_artifact(trace.id, artifact.id, actor_user_id=owner.id)
    return trace


def validate(context, requirement_id, result="pass"):
    db, owner, _, release, _, _, _ = context
    return RequirementMappingService(db).update_release_requirement_status(
        release.id, requirement_id,
        RequirementProgressStatus.validated if result == "pass" else RequirementProgressStatus.implemented,
        actor_user_id=owner.id, verification_result=result,
        validation_notes="Reviewed the release scope, applicable acceptance criteria and pinned security review. Combined coverage is adequate." if result == "pass" else "Unauthorized operations were not rejected; changes are required.",
    )


def test_publication_selection_and_source_editions(trace_context):
    db, owner, product, release, _, _, essentials = trace_context
    identifier = f"EDITION-{uuid4()}"
    source, requirement = technical(trace_context, identifier=identifier)
    _, next_edition = technical(trace_context, identifier=identifier, edition="2")
    service = RequirementMappingService(db)
    assert len(service.release_matrix(release.id)) == len(essentials)
    service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id)
    row = service.release_requirement_row(release.id, requirement.id)
    assert row.annex_requirement.source_edition == "1"
    assert row.annex_requirement.contributions[0].contribution
    RequirementSourceService(db).set_status(source.id, "retired")
    assert service.release_requirement_row(release.id, requirement.id).annex_requirement.status == "published"
    with pytest.raises(ConflictException):
        AnnexRequirementService(db).update(requirement.id, AnnexRequirementUpdate(title="Changed"), actor_user_id=owner.id)
    successor = ProductReleaseService(db).create_release(ProductReleaseCreate(product_id=product.id, parent_release_id=release.id), actor=owner)
    inherited = service.release_requirement_row(successor.id, requirement.id)
    assert inherited.annex_requirement.source_edition == "1"
    assert inherited.implementation_status == RequirementProgressStatus.planned
    assert next_edition.id != requirement.id


def test_shared_technical_proof_requires_each_essential_conclusion(trace_context):
    db, owner, _, release, _, _, essentials = trace_context
    _, requirement = technical(trace_context)
    service = RequirementMappingService(db)
    service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id)
    scope_and_risk(trace_context, requirement.id)
    for essential in essentials[:2]:
        scope_and_risk(trace_context, essential.id, evidence=False)
    validate(trace_context, requirement.id)
    for essential in essentials[:2]:
        row = service.release_requirement_row(release.id, essential.id)
        assert len(row.supporting_requirements) == 1
        assert len(row.supporting_artifacts) == 1
        assert not row.finalized
        assert validate(trace_context, essential.id).finalized


def test_failed_child_blocks_parent_even_with_direct_evidence(trace_context):
    db, owner, _, release, _, _, essentials = trace_context
    _, requirement = technical(trace_context, targets=essentials[:1])
    service = RequirementMappingService(db)
    service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id)
    scope_and_risk(trace_context, requirement.id)
    scope_and_risk(trace_context, essentials[0].id)
    row = validate(trace_context, requirement.id, "fail")
    assert row.verification_result == "fail" and not row.finalized
    with pytest.raises(ValidationException, match="selected technical"):
        validate(trace_context, essentials[0].id)
    validate(trace_context, requirement.id)
    assert validate(trace_context, essentials[0].id).finalized


def test_na_child_never_supplies_essential_evidence(trace_context):
    db, owner, _, release, _, _, essentials = trace_context
    _, requirement = technical(trace_context, targets=essentials[:1])
    service = RequirementMappingService(db)
    service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id)
    scope_and_risk(trace_context, requirement.id)
    scope_and_risk(trace_context, essentials[0].id, evidence=False)
    service.update_release_requirement_decision(release.id, requirement.id, ProductRequirementDecisionUpdate(applicability_decision=RequirementApplicabilityDecision.not_applicable, rationale="This release has no administrative interface."), actor_user_id=owner.id)
    row = service.release_requirement_row(release.id, essentials[0].id)
    assert row.applicability_decision == RequirementApplicabilityDecision.applicable
    assert not row.supporting_artifacts and not row.finalized
    with pytest.raises(ValidationException, match="evidence"):
        validate(trace_context, essentials[0].id)


def test_evidence_revision_is_pinned_and_changes_invalidate_parent(trace_context):
    db, owner, _, release, _, artifact, essentials = trace_context
    _, requirement = technical(trace_context, targets=essentials[:1])
    service = RequirementMappingService(db)
    service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id)
    trace = scope_and_risk(trace_context, requirement.id)
    scope_and_risk(trace_context, essentials[0].id, evidence=False)
    validate(trace_context, requirement.id)
    validate(trace_context, essentials[0].id)
    db.add(ArtifactRevision(artifact_id=artifact.id, revision_number=2, source_type=ArtifactSourceType.upload, storage_path="new-review.txt", uploaded_by_user_id=owner.id))
    db.commit()
    db.expire_all()
    assert service.release_requirement_row(release.id, requirement.id).artifacts[0].latest_revision.revision_number == 1
    service.detach_artifact(trace.id, artifact.id, actor_user_id=owner.id)
    parent = service.release_requirement_row(release.id, essentials[0].id)
    assert not parent.finalized and parent.validation_notes is None
    service.attach_artifact(trace.id, artifact.id, actor_user_id=owner.id)
    assert service.release_requirement_row(release.id, requirement.id).artifacts[0].latest_revision.revision_number == 2


def test_approval_lock_and_immutable_report_survive_library_changes(trace_context):
    db, owner, _, release, _, _, essentials = trace_context
    source, requirement = technical(trace_context, targets=essentials[:1])
    service = RequirementMappingService(db)
    service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id)
    scope_and_risk(trace_context, requirement.id)
    validate(trace_context, requirement.id)
    for essential in essentials:
        scope_and_risk(trace_context, essential.id)
        validate(trace_context, essential.id)
    assessment = RequirementAssessmentService(db)
    assert assessment.approve(release.id, actor_user_id=owner.id)["is_locked"]
    snapshot = db.scalar(select(ReleaseRequirementAssessmentSnapshot).join(ReleaseRequirementAssessment).where(ReleaseRequirementAssessment.product_release_id == release.id))
    original_hash = snapshot.content_sha256
    from app.services.artifact_service import ArtifactService
    artifact = trace_context[5]
    with pytest.raises(ConflictException, match="snapshot"):
        ArtifactService(db).delete_artifact(artifact.id, actor_user_id=owner.id)
    with pytest.raises(ConflictException, match="locked"):
        service.deselect_requirement(release.id, requirement.id, actor_user_id=owner.id)
    RequirementSourceService(db).set_status(source.id, "retired")
    assert service.release_requirement_row(release.id, requirement.id).annex_requirement.status == "published"
    assert snapshot.content_sha256 == original_hash
    assessment.reopen(release.id, actor_user_id=owner.id)
    service.deselect_requirement(release.id, requirement.id, actor_user_id=owner.id)
    assert not assessment.get_status(release.id)["can_approve"]
    assert validate(trace_context, essentials[0].id).finalized
    assessment.approve(release.id, actor_user_id=owner.id)
    assert len(list(db.scalars(select(ReleaseRequirementAssessmentSnapshot).where(ReleaseRequirementAssessmentSnapshot.release_requirement_assessment_id == snapshot.release_requirement_assessment_id)))) == 2
    assert snapshot.content_sha256 == original_hash


def test_selection_and_mapping_guardrails(trace_context):
    db, owner, _, release, _, _, essentials = trace_context
    source, draft = technical(trace_context, publish=False)
    service = RequirementMappingService(db)
    with pytest.raises(ValidationException, match="published"):
        service.select_requirements(release.id, [draft.id], actor_user_id=owner.id)
    with pytest.raises(ValidationException, match="must remain"):
        service.deselect_requirement(release.id, essentials[0].id, actor_user_id=owner.id)
    with pytest.raises(ValidationException, match="before assessing"):
        scope_and_risk(trace_context, draft.id)
    link = RequirementContributionRead(essential_requirement_id=essentials[0].id, contribution="Revised contribution scope.")
    updated = AnnexRequirementService(db).update(draft.id, AnnexRequirementUpdate(contributions=[link]), actor_user_id=owner.id)
    assert len(updated.contributions) == 1
    updated = AnnexRequirementService(db).update(draft.id, AnnexRequirementUpdate(contributions=[link]), actor_user_id=owner.id)
    assert len(updated.contributions) == 1
    with pytest.raises(ValidationException, match="only once"):
        AnnexRequirementService(db).update(draft.id, AnnexRequirementUpdate(contributions=[link, link]), actor_user_id=owner.id)
    with pytest.raises(ValidationException, match="valid CRA"):
        AnnexRequirementService(db).update(draft.id, AnnexRequirementUpdate(contributions=[RequirementContributionRead(essential_requirement_id=draft.id, contribution="Invalid self link")]), actor_user_id=owner.id)


def test_report_and_readiness_follow_reviewed_essential_proof(trace_context):
    from app.services.product_readiness_service import ProductReadinessService
    from app.services.release_report_service import ReleaseReportService

    db, owner, _, release, _, _, essentials = trace_context
    _, requirement = technical(trace_context, targets=essentials[:1])
    service = RequirementMappingService(db)
    service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id)
    scope_and_risk(trace_context, requirement.id)
    scope_and_risk(trace_context, essentials[0].id, evidence=False)
    validate(trace_context, requirement.id)
    report = ReleaseReportService(db)._annex_sections(release.id)
    assert len(report["part1"] + report["part2"]) == len(essentials)
    entry = next(e for e in report["part1"] if e["code"] == essentials[0].code)
    assert entry["bucket"] == "partial"
    assert ProductReadinessService(db)._build_release_readiness(release, set()).coverage.met == 0
    validate(trace_context, essentials[0].id)
    assert ProductReadinessService(db)._build_release_readiness(release, set()).coverage.met == 1
    report = ReleaseReportService(db)._annex_sections(release.id)
    entry = next(e for e in report["part1"] if e["code"] == essentials[0].code)
    assert entry["bucket"] == "compliant"
    assert "revision 1" in entry["linked_artifacts"][0]


def test_legacy_approval_is_read_without_rewriting_snapshot(trace_context):
    import hashlib
    import json
    from copy import deepcopy

    db, owner, _, release, _, _, essentials = trace_context
    for essential in essentials:
        scope_and_risk(trace_context, essential.id)
        validate(trace_context, essential.id)
    RequirementAssessmentService(db).approve(release.id, actor_user_id=owner.id)
    snapshot = db.scalar(select(ReleaseRequirementAssessmentSnapshot).join(ReleaseRequirementAssessment).where(ReleaseRequirementAssessment.product_release_id == release.id))
    payload = deepcopy(snapshot.snapshot_json)
    original_fields = {"id", "code", "title", "is_active", "annex_part", "created_at", "updated_at", "description"}
    for row in payload["matrix"]:
        row["annex_requirement"] = {key: value for key, value in row["annex_requirement"].items() if key in original_fields}
        for key in ("implementation_status", "finalized", "validation_notes", "verification_result", "validated_by_user_id", "validated_at", "supporting_requirements", "supporting_artifacts", "blockers"):
            row.pop(key, None)
    snapshot.snapshot_json = payload
    snapshot.content_sha256 = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    db.commit()
    original_hash = snapshot.content_sha256
    rows = RequirementMappingService(db).release_matrix(release.id)
    assert len(rows) == len(essentials)
    assert all(row.finalized and row.annex_requirement.kind == "essential" for row in rows)
    assert all(row.verification_result is None and "Historical approval" in row.validation_notes for row in rows)
    assert snapshot.snapshot_json == payload and snapshot.content_sha256 == original_hash


def test_unmapped_requirement_can_contribute_without_changing_library(trace_context):
    db, owner, _, release, _, _, essentials = trace_context
    _, requirement = technical(trace_context, targets=[])
    service = RequirementMappingService(db)
    with pytest.raises(ValidationException, match="Explain how"):
        service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id,
                                    essential_requirement_id=essentials[0].id)
    assert all(row.annex_requirement.id != requirement.id for row in service.release_matrix(release.id))
    rows = service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id,
        essential_requirement_id=essentials[0].id, contribution_notes={requirement.id: "Rejects unauthorized administration of this release."})
    parent = next(row for row in rows if row.annex_requirement.id == essentials[0].id)
    assert parent.supporting_requirements[0].requirement.id == requirement.id
    assert parent.supporting_requirements[0].contribution == "Rejects unauthorized administration of this release."
    assert not parent.finalized
    db.refresh(requirement)
    assert requirement.contributions == []
    scope_and_risk(trace_context, requirement.id)
    scope_and_risk(trace_context, essentials[0].id, evidence=False)
    validate(trace_context, requirement.id)
    assert validate(trace_context, essentials[0].id).finalized


def test_selected_requirement_can_be_linked_to_another_essential(trace_context):
    db, owner, _, release, _, _, essentials = trace_context
    _, requirement = technical(trace_context, targets=essentials[:1])
    service = RequirementMappingService(db)
    service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id)
    scope_and_risk(trace_context, requirement.id)
    validate(trace_context, requirement.id)
    scope_and_risk(trace_context, essentials[1].id)
    validate(trace_context, essentials[1].id)
    rows = service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id,
        essential_requirement_id=essentials[1].id, contribution_notes={requirement.id: "Additional release-specific scope."})
    parent = next(row for row in rows if row.annex_requirement.id == essentials[1].id)
    assert parent.supporting_requirements[0].requirement.id == requirement.id
    assert not parent.finalized and parent.validation_notes is None
    assert service.release_requirement_row(release.id, requirement.id).finalized
    assert len(service.release_requirement_row(release.id, requirement.id).annex_requirement.contributions) == 2
    service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id,
                                essential_requirement_id=essentials[1].id)
    assert len(service.release_requirement_row(release.id, requirement.id).annex_requirement.contributions) == 2
    assert len(requirement.contributions) == 1
    with pytest.raises(ValidationException, match="CRA essential"):
        service.select_requirements(release.id, [requirement.id], actor_user_id=owner.id,
                                    essential_requirement_id=requirement.id)
