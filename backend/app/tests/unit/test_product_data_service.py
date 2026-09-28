from __future__ import annotations

from copy import deepcopy
from uuid import UUID

import pytest

from app.schemas.product_data import ProductDataBundle
from app.services.product_data_service import ProductDataService, _digest

ACTOR_ID = UUID("11111111-1111-1111-1111-111111111111")
PRODUCT_ID = "22222222-2222-2222-2222-222222222222"
RELEASE_ID = "33333333-3333-3333-3333-333333333333"


def bundle_dict() -> dict:
    return {
        "_meta": {
            "schema_version": "2.0",
            "exported_at": "2026-09-28T10:00:00+00:00",
            "tool": "CRANE CRA Compliance Tool",
            "bundle_id": "44444444-4444-4444-4444-444444444444",
            "sensitivity": "confidential",
        },
        "manifest": {},
        "product": {
            "id": PRODUCT_ID,
            "product_code": "CRANE-DEMO",
            "name": "CRANE demo",
            "manufacturer_name": "Example manufacturer",
            "intended_use": "Transfer test",
            "product_type": "Software",
        },
        "releases": [{
            "id": RELEASE_ID,
            "product_id": PRODUCT_ID,
            "release_status": "released",
            "vulnerability_reports": [],
            "security_updates": [],
            "sbom_records": [],
        }],
        "risk_assessments": [],
        "security_advisories": [],
        "cvd_policies": [],
        "support_periods": [],
        "certification_records": [],
        "changes": [],
    }


class FakeSession:
    def __init__(self, *, fail_on_add: int | None = None, scalar_results: list[object | None] | None = None) -> None:
        self.fail_on_add = fail_on_add
        self.scalar_results = iter(scalar_results or [])
        self.add_count = 0
        self.rolled_back = False
        self.committed = False

    def scalar(self, _statement):
        return next(self.scalar_results, None)

    def add(self, _record) -> None:
        self.add_count += 1
        if self.fail_on_add == self.add_count:
            raise RuntimeError("injected import failure")

    def flush(self) -> None:
        return None

    def rollback(self) -> None:
        self.rolled_back = True

    def commit(self) -> None:
        self.committed = True


def test_validation_normalizes_workflow_state() -> None:
    raw = bundle_dict()
    service = ProductDataService(FakeSession())
    result, prepared = service.validate(ProductDataBundle.model_validate(raw), raw, actor_id=ACTOR_ID)

    assert result.valid
    assert prepared.releases[0][1]["release_status"] == "draft"
    assert result.counts["releases"] == 1


def test_integrity_detects_tampering() -> None:
    raw = bundle_dict()
    digest, _ = _digest(raw)
    raw["integrity"] = {"algorithm": "sha256", "digest_scope": "bundle_without_integrity", "sha256": digest}
    tampered = deepcopy(raw)
    tampered["product"]["name"] = "Modified after signing"

    result, _ = ProductDataService(FakeSession()).validate(
        ProductDataBundle.model_validate(tampered), tampered, actor_id=ACTOR_ID
    )

    assert not result.valid
    assert result.signature_status == "invalid"


def test_existing_source_code_uses_available_clone_code() -> None:
    raw = bundle_dict()
    session = FakeSession(scalar_results=[object(), object(), None, None])

    result, prepared = ProductDataService(session).validate(
        ProductDataBundle.model_validate(raw), raw, actor_id=ACTOR_ID
    )

    assert result.valid
    assert result.suggested_product_code == "CRANE-DEMO-2"
    assert prepared.product and prepared.product["product_code"] == "CRANE-DEMO-2"
    assert any(issue.path == "product.product_code" and issue.level == "will_adjust" for issue in result.issues)


def test_import_failure_rolls_back_the_whole_transaction() -> None:
    raw = bundle_dict()
    session = FakeSession(fail_on_add=2)

    with pytest.raises(RuntimeError, match="injected import failure"):
        ProductDataService(session).import_bundle(
            ProductDataBundle.model_validate(raw),
            raw,
            actor_id=ACTOR_ID,
            product_name=None,
            product_code=None,
        )

    assert session.rolled_back
    assert not session.committed
