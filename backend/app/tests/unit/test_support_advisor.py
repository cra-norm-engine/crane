from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.exceptions import ConflictException, ForbiddenException, ValidationException
from app.schemas.support_advisor import AssessmentCreate, AssessmentReview
from app.services.support_advisor_rules import assess
from app.services.support_advisor_service import SupportAdvisorService


def payload(**changes):
    values = dict(context_version="a" * 64, product_release_id=uuid4(), support_start=date(2026, 1, 1),
                  support_end=date(2038, 1, 1), expected_use_end=date(2041, 1, 1),
                  expected_use_basis="documented", rationale="Reasoned proportionality determination.",
                  evidence_ids=[uuid4()])
    return AssessmentCreate(**(values | changes))


def component(**changes):
    return dict(id=str(uuid4()), link_id=str(uuid4()), name="Core library", version="1.0",
                support_start_date="2026-01-01", support_end_date="2034-01-01",
                support_verified_at="2026-01-01T00:00:00Z", support_reference_url="https://supplier.example/terms",
                support_scope="Security patches for version 1.0", criticality="high", is_core_function=True) | changes


def rules(result):
    return {f["rule"] for f in result["findings"]}


def test_primary_case_is_review_not_automatic_noncompliance():
    result = assess(payload(), [component()])
    assert result["general_minimum_met"]
    assert {"SP-002", "SP-003", "SP-004"} <= rules(result)
    assert result["components"][0]["gap_days"] == (date(2038, 1, 1) - date(2034, 1, 1)).days
    assert result["legal_admissibility"] == "review_required"
    assert result["economic_attractiveness"] == "not_assessed"


def test_different_start_dates_use_actual_ends_and_clip_gap_to_system_interval():
    result = assess(payload(), [component(support_start_date="2010-01-01", support_end_date="2020-01-01")])
    assert result["components"][0]["gap_days"] == (date(2038, 1, 1) - date(2026, 1, 1)).days
    result = assess(payload(), [component(support_start_date="2028-01-01", support_end_date="2045-01-01")])
    assert result["components"][0]["gap_days"] == 730


@pytest.mark.parametrize("changes", [{"support_end_date": None}, {"support_verified_at": None}, {"support_reference_url": None}, {"support_scope": None}, {"support_start_date": None}])
def test_missing_commitment_evidence_is_unknown(changes):
    result = assess(payload(), [component(**changes)])
    assert result["components"][0]["status"] == "UNKNOWN"
    assert "SP-005" in result["approval_blockers"]


def test_documented_shorter_use_exception_and_five_year_calendar_boundary():
    short = payload(support_end=date(2029, 1, 1), expected_use_end=date(2029, 1, 1))
    assert "SP-001" not in rules(assess(short, [component()]))
    assert "SP-001" in rules(assess(short.model_copy(update={"evidence_ids": []}), [component()]))
    leap = payload(support_start=date(2028, 2, 29), support_end=date(2033, 2, 28))
    assert assess(leap, [component()])["general_minimum_met"]


def test_remediation_is_submitted_for_review_never_auto_verified():
    c = component()
    p = payload(remediations=[dict(component_link_id=c["link_id"], approach="independent_patching",
                                  rationale="We can maintain this version through the support end.", evidence_ids=[uuid4()])])
    result = assess(p, [c])
    assert result["components"][0]["status"] == "REMEDIATION_REVIEW"
    assert "SP-004" not in rules(result)
    assert result["technical_readiness"] == "review_required"


def test_empty_inventory_and_unlinked_sbom_versions_block_approval():
    assert "SP-005" in assess(payload(), [])["approval_blockers"]
    c = component(support_end_date="2045-01-01")
    result = assess(payload(), [c], [{"components_json": [{"name": c["name"], "version": "2.0"}]}])
    assert "SP-005" in result["approval_blockers"]


@pytest.mark.parametrize("change", [{"support_end": "2020-01-01"}, {"rationale": "          "}, {"expected_use_end": "2025-01-01"}])
def test_invalid_inputs_rejected(change):
    with pytest.raises(ValidationError):
        payload(**change)


def test_cross_release_evidence_and_remediation_rejected():
    service = SupportAdvisorService(Mock())
    service.context = Mock(return_value={"context_version": "a" * 64, "evidence": [], "components": [], "sboms": []})
    with pytest.raises(ValidationException, match="Evidence must belong"):
        service.create(uuid4(), payload(), SimpleNamespace(id=uuid4()))
    p = payload(evidence_ids=[], remediations=[dict(component_link_id=uuid4(), approach="replacement", rationale="Replace the dependency.", evidence_ids=[uuid4()])])
    with pytest.raises(ValidationException, match="does not belong"):
        service.create(uuid4(), p, SimpleNamespace(id=uuid4()))


def test_approval_guards_self_review_refresh_missing_evidence_and_repeat_decision():
    service = SupportAdvisorService(Mock())
    author, reviewer = uuid4(), uuid4()
    record = SimpleNamespace(status="pending_review", author_id=author, result={"approval_blockers": []})
    service.get = Mock(return_value=record)
    decision = AssessmentReview(decision="approved", reason="Evidence independently reviewed.")
    with pytest.raises(ForbiddenException):
        service.review(uuid4(), uuid4(), decision, SimpleNamespace(id=author))
    service.read = Mock(return_value={"needs_refresh": True})
    with pytest.raises(ConflictException, match="SP-007"):
        service.review(uuid4(), uuid4(), decision, SimpleNamespace(id=reviewer))
    service.read.return_value = {"needs_refresh": False}
    record.result["approval_blockers"] = ["SP-005"]
    with pytest.raises(ValidationException):
        service.review(uuid4(), uuid4(), decision, SimpleNamespace(id=reviewer))
    record.status = "approved"
    with pytest.raises(ConflictException, match="already recorded"):
        service.review(uuid4(), uuid4(), decision, SimpleNamespace(id=reviewer))


def test_approval_records_reviewer_and_audit_and_return_can_have_unresolved_issues():
    service = SupportAdvisorService(Mock())
    reviewer = SimpleNamespace(id=uuid4())
    record = SimpleNamespace(status="pending_review", author_id=uuid4(), result={"approval_blockers": []})
    service.get = Mock(return_value=record)
    service.read = Mock(return_value={"needs_refresh": False})
    service._audit = Mock()
    service.review(uuid4(), uuid4(), AssessmentReview(decision="approved", reason="Reviewed all remediation evidence."), reviewer)
    assert record.status == "approved" and record.reviewer_id == reviewer.id and record.reviewed_at
    service._audit.assert_called_once_with(record, reviewer, "approved")
    record.status = "pending_review"
    record.result["approval_blockers"] = ["SP-005"]
    service.review(uuid4(), uuid4(), AssessmentReview(decision="returned", reason="Please add supplier evidence."), reviewer)
    assert record.status == "returned"


def test_source_change_while_editing_rejects_submission():
    service = SupportAdvisorService(Mock())
    service.context = Mock(return_value={"context_version": "b" * 64})
    with pytest.raises(ConflictException, match="while editing"):
        service.create(uuid4(), payload(), SimpleNamespace(id=uuid4()))


def test_route_permissions_and_report_snapshot_are_enforced():
    # Load this router independently of unrelated optional full-app dependencies.
    import importlib.util
    from pathlib import Path
    from fastapi import HTTPException
    from app.core.permissions import Permission
    from unittest.mock import patch

    spec = importlib.util.spec_from_file_location("advisor_routes_test", Path(__file__).parents[2] / "api/routes/support_advisor.py")
    routes = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(routes)
    user = SimpleNamespace(id=uuid4(), roles=[])
    for dependency in (routes.read, routes.write, routes.review):
        with pytest.raises(HTTPException) as exc:
            dependency(user)
        assert exc.value.status_code == 403
    with patch("app.core.permissions.get_permissions_from_user", return_value=set(routes.read_permissions)):
        assert routes.read(user) is user
        with pytest.raises(HTTPException):
            routes.review(user)
        with patch.object(routes, "SupportAdvisorService") as factory:
            factory.return_value.read.return_value = {"context_snapshot": {"release": "original"}, "needs_refresh": True}
            report = routes.report(uuid4(), uuid4(), Mock(), user)
            assert b'"release":"original"' in report.body
            assert "attachment" in report.headers["content-disposition"]
    permissions = set(routes.read_permissions) | {Permission.support_period_write, Permission.supplier_assessment_approve}
    with patch("app.core.permissions.get_permissions_from_user", return_value=permissions):
        assert routes.review(user) is user


def test_invalid_legacy_component_interval_is_unknown_not_an_inflated_gap():
    result = assess(payload(), [component(support_start_date="2040-01-01", support_end_date="2020-01-01")])
    assert result["components"][0]["status"] == "UNKNOWN"
    assert result["components"][0]["gap_days"] is None


def test_preview_uses_save_rules_without_writing_or_creating_audit_events():
    service = SupportAdvisorService(Mock())
    p = payload()
    service.context = Mock(return_value={"context_version": p.context_version,
        "evidence": [{"id": str(p.evidence_ids[0])}], "components": [component()], "sboms": []})
    service._audit = Mock()
    result = service.preview(uuid4(), p)
    assert result["components"][0]["gap_days"] == 1461
    assert {"SP-002", "SP-003", "SP-004"} <= rules(result)
    service.db.add.assert_not_called()
    service.db.flush.assert_not_called()
    service.db.commit.assert_not_called()
    service._audit.assert_not_called()
    service.read = lambda record: record.result
    assert service.create(uuid4(), p, SimpleNamespace(id=uuid4())) == result


def test_preview_rejects_stale_source_and_foreign_evidence_without_writes():
    service = SupportAdvisorService(Mock())
    service.context = Mock(return_value={"context_version": "b" * 64})
    with pytest.raises(ConflictException):
        service.preview(uuid4(), payload())
    service.context.return_value = {"context_version": "a" * 64, "evidence": [], "components": []}
    with pytest.raises(ValidationException, match="Evidence must belong"):
        service.preview(uuid4(), payload())
    service.db.commit.assert_not_called()
