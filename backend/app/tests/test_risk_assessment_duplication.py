from __future__ import annotations

from uuid import uuid4

from app.models.enums import (
    AnnexPart,
    RequirementImplementationStatus,
    RiskAssessmentStatus,
    RiskItemStatus,
    RiskLevel,
)
from app.models.product import Product
from app.models.risk_assessment import RiskAssessment
from app.models.risk_item import RiskItem
from app.models.requirement_mapping import RequirementMapping
from app.models.user import User
from app.schemas.risk_assessment import RiskAssessmentDuplicateVersionRequest
from app.services.risk_assessment_service import RiskAssessmentService


def test_duplicate_risk_assessment_copies_items_and_mappings_but_not_evidence(db_session) -> None:
    owner = User(
        email=f"owner-{uuid4()}@example.com",
        full_name="Risk Owner",
        hashed_password="hashed-password",
        is_active=True,
    )

    product = Product(
        product_code=f"PRD-{uuid4()}",
        name="Secure Gateway",
        description="Gateway product",
        manufacturer_name="Example Manufacturer",
        intended_use="Network security gateway",
        product_type="software",
    )

    db_session.add_all([owner, product])
    db_session.flush()

    source_assessment = RiskAssessment(
        product_id=product.id,
        product_release_id=None,
        title="Initial risk assessment",
        system_version=1,
        user_version=None,
        status=RiskAssessmentStatus.approved,
        methodology="STRIDE",
        summary="Initial approved assessment",
        owner_user_id=owner.id,
    )
    db_session.add(source_assessment)
    db_session.flush()

    source_item = RiskItem(
        risk_assessment_id=source_assessment.id,
        title="Unauthenticated admin interface exposure",
        description="The admin interface may be exposed to unauthenticated users.",
        threat_scenario="External actor reaches exposed admin endpoint over the network.",
        asset_affected="Administrative control plane",
        likelihood=RiskLevel.high,
        impact=RiskLevel.critical,
        risk_level=RiskLevel.critical,
        mitigation_plan="Restrict access and enforce authentication.",
        residual_risk_level=RiskLevel.medium,
        status=RiskItemStatus.in_progress,
        owner_user_id=owner.id,
    )
    db_session.add(source_item)
    db_session.flush()

    annex_requirement_id = _create_annex_requirement(db_session)

    source_mapping = RequirementMapping(
        risk_item_id=source_item.id,
        annex_requirement_id=annex_requirement_id,
        engineering_requirement_ref="ENG-REQ-001",
        sdl_activity="Threat modeling",
        implementation_status=RequirementImplementationStatus.in_progress,
        evidence_summary="Threat model in progress",
    )
    db_session.add(source_mapping)
    db_session.commit()

    service = RiskAssessmentService(db_session)

    duplicated = service.duplicate_version(
        source_assessment.id,
        RiskAssessmentDuplicateVersionRequest(
            user_version=None,
            title="Initial risk assessment - Release 2",
            reset_status_to_draft=True,
            copy_risk_items=True,
            copy_requirement_mappings=True,
            copy_evidence_links=False,
        ),
        actor_user_id=owner.id,
    )

    assert duplicated.id != source_assessment.id
    assert duplicated.product_id == source_assessment.product_id
    assert duplicated.title == "Initial risk assessment - Release 2"
    assert duplicated.system_version == 2  # Auto-generated
    assert duplicated.status == RiskAssessmentStatus.draft
    assert duplicated.approved_at is None

    duplicated_full = service.get(duplicated.id)
    assert len(duplicated_full.risk_items) == 1

    duplicated_item = duplicated_full.risk_items[0]
    assert duplicated_item.id != source_item.id
    assert duplicated_item.risk_assessment_id == duplicated.id
    assert duplicated_item.title == source_item.title
    assert duplicated_item.risk_level == source_item.risk_level
    assert duplicated_item.owner_user_id == source_item.owner_user_id

    assert len(duplicated_item.requirement_mappings) == 1
    duplicated_mapping = duplicated_item.requirement_mappings[0]
    assert duplicated_mapping.id != source_mapping.id
    assert duplicated_mapping.risk_item_id == duplicated_item.id
    assert duplicated_mapping.annex_requirement_id == source_mapping.annex_requirement_id
    assert duplicated_mapping.engineering_requirement_ref == source_mapping.engineering_requirement_ref
    assert duplicated_mapping.sdl_activity == source_mapping.sdl_activity

    assert len(duplicated_full.evidence_items) == 0


def test_duplicate_risk_assessment_without_copying_items_creates_empty_new_version(db_session) -> None:
    owner = User(
        email=f"owner2-{uuid4()}@example.com",
        full_name="Risk Owner 2",
        hashed_password="hashed-password",
        is_active=True,
    )

    product = Product(
        product_code=f"PRD-{uuid4()}",
        name="Embedded Controller",
        description="Controller product",
        manufacturer_name="Example Manufacturer",
        intended_use="Industrial control",
        product_type="firmware",
    )

    db_session.add_all([owner, product])
    db_session.flush()

    source_assessment = RiskAssessment(
        product_id=product.id,
        product_release_id=None,
        title="Controller risk assessment",
        system_version=1,
        user_version="2026.1",
        status=RiskAssessmentStatus.in_review,
        methodology="Attack tree",
        summary="Baseline",
        owner_user_id=owner.id,
    )
    db_session.add(source_assessment)
    db_session.flush()

    source_item = RiskItem(
        risk_assessment_id=source_assessment.id,
        title="Debug port abuse",
        description="Debug port may be misused.",
        threat_scenario="Attacker obtains physical access to the device.",
        asset_affected="Firmware integrity",
        likelihood=RiskLevel.medium,
        impact=RiskLevel.high,
        risk_level=RiskLevel.high,
        mitigation_plan="Disable debug port in production.",
        residual_risk_level=RiskLevel.low,
        status=RiskItemStatus.open,
        owner_user_id=None,
    )
    db_session.add(source_item)
    db_session.commit()

    service = RiskAssessmentService(db_session)

    duplicated = service.duplicate_version(
        source_assessment.id,
        RiskAssessmentDuplicateVersionRequest(
            user_version="2026.2",
            copy_risk_items=False,
            copy_requirement_mappings=False,
            copy_evidence_links=False,
            reset_status_to_draft=True,
        ),
        actor_user_id=owner.id,
    )

    duplicated_full = service.get(duplicated.id)
    assert duplicated_full.user_version == "2026.2"
    assert duplicated_full.system_version == 2  # Auto-generated
    assert duplicated_full.status == RiskAssessmentStatus.draft
    assert len(duplicated_full.risk_items) == 0
    assert len(duplicated_full.evidence_items) == 0


def _create_annex_requirement(db_session):
    from app.models.annex_requirement import AnnexRequirement

    requirement = AnnexRequirement(
        code=f"ANNEX-TEST-{uuid4()}",
        title="Test Annex Requirement",
        description="Requirement used for duplication test.",
        annex_part=AnnexPart.part_i,
        is_active=True,
    )
    db_session.add(requirement)
    db_session.flush()
    return requirement.id