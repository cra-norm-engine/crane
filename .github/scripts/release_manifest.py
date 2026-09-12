#!/usr/bin/env python3
"""Generate canonical, expiring metadata for one immutable CRANE release."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path


def database_head(versions_dir: Path) -> str:
    revisions: set[str] = set()
    parents: set[str] = set()
    for path in versions_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        revision = re.search(r'^revision\s*=\s*["\']([^"\']+)', text, re.MULTILINE)
        parent = re.search(r'^down_revision\s*=\s*["\']([^"\']+)', text, re.MULTILINE)
        if revision:
            revisions.add(revision.group(1))
        if parent:
            parents.add(parent.group(1))
    heads = revisions - parents
    if len(heads) != 1:
        raise SystemExit(f"expected one Alembic head, found: {sorted(heads)}")
    return heads.pop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--backend-digest", required=True)
    parser.add_argument("--frontend-digest", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--metadata", default="updates/release-metadata.json")
    parser.add_argument("--output", default="update-manifest.json")
    args = parser.parse_args()

    version = args.version.removeprefix("v")
    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SystemExit("release tag must be vMAJOR.MINOR.PATCH")
    if metadata["update_type"] == "security" and metadata["severity"] == "none":
        raise SystemExit("security releases require a severity")
    now = datetime.now(UTC).replace(microsecond=0)
    manifest = {
        "schema_version": 1,
        "version": version,
        "channel": "stable",
        "update_type": metadata["update_type"],
        "severity": metadata["severity"],
        "published_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(days=30)).isoformat().replace("+00:00", "Z"),
        "minimum_upgrade_version": metadata["minimum_upgrade_version"],
        "database_revision": database_head(Path("backend/alembic/versions")),
        "postgres_major_versions": metadata["postgres_major_versions"],
        "automatic_update_allowed": metadata["automatic_update_allowed"],
        "rollback_mode": metadata["rollback_mode"],
        "backend": {"image": "ghcr.io/cra-norm-engine/crane-backend", "digest": args.backend_digest},
        "frontend": {"image": "ghcr.io/cra-norm-engine/crane-frontend", "digest": args.frontend_digest},
        "advisory_url": metadata.get("advisory_url"),
        "release_notes_url": f"https://github.com/{args.repository}/releases/tag/v{version}",
        "download_url": f"https://github.com/{args.repository}/releases/tag/v{version}",
    }
    Path(args.output).write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
