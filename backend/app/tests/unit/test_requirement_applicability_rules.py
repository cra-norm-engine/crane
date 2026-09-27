from __future__ import annotations

import pytest

from app.core.exceptions import ValidationException
from app.models.enums import RequirementApplicabilityDecision
from app.services.requirement_mapping_service import _validate_applicability_decision


@pytest.mark.parametrize(
    "code",
    ["ANNEX-I-PART-I-1", "ANNEX-I-PART-II-1", "ANNEX-I-PART-II-8"],
)
def test_mandatory_requirements_cannot_be_not_applicable(code: str) -> None:
    with pytest.raises(ValidationException, match="mandatory"):
        _validate_applicability_decision(
            code,
            RequirementApplicabilityDecision.not_applicable,
            "Not relevant",
        )


def test_optional_requirement_requires_risk_based_rationale() -> None:
    with pytest.raises(ValidationException, match="rationale"):
        _validate_applicability_decision(
            "ANNEX-I-PART-I-6",
            RequirementApplicabilityDecision.not_applicable,
            " ",
        )

    _validate_applicability_decision(
        "ANNEX-I-PART-I-6",
        RequirementApplicabilityDecision.not_applicable,
        "The product stores and transmits no user or operational data.",
    )
