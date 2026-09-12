from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.api.deps import get_current_user
from app.api.routes.external_findings import router
from app.core.database import get_db
from app.core.exceptions import register_exception_handlers
from app.models.audit_log_event import AuditLogEvent
from app.models.base import utc_now
from app.models.ingestion_key import IngestionKey
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import Role, UserRole
from app.models.sbom_record import SbomRecord
from app.models.sbom_vulnerability_finding import SbomVulnerabilityFinding
from app.models.system_setting import SystemSetting
from app.models.vulnerability_report import VulnerabilityReport
from app.models.enums import VexStatus
from app.tests.integration.test_vulnerability_assessment import _create_product_and_release, _create_test_user


@pytest.fixture
def setup(db_session):
    db = db_session
    user = _create_test_user(db)
    role = Role(name=f"import-admin-{uuid4()}")
    permission = db.scalar(select(Permission).where(Permission.key == "admin_manage_users"))
    if permission is None:
        permission = Permission(key="admin_manage_users")
        db.add(permission)
    db.add(role)
    db.flush()
    db.add_all([RolePermission(role_id=role.id, permission_id=permission.id), UserRole(user_id=user.id, role_id=role.id)])
    release = _create_product_and_release(db)
    sbom = SbomRecord(product_release_id=release.id, components_json=[{"name": "example", "version": "1.0"}])
    db.add(sbom)
    db.flush()
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)

    def database():
        savepoint = db.begin_nested()
        try:
            yield db
        except Exception:
            if savepoint.is_active:
                savepoint.rollback()
            raise

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)
    issued = client.post("/admin/ingestion-keys", json={"name": "Test sync", "source": "dependency-track", "sbom_record_id": str(sbom.id)})
    assert issued.status_code == 201, issued.text
    payload = {"source": "dependency-track", "findings": [{
        "external_id": "project:component:vuln", "source_updated_at": "2026-09-01T00:00:00Z",
        "component_name": "example", "component_version": "1.0", "component_purl": "pkg:pypi/example@1.0",
        "vulnerability_id": "CVE-2026-1234", "cvss_score": 8.8,
        "assessment": {"vex_status": "affected", "rationale": "Reachable code", "assessed_at": "2026-09-01T00:00:00Z"},
    }]}
    return SimpleNamespace(db=db, user=user, release=release, sbom=sbom, client=client, app=app,
                           key=issued.json(), headers={"X-CRANE-Ingestion-Key": issued.json()["token"]},
                           url=f"/sbom-records/{sbom.id}/external-vulnerability-findings", payload=payload)


def send(s, payload=None):
    return s.client.put(s.url, json=payload or s.payload, headers=s.headers)


def test_retries_updates_history_and_disabled_scanning(setup):
    s = setup
    s.db.merge(SystemSetting(id=1, vulnerability_scanning_enabled=False))
    response = send(s)
    assert response.status_code == 200, response.text
    assert response.json()["created"] == 1
    assert send(s).json()["unchanged"] == 1
    report = s.db.scalar(select(VulnerabilityReport).where(VulnerabilityReport.product_release_id == s.release.id))
    assert report.source.value == "external"
    assert s.release.has_known_exploitable_vulnerabilities is True
    changed = deepcopy(s.payload)
    changed["findings"][0]["source_updated_at"] = "2026-09-02T00:00:00Z"
    changed["findings"][0]["assessment"].update(vex_status="not_affected", rationale="Unused function", assessed_at="2026-09-02T00:00:00Z")
    assert send(s, changed).json()["updated"] == 1
    assert report.vex_status == VexStatus.not_affected
    assert s.release.has_known_exploitable_vulnerabilities is False
    assert send(s).json()["stale"] == 1
    events = s.db.scalars(select(AuditLogEvent).where(AuditLogEvent.entity_id == report.id, AuditLogEvent.action_type == "vulnerability_report.external_imported")).all()
    assert len(events) == 2
    assert events[-1].details_json["before"]["assessment"]["rationale"] == "Reachable code"
    assert s.db.scalar(select(func.count()).select_from(SbomVulnerabilityFinding).where(SbomVulnerabilityFinding.sbom_record_id == s.sbom.id)) == 1


def test_local_assessment_preserved_and_suppression_not_fixed(setup):
    s = setup
    assert send(s).status_code == 200
    report = s.db.scalar(select(VulnerabilityReport).where(VulnerabilityReport.product_release_id == s.release.id))
    report.exploitability_rationale = "CRANE reviewer decision"
    report.exploitability_assessed_at = utc_now()
    s.db.flush()
    changed = deepcopy(s.payload)
    changed["findings"][0].update(source_updated_at="2026-09-02T00:00:00Z", suppressed=True)
    changed["findings"][0]["assessment"]["vex_status"] = "fixed"
    response = send(s, changed)
    assert response.json()["assessment_conflicts"] == ["project:component:vuln"]
    assert send(s, changed).json()["assessment_conflicts"] == ["project:component:vuln"]
    assert report.vex_status == VexStatus.affected
    assert report.exploitability_rationale == "CRANE reviewer decision"
    assert s.release.has_known_exploitable_vulnerabilities is True


def test_authentication_scope_expiry_revocation_and_secret_storage(setup):
    s = setup
    key = s.db.get(IngestionKey, s.key["id"])
    assert key.token_hash != s.key["token"] and len(key.token_hash) == 64
    assert "token" not in s.client.get("/admin/ingestion-keys").json()[0]
    assert s.client.put(s.url, json=s.payload).status_code == 401
    assert s.client.put(s.url, json=s.payload, headers={"X-CRANE-Ingestion-Key": "bad"}).status_code == 401
    assert s.client.put(f"/sbom-records/{uuid4()}/external-vulnerability-findings", json=s.payload, headers=s.headers).status_code == 403
    wrong_source = {**s.payload, "source": "other"}
    assert send(s, wrong_source).status_code == 403
    key.expires_at = utc_now() - timedelta(seconds=1)
    s.db.flush()
    assert send(s).status_code == 401
    key.expires_at = utc_now() + timedelta(days=1)
    s.db.flush()
    assert s.client.delete(f"/admin/ingestion-keys/{key.id}").status_code == 204
    assert send(s).status_code == 401
    s.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(roles=[])
    assert s.client.get("/admin/ingestion-keys").status_code == 403


def test_invalid_batches_and_conflicts_are_atomic(setup):
    s = setup
    assert send(s).status_code == 200
    duplicate = deepcopy(s.payload)
    duplicate["findings"].append(deepcopy(duplicate["findings"][0]))
    assert send(s, duplicate).status_code == 422
    invalid = deepcopy(s.payload)
    invalid["findings"][0]["cvss_score"] = 11
    assert send(s, invalid).status_code == 422
    conflict = deepcopy(s.payload)
    conflict["findings"][0]["summary"] = "Different data at identical timestamp"
    extra = deepcopy(conflict["findings"][0])
    extra["external_id"] = "new-finding"
    conflict["findings"].insert(0, extra)
    assert send(s, conflict).status_code == 409
    assert s.db.scalar(select(func.count()).select_from(SbomVulnerabilityFinding).where(SbomVulnerabilityFinding.sbom_record_id == s.sbom.id)) == 1


def test_unassessed_is_unknown_and_absent_findings_are_retained(setup):
    s = setup
    s.payload["findings"][0]["assessment"]["vex_status"] = "under_investigation"
    assert send(s).status_code == 200
    report = s.db.scalar(select(VulnerabilityReport).where(VulnerabilityReport.product_release_id == s.release.id))
    assert report.is_exploitable is None
    assert send(s, {"source": "dependency-track", "findings": []}).status_code == 200
    assert s.db.get(VulnerabilityReport, report.id) is not None
