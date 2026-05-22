from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.annex_requirement import AnnexRequirement
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
from app.models.user import User
from app.schemas.requirement_mapping import RequirementMappingCreate, RequirementMappingUpdate
from app.services.requirement_mapping_service import RequirementMappingService


def test_create_requirement_mapping_requires_valid_annex_requirement(db_session) -> None:
    owner, _, risk_item = _create_risk_item_context(db_session)
    service = RequirementMappingService(db_session)

    with pytest.raises(ValueError, match="Annex requirement not found"):
        service.create(
            RequirementMappingCreate(
                risk_item_id=risk_item.id,
                annex_requirement_id=uuid4(),
                engineering_requirement_ref="ENG-REQ-404",
                sdl_activity="Threat modeling",
                implementation_status=RequirementImplementationStatus.planned,
                evidence_summary="Pending mapping",
            ),
            actor_user_id=owner.id,
        )


def test_create_requirement_mapping_requires_valid_risk_item_when_provided(db_session) -> None:
    owner, _, _ = _create_risk_item_context(db_session)
    annex_requirement = _create_annex_requirement(db_session)
    service = RequirementMappingService(db_session)

    with pytest.raises(ValueError, match="Risk item not found"):
        service.create(
            RequirementMappingCreate(
                risk_item_id=uuid4(),
                annex_requirement_id=annex_requirement.id,
                engineering_requirement_ref="ENG-REQ-101",
                sdl_activity="Secure design review",
                implementation_status=RequirementImplementationStatus.planned,
                evidence_summary="No linked risk item exists",
            ),
            actor_user_id=owner.id,
        )


def test_create_and_update_requirement_mapping_preserves_integrity(db_session) -> None:
    owner, _, risk_item = _create_risk_item_context(db_session)
    annex_requirement = _create_annex_requirement(db_session)
    other_annex_requirement = _create_annex_requirement(db_session, code_prefix="ANNEX-OTHER")
    service = RequirementMappingService(db_session)

    created = service.create(
        RequirementMappingCreate(
            risk_item_id=risk_item.id,
            annex_requirement_id=annex_requirement.id,
            engineering_requirement_ref="ENG-REQ-001",
            sdl_activity="Threat modeling",
            implementation_status=RequirementImplementationStatus.in_progress,
            evidence_summary="Initial evidence summary",
        ),
        actor_user_id=owner.id,
    )

    assert created.risk_item_id == risk_item.id
    assert created.annex_requirement_id == annex_requirement.id
    assert created.engineering_requirement_ref == "ENG-REQ-001"
    assert created.implementation_status == RequirementImplementationStatus.in_progress

    updated = service.update(
        created.id,
        RequirementMappingUpdate(
            annex_requirement_id=other_annex_requirement.id,
            engineering_requirement_ref="ENG-REQ-002",
            sdl_activity="Security testing",
            implementation_status=RequirementImplementationStatus.verified,
            evidence_summary="Verified by test evidence",
        ),
        actor_user_id=owner.id,
    )

    assert updated.id == created.id
    assert updated.annex_requirement_id == other_annex_requirement.id
    assert updated.engineering_requirement_ref == "ENG-REQ-002"
    assert updated.sdl_activity == "Security testing"
    assert updated.implementation_status == RequirementImplementationStatus.verified
    assert updated.evidence_summary == "Verified by test evidence"


def test_update_requirement_mapping_rejects_invalid_foreign_keys(db_session) -> None:
    owner, _, risk_item = _create_risk_item_context(db_session)
    annex_requirement = _create_annex_requirement(db_session)
    service = RequirementMappingService(db_session)

    created = service.create(
        RequirementMappingCreate(
            risk_item_id=risk_item.id,
            annex_requirement_id=annex_requirement.id,
            engineering_requirement_ref="ENG-REQ-003",
            sdl_activity="Code review",
            implementation_status=RequirementImplementationStatus.planned,
            evidence_summary="Initial state",
        ),
        actor_user_id=owner.id,
    )

    with pytest.raises(ValueError, match="Annex requirement not found"):
        service.update(
            created.id,
            RequirementMappingUpdate(annex_requirement_id=uuid4()),
            actor_user_id=owner.id,
        )

    with pytest.raises(ValueError, match="Risk item not found"):
        service.update(
            created.id,
            RequirementMappingUpdate(risk_item_id=uuid4()),
            actor_user_id=owner.id,
        )


def _create_risk_item_context(db_session):
    owner = User(
        email=f"user-{uuid4()}@example.com",
        full_name="Security Engineer",
        hashed_password="hashed-password",
        is_active=True,
    )

    product = Product(
        product_code=f"PRD-{uuid4()}",
        name="Connected Device",
        description="Device under assessment",
        manufacturer_name="Example Manufacturer",
        intended_use="Connected service delivery",
        product_type="software",
    )

    db_session.add_all([owner, product])
    db_session.flush()

    assessment = RiskAssessment(
        product_id=product.id,
        product_release_id=None,
        title="Product assessment",
        system_version=1,
        user_version=None,
        status=RiskAssessmentStatus.draft,
        methodology="STRIDE",
        summary="Initial draft",
        owner_user_id=owner.id,
    )
    db_session.add(assessment)
    db_session.flush()

    risk_item = RiskItem(
        risk_assessment_id=assessment.id,
        title="Weak authentication",
        description="Authentication controls may be bypassed.",
        threat_scenario="Remote attacker targets login flow.",
        asset_affected="Access control",
        likelihood=RiskLevel.high,
        impact=RiskLevel.high,
        risk_level=RiskLevel.high,
        mitigation_plan="Strengthen authentication controls and rate limiting.",
        residual_risk_level=RiskLevel.medium,
        status=RiskItemStatus.open,
        owner_user_id=owner.id,
    )
    db_session.add(risk_item)
    db_session.commit()

    return owner, assessment, risk_item


def _create_annex_requirement(db_session, code_prefix: str = "ANNEX-TEST") -> AnnexRequirement:
    requirement = AnnexRequirement(
        code=f"{code_prefix}-{uuid4()}",
        title="Annex Requirement",
        description="Requirement used for integrity testing.",
        annex_part=AnnexPart.part_i,
        is_active=True,
    )
    db_session.add(requirement)
    db_session.flush()
    return requirement