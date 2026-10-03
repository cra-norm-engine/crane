from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.exceptions import ValidationException
from app.models.enums import RequirementApplicabilityDecision, RequirementProgressStatus
from app.schemas.requirement_source import RequirementSourceCreate
from app.services.requirement_mapping_service import RequirementMappingService, _validate_applicability_decision
from app.schemas.release_journey import JourneyStepStatus
from app.services.release_journey_service import _requirement_collection_status


def test_requirement_source_requires_a_scope() -> None:
    with pytest.raises(ValidationError):
        RequirementSourceCreate(
            identifier="EN-TEST",
            title="Test standard",
            source_type="standard",
            organization_wide=False,
            product_ids=[],
        )


def test_mandatory_requirement_cannot_be_not_applicable() -> None:
    with pytest.raises(ValidationException):
        _validate_applicability_decision(
            True,
            RequirementApplicabilityDecision.not_applicable,
            "Not relevant",
        )


def test_custom_requirement_uses_existing_finalization_workflow() -> None:
    assert RequirementMappingService._is_finalized(
        RequirementApplicabilityDecision.applicable,
        RequirementProgressStatus.validated,
        [object()],
        [object()],
    )
    assert not RequirementMappingService._is_finalized(
        RequirementApplicabilityDecision.applicable,
        RequirementProgressStatus.implemented,
        [object()],
        [object()],
    )


def test_requirement_collection_journey_status() -> None:
    draft = SimpleNamespace(status="draft", requirements=[])
    published = SimpleNamespace(
        status="published",
        requirements=[SimpleNamespace(status="published", is_active=True)],
    )

    assert _requirement_collection_status([]) == JourneyStepStatus.todo
    assert _requirement_collection_status([draft]) == JourneyStepStatus.in_progress
    assert _requirement_collection_status([published]) == JourneyStepStatus.complete
