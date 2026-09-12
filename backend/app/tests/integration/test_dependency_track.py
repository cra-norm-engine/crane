from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.api.deps import get_current_user
from app.api.routes.dependency_track import router
from app.core.exceptions import ValidationException
from app.models.base import utc_now
from app.models.dependency_track import DependencyTrackConnection
from app.models.vulnerability_report import VulnerabilityReport
from app.services.dependency_track_service import sync_connection
from app.tests.integration.test_external_findings import setup as external_setup  # noqa: F401


@pytest.fixture
def connected(external_setup, monkeypatch):  # noqa: F811
    s = external_setup
    s.app.include_router(router)
    s.project = {"uuid": str(uuid4()), "name": "Example product", "version": "1.0"}
    s.remote = [{"component": {"uuid": str(uuid4()), "name": "example", "version": "1.0"},
                 "vulnerability": {"uuid": str(uuid4()), "vulnId": "CVE-2026-1234", "severity": "HIGH"},
                 "analysis": {"state": "EXPLOITABLE", "isSuppressed": True, "detail": "Reachable code"}}]
    s.calls = []

    def remote(url, key, path, params=None):
        assert key == "test-secret"
        s.calls.append((path, params))
        return deepcopy(s.remote if "/finding/" in path else [s.project] if path == "/api/v1/project" else s.project)

    monkeypatch.setattr("app.api.routes.dependency_track.get_json", remote)
    monkeypatch.setattr("app.services.dependency_track_service.get_json", remote)
    s.payload = {"server_url": "https://dtrack.example", "api_key": "test-secret", "project_id": s.project["uuid"], "sbom_record_id": str(s.sbom.id), "automatic_sync": True}
    response = s.client.post("/admin/dependency-track", json=s.payload)
    assert response.status_code == 201, response.text
    s.connection_id = response.json()["id"]
    s.sync_url = f"/admin/dependency-track/{s.connection_id}/sync"
    return s


def test_connect_sync_retry_local_assessment_and_disconnect(connected):
    s = connected
    key = s.db.get(DependencyTrackConnection, UUID(s.connection_id))
    assert "test-secret" not in key.api_key_encrypted
    assert "api_key" not in s.client.get("/admin/dependency-track").text
    test = s.client.post("/admin/dependency-track/test", json={"server_url": s.payload["server_url"], "api_key": "test-secret"})
    assert test.status_code == 200 and test.json()[0]["name"] == "Example product"
    options = s.client.get("/admin/dependency-track/sboms").json()
    assert any(row["id"] == str(s.sbom.id) and row["label"] for row in options)
    first = s.client.post(s.sync_url).json()
    assert first["last_error"] is None
    assert first["last_result"]["created"] == 1
    assert s.client.post(s.sync_url).json()["last_result"]["unchanged"] == 1
    assert s.calls[-1][1] == {"suppressed": "true"}
    report = s.db.scalar(select(VulnerabilityReport).where(VulnerabilityReport.product_release_id == s.release.id))
    assert report.is_exploitable is True  # Suppression does not imply unaffected.
    report.exploitability_rationale = "Local reviewer decision"
    s.db.flush()
    s.remote[0]["analysis"]["state"] = "NOT_AFFECTED"
    result = s.client.post(s.sync_url).json()
    assert len(result["last_result"]["assessment_conflicts"]) == 1
    assert report.exploitability_rationale == "Local reviewer decision"
    assert s.client.patch(f"/admin/dependency-track/{s.connection_id}", json={"automatic_sync": False}).json()["automatic_sync"] is False
    assert s.client.delete(f"/admin/dependency-track/{s.connection_id}").status_code == 204
    assert s.db.get(VulnerabilityReport, report.id) is not None


def test_failed_sync_rolls_back_all_batches_and_records_error(connected, monkeypatch):
    s = connected
    import app.services.dependency_track_service as service
    original = service.import_external_findings

    def fail_after_import(*args, **kwargs):
        original(*args, **kwargs)
        raise ValidationException("Remote snapshot could not be applied")

    monkeypatch.setattr(service, "import_external_findings", fail_after_import)
    result = s.client.post(s.sync_url).json()
    assert result["last_error"] == "Remote snapshot could not be applied"
    assert result["last_synced_at"] is None
    assert not s.db.scalars(select(VulnerabilityReport).where(VulnerabilityReport.product_release_id == s.release.id)).all()


def test_scheduler_throttles_and_inactive_owner_blocks_sync(connected):
    s = connected
    item = sync_connection(s.db, UUID(s.connection_id), scheduled=True)
    assert item.last_synced_at is not None
    count = len(s.calls)
    sync_connection(s.db, UUID(s.connection_id), scheduled=True)
    assert len(s.calls) == count
    item.last_attempt_at = utc_now() - timedelta(hours=2)
    s.user.is_active = False
    s.db.flush()
    item = sync_connection(s.db, item.id, scheduled=True)
    assert "active administrator" in item.last_error
    assert len(s.calls) == count


def test_authorization_invalid_credentials_and_duplicate_mapping(connected):
    s = connected
    assert s.client.post("/admin/dependency-track", json=s.payload).status_code == 409
    assert s.client.post("/admin/dependency-track/test", json={"server_url": "file:///etc/passwd", "api_key": "secret"}).status_code == 422
    s.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(roles=[])
    assert s.client.get("/admin/dependency-track").status_code == 403
    assert s.client.post(s.sync_url).status_code == 403
