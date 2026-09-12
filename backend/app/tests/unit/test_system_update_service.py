from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.services.system_update_service import (
    UpdateVerificationError,
    is_newer_version,
    verify_manifest,
)


def manifest_bytes() -> bytes:
    now = datetime.now(UTC)
    return json.dumps({
        "schema_version": 1,
        "version": "1.4.0",
        "channel": "stable",
        "update_type": "security",
        "severity": "high",
        "published_at": now.isoformat(),
        "expires_at": (now + timedelta(days=1)).isoformat(),
        "minimum_upgrade_version": "1.0.0",
        "database_revision": "20260912_0085",
        "postgres_major_versions": [16],
        "automatic_update_allowed": True,
        "rollback_mode": "database-restore",
        "backend": {"image": "ghcr.io/cra-norm-engine/crane-backend", "digest": "sha256:" + "a" * 64},
        "frontend": {"image": "ghcr.io/cra-norm-engine/crane-frontend", "digest": "sha256:" + "b" * 64},
        "release_notes_url": "https://github.com/cra-norm-engine/crane/releases/tag/v1.4.0",
    }, separators=(",", ":")).encode()


def test_signed_manifest_and_version_ordering() -> None:
    private_key = Ed25519PrivateKey.generate()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    payload = manifest_bytes()

    verified = verify_manifest(payload, private_key.sign(payload), public_pem)

    assert verified.version == "1.4.0"
    assert verified.backend.immutable_reference.endswith("@sha256:" + "a" * 64)
    assert is_newer_version("1.4.0", "1.3.9")
    assert not is_newer_version("1.4.0", "1.4.0")
    with pytest.raises(UpdateVerificationError):
        verify_manifest(payload + b" ", private_key.sign(payload), public_pem)
