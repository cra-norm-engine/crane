# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import base64
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID

import httpx
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy.orm import Session

from app.core.audit import AuditLogger
from app.core.config import settings
from app.models.enums import AuditStatus
from app.models.system_setting import SystemSetting
from app.schemas.system_update import (
    SystemUpdatePolicy,
    SystemUpdateStatus,
    UpdateManifest,
)

_SETTINGS_ID = 1
_CHECK_STATE = "check-state.json"
_OPERATION_STATE = "operation-state.json"
_POLICY_STATE = "update-policy.json"


class UpdateVerificationError(ValueError):
    pass


def _version_tuple(value: str) -> tuple[int, int, int]:
    core = value.lstrip("v").split("+", 1)[0].split("-", 1)[0]
    parts = core.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Invalid CRANE version: {value}")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def is_newer_version(candidate: str, installed: str) -> bool:
    return _version_tuple(candidate) > _version_tuple(installed)


def _state_path(name: str) -> Path:
    return settings.update_state_dir / name


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, separators=(",", ":"), default=str)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    temporary.chmod(0o640)
    temporary.replace(path)


def verify_manifest(payload: bytes, signature: bytes, public_key_pem: bytes) -> UpdateManifest:
    try:
        key = serialization.load_pem_public_key(public_key_pem)
        if not isinstance(key, Ed25519PublicKey):
            raise UpdateVerificationError("Update key must be Ed25519")
        key.verify(signature, payload)
        manifest = UpdateManifest.model_validate_json(payload)
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise UpdateVerificationError("Update manifest signature or content is invalid") from exc
    if manifest.expires_at <= datetime.now(UTC):
        raise UpdateVerificationError("Update manifest has expired")
    return manifest


def fetch_verified_manifest() -> UpdateManifest:
    if not settings.update_check_enabled:
        raise UpdateVerificationError("Update checks are disabled")
    try:
        public_key = settings.update_public_key_path.read_bytes()
    except OSError as exc:
        raise UpdateVerificationError("Update verification key is not installed") from exc
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            payload_response = client.get(settings.update_manifest_url)
            signature_response = client.get(f"{settings.update_manifest_url}.sig")
            payload_response.raise_for_status()
            signature_response.raise_for_status()
        signature = base64.b64decode(signature_response.content, validate=True)
    except (httpx.HTTPError, ValueError) as exc:
        raise UpdateVerificationError("Could not retrieve the signed update manifest") from exc
    return verify_manifest(payload_response.content, signature, public_key)


def _settings_row(db: Session) -> SystemSetting:
    row = db.get(SystemSetting, _SETTINGS_ID)
    if row is None:
        row = SystemSetting(
            id=_SETTINGS_ID,
            vulnerability_scanning_enabled=settings.vulnerability_scanning_enabled,
        )
        db.add(row)
        db.flush()
    return row


def get_policy(db: Session) -> SystemUpdatePolicy:
    row = db.get(SystemSetting, _SETTINGS_ID)
    if row is None:
        return SystemUpdatePolicy(
            policy="manual",
            channel="stable",
            maintenance_day=6,
            maintenance_hour_utc=2,
            postponed_until=None,
        )
    return SystemUpdatePolicy(
        policy=row.update_policy,
        channel=row.update_channel,
        maintenance_day=row.update_maintenance_day,
        maintenance_hour_utc=row.update_maintenance_hour_utc,
        postponed_until=row.update_postponed_until,
    )


def set_policy(db: Session, payload: SystemUpdatePolicy, actor_user_id: UUID) -> SystemUpdatePolicy:
    row = _settings_row(db)
    previous = get_policy(db).model_dump(mode="json")
    row.update_policy = payload.policy
    row.update_channel = payload.channel
    row.update_maintenance_day = payload.maintenance_day
    row.update_maintenance_hour_utc = payload.maintenance_hour_utc
    row.update_postponed_until = payload.postponed_until
    _write_json(_state_path(_POLICY_STATE), payload.model_dump(mode="json"))
    AuditLogger(db).log_event(
        actor_user_id=actor_user_id,
        action_type="admin.system_update_policy.updated",
        entity_type="system_setting",
        status=AuditStatus.success.value,
        details_json={"previous": previous, "current": payload.model_dump(mode="json")},
    )
    db.commit()
    return get_policy(db)


def check_for_updates() -> dict[str, object]:
    checked_at = datetime.now(UTC)
    try:
        manifest = fetch_verified_manifest()
        state: dict[str, object] = {
            "last_checked_at": checked_at.isoformat(),
            "manifest": manifest.model_dump(mode="json"),
            "last_error": None,
        }
    except UpdateVerificationError as exc:
        state = {
            "last_checked_at": checked_at.isoformat(),
            "manifest": None,
            "last_error": str(exc),
        }
    _write_json(_state_path(_CHECK_STATE), state)
    return state


def get_status(db: Session) -> SystemUpdateStatus:
    policy = get_policy(db)
    state = _read_json(_state_path(_CHECK_STATE)) or {}
    raw_manifest = state.get("manifest")
    manifest = UpdateManifest.model_validate(raw_manifest) if isinstance(raw_manifest, dict) else None
    last_error = state.get("last_error") if isinstance(state.get("last_error"), str) else None
    if manifest and manifest.expires_at <= datetime.now(UTC):
        manifest = None
        last_error = "Cached update metadata has expired; run Check now"
    available = bool(
        manifest
        and manifest.channel == policy.channel
        and is_newer_version(manifest.version, settings.app_version)
    )
    postponed = bool(policy.postponed_until and policy.postponed_until > datetime.now(UTC))
    auto_type = bool(
        manifest
        and (policy.policy == "all" or (policy.policy == "security" and manifest.update_type == "security"))
    )
    eligible = bool(available and not postponed and manifest and manifest.automatic_update_allowed and auto_type)
    return SystemUpdateStatus(
        installed_version=settings.app_version,
        configured=settings.update_public_key_path.is_file(),
        update_checks_enabled=settings.update_check_enabled,
        policy=policy,
        update_available=available,
        automatic_update_eligible=eligible,
        manifest=manifest,
        last_checked_at=state.get("last_checked_at"),
        last_error=last_error,
        last_operation=_read_json(_state_path(_OPERATION_STATE)),
    )
