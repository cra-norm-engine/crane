"""Pull Dependency-Track findings using the existing external-import transaction."""
from __future__ import annotations

import base64
import hashlib
import ipaddress
import logging
import socket
from datetime import timedelta
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from cryptography.fernet import Fernet, InvalidToken
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.config import settings
from app.core.exceptions import AppException, ConflictException, NotFoundException, ValidationException
from app.core.permissions import Permission, require_permissions
from app.models.base import utc_now
from app.models.dependency_track import DependencyTrackConnection
from app.models.sbom_vulnerability_finding import SbomVulnerabilityFinding
from app.models.user import User
from app.schemas.dependency_track import ProjectOption
from app.schemas.external_finding import ExternalFinding, ExternalFindingsImport, ImportResult
from app.services.external_finding_service import import_external_findings

logger = logging.getLogger(__name__)


def credential_cipher() -> Fernet:
    # Same encryption convention as the existing Jira integration.
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest()))


def get_json(server_url: str, api_key: str, path: str, params: dict | None = None):
    url = urlsplit(server_url)
    try:
        addresses = [ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(url.hostname, url.port or (443 if url.scheme == "https" else 80), type=socket.SOCK_STREAM)]
    except (OSError, ValueError) as exc:
        raise ValidationException("Dependency-Track address could not be resolved. Check the backend URL.") from exc
    # Administrators may connect to private installations. Metadata/link-local and
    # unspecified destinations are never Dependency-Track servers.
    if any(ip.is_link_local or ip.is_unspecified or ip.is_multicast for ip in addresses):
        raise ValidationException("This server address is not allowed")
    if url.scheme == "http" and any(not (ip.is_private or ip.is_loopback) for ip in addresses):
        raise ValidationException("Use HTTPS for a public Dependency-Track server")
    try:
        with httpx.Client(timeout=30, follow_redirects=False, trust_env=False) as client:
            response = client.get(server_url + path, headers={"X-Api-Key": api_key}, params=params)
            if response.status_code in {401, 403}:
                raise ValidationException("Dependency-Track rejected the API key. Grant VIEW_PORTFOLIO and VIEW_VULNERABILITY and project access to its team.")
            if 300 <= response.status_code < 400:
                raise ValidationException("The URL redirects. Enter the final Dependency-Track backend URL.")
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        # Do not expose remote response bodies, request headers, or credentials.
        raise ValidationException("Could not read Dependency-Track. Check its backend URL, availability, and TLS certificate.") from exc


def list_projects(server_url: str, api_key: str) -> list[ProjectOption]:
    projects = []
    for page in range(1, 101):
        data = get_json(server_url, api_key, "/api/v1/project", {"pageNumber": page, "pageSize": 100})
        if not isinstance(data, list):
            raise ValidationException("The server did not return projects. Use the backend URL, not the web interface URL.")
        try:
            projects.extend(ProjectOption.model_validate(item) for item in data)
        except ValidationError as exc:
            raise ValidationException("Dependency-Track returned an unsupported project response") from exc
        if len(data) < 100:
            return projects
    raise ValidationException("More than 10,000 projects are visible. Limit this API team's project access.")


def normalize_findings(items: list, project_id: UUID, timestamp) -> list[ExternalFinding]:
    findings = []
    states = {"EXPLOITABLE": "affected", "NOT_AFFECTED": "not_affected", "FALSE_POSITIVE": "not_affected",
              "RESOLVED": "fixed", "IN_TRIAGE": "under_investigation", "NOT_SET": "under_investigation"}
    try:
        for item in items:
            component, vuln = item["component"], item["vulnerability"]
            analysis = item.get("analysis") or {}
            state = analysis.get("state", "NOT_SET")
            severity = str(vuln.get("severity", "")).lower()
            assessment = None
            if state in states:
                assessment = {"vex_status": states[state], "rationale": analysis.get("detail") or f"Dependency-Track analysis state: {state}. No analyst notes supplied.",
                              "assessed_at": timestamp, "assessed_by": "Dependency-Track export snapshot"}
            findings.append(ExternalFinding(
                external_id=item.get("matrix") or f'{project_id}:{component["uuid"]}:{vuln["uuid"]}',
                source_updated_at=timestamp, component_name=component["name"], component_version=component.get("version"),
                component_purl=component.get("purl"), vulnerability_id=vuln["vulnId"],
                aliases=sorted({v for alias in (vuln.get("aliases") or []) for k, v in alias.items() if k in {"cveId", "ghsaId", "osvId"} and isinstance(v, str)}),
                summary=vuln.get("description") or vuln.get("title"),
                severity=severity if severity in {"critical", "high", "medium", "low", "informational"} else None,
                cvss_score=next((vuln[k] for k in ("cvssV4BaseScore", "cvssV3BaseScore", "cvssV2BaseScore") if vuln.get(k) is not None), None),
                cvss_vector=next((vuln[k] for k in ("cvssV4Vector", "cvssV3Vector", "cvssV2Vector") if vuln.get(k)), None),
                epss_score=vuln.get("epssScore"), epss_percentile=vuln.get("epssPercentile"),
                suppressed=analysis.get("isSuppressed", False), source_analysis_state=state, assessment=assessment,
            ))
    except (KeyError, TypeError, AttributeError, ValidationError) as exc:
        raise ValidationException("Dependency-Track returned an unsupported finding. No findings were imported.") from exc
    if len({item.external_id for item in findings}) != len(findings):
        raise ValidationException("Dependency-Track returned duplicate finding identifiers")
    return findings


def sync_connection(db: Session, connection_id: UUID, *, scheduled: bool = False) -> DependencyTrackConnection:
    connection = db.scalar(select(DependencyTrackConnection).where(DependencyTrackConnection.id == connection_id).with_for_update(skip_locked=True))
    if connection is None:
        raise ConflictException("This connection is already syncing or has been removed")
    if scheduled and (not connection.automatic_sync or (connection.last_attempt_at and connection.last_attempt_at > utc_now() - timedelta(hours=1))):
        db.commit()
        return connection
    connection.last_attempt_at = utc_now()
    try:
        # Nested transaction rolls back every batch on failure, retaining status.
        with db.begin_nested():
            owner = db.get(User, connection.created_by_user_id)
            if owner is None or not owner.is_active or owner.must_change_password:
                raise ValidationException("The connection owner must be an active administrator")
            require_permissions(owner, {Permission.admin_manage_users})
            api_key = credential_cipher().decrypt(connection.api_key_encrypted.encode()).decode()
            timestamp = utc_now()
            data = get_json(connection.server_url, api_key, f"/api/v1/finding/project/{connection.project_id}", {"suppressed": "true"})
            if not isinstance(data, list):
                raise ValidationException("Dependency-Track did not return a findings list")
            findings = normalize_findings(data, connection.project_id, timestamp)
            source = "dependency-track-" + hashlib.sha256(connection.server_url.encode()).hexdigest()[:16]
            existing = {row.external_id: row.external_payload_json for row in db.scalars(select(SbomVulnerabilityFinding).where(
                SbomVulnerabilityFinding.sbom_record_id == connection.sbom_record_id,
                SbomVulnerabilityFinding.external_source == source,
            ))}
            # Poll time is not a new assessment. Preserve snapshot timestamps when
            # the remote content has not changed, making hourly polling a no-op.
            for item in findings:
                previous = existing.get(item.external_id)
                if previous:
                    candidate = item.model_dump(mode="json")
                    candidate["source_updated_at"] = previous["source_updated_at"]
                    if candidate["assessment"] and previous.get("assessment"):
                        candidate["assessment"]["assessed_at"] = previous["assessment"]["assessed_at"]
                    if candidate == previous:
                        item.source_updated_at = ExternalFinding.model_validate(previous).source_updated_at
                        item.assessment = ExternalFinding.model_validate(previous).assessment
            result = ImportResult()
            for offset in range(0, len(findings), 500):
                batch = import_external_findings(db, connection.sbom_record_id, ExternalFindingsImport(source=source, findings=findings[offset:offset + 500]), actor_user_id=owner.id, commit=False)
                for field in ("created", "updated", "unchanged", "stale"):
                    setattr(result, field, getattr(result, field) + getattr(batch, field))
                result.assessment_conflicts.extend(batch.assessment_conflicts)
            connection.last_result = result.model_dump()
            connection.last_synced_at = utc_now()
            connection.last_error = None
            create_audit_event(db, actor_user_id=owner.id, action_type="dependency_track.synced", entity_type="dependency_track_connection", entity_id=connection.id, status="success", details_json=result.model_dump())
    except (AppException, InvalidToken) as exc:
        connection.last_error = exc.message if isinstance(exc, AppException) else "Stored credentials cannot be decrypted. Reconnect Dependency-Track."
    except Exception:
        logger.exception("Dependency-Track sync failed for connection %s", connection_id)
        connection.last_error = "Synchronization failed. No changes from this attempt were saved. Retry or check the server logs."
    db.commit()
    return connection


def get_connection(db: Session, connection_id: UUID) -> DependencyTrackConnection:
    item = db.scalar(select(DependencyTrackConnection).where(DependencyTrackConnection.id == connection_id).with_for_update())
    if item is None:
        raise NotFoundException("Dependency-Track connection not found")
    return item


def run_due_syncs() -> None:
    from app.core.database import SessionLocal
    with SessionLocal() as db:
        ids = list(db.scalars(select(DependencyTrackConnection.id).where(DependencyTrackConnection.automatic_sync.is_(True))))
    for connection_id in ids:
        with SessionLocal() as db:
            try:
                sync_connection(db, connection_id, scheduled=True)
            except ConflictException:
                db.rollback()
