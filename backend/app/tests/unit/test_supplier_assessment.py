from datetime import date
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.enums import SupplierAssessmentStatus
from app.schemas.supplier_assessment import (
    AssessmentDecision,
    ComponentLinkUpdate,
    EvidenceLinkCreate,
    MaintainerNotificationUpdate,
)
from app.services.supplier_assessment_service import (
    SupplierAssessmentService,
    classify_component_support,
    match_registered_component,
)


def test_only_draft_assessments_are_editable() -> None:
    SupplierAssessmentService._editable(SimpleNamespace(status="draft"))
    with pytest.raises(ValueError, match="Only draft"):
        SupplierAssessmentService._editable(SimpleNamespace(status="approved"))


def test_decision_reject_requires_reason() -> None:
    with pytest.raises(ValidationError, match="rejection_reason"):
        AssessmentDecision(decision=SupplierAssessmentStatus.rejected, conclusion="Insufficient assurance")


def test_decision_reject_accepts_reason() -> None:
    value = AssessmentDecision(
        decision=SupplierAssessmentStatus.rejected,
        conclusion="Insufficient assurance",
        rejection_reason="Security update commitment is missing",
    )
    assert value.decision is SupplierAssessmentStatus.rejected


def test_evidence_validity_cannot_precede_issue_date() -> None:
    with pytest.raises(ValidationError, match="valid_until"):
        EvidenceLinkCreate(
            evidence_item_id="00000000-0000-0000-0000-000000000001",
            issued_at="2026-08-08",
            valid_until="2026-08-07",
        )


def test_maintainer_notification_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError, match="status"):
        MaintainerNotificationUpdate(status="delivered")


def test_maintainer_notification_supports_operational_states() -> None:
    for status in ("draft", "sent", "acknowledged", "closed"):
        assert MaintainerNotificationUpdate(status=status).status == status


def test_component_link_update_rejects_empty_criticality_rationale() -> None:
    with pytest.raises(ValidationError, match="criticality_rationale"):
        ComponentLinkUpdate(criticality_rationale="")


def test_component_correlation_requires_an_unambiguous_identity() -> None:
    component = SimpleNamespace(id="component-1")
    unique_db = SimpleNamespace(scalars=lambda _stmt: SimpleNamespace(all=lambda: [component]))
    ambiguous_db = SimpleNamespace(scalars=lambda _stmt: SimpleNamespace(all=lambda: [component, SimpleNamespace(id="component-2")]))
    assert match_registered_component(unique_db, "openssl", "3.0", "pkg:generic/openssl@3.0") is component
    assert match_registered_component(ambiguous_db, "openssl", "3.0", "pkg:generic/openssl@3.0") is None


def test_component_support_classification_flags_product_coverage_gap() -> None:
    status, severity, days_left, gap_days = classify_component_support(
        date(2026, 8, 15), date(2027, 8, 15), 180, True, "high", date(2026, 3, 1)
    )

    assert (status, severity, days_left, gap_days) == ("gap", "high", 167, 365)
    assert classify_component_support(None, date(2027, 8, 15), 180, False, "low", date(2026, 3, 1))[:2] == ("unknown", "medium")


def test_component_support_dates_and_unknown_reason_are_validated() -> None:
    with pytest.raises(ValueError, match="on or after"):
        SupplierAssessmentService._validate_component_support(date(2027, 1, 1), date(2026, 1, 1), None)
    with pytest.raises(ValueError, match="required"):
        SupplierAssessmentService._validate_component_support(None, None, "")
