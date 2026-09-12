#!/usr/bin/env bash
set -Eeuo pipefail

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TEST_DIR="$(mktemp -d)"
trap 'rm -rf -- "$TEST_DIR"' EXIT
mkdir -p "$TEST_DIR/bin" "$TEST_DIR/updates" "$TEST_DIR/data/artifacts" "$TEST_DIR/offsite"
cp "$REPO/scripts/tests/fake-docker" "$TEST_DIR/bin/docker"
chmod +x "$TEST_DIR/bin/docker"
printf 'CRANE_VERSION=1.2.0\nPOSTGRES_USER=postgres\nPOSTGRES_DB=cra_compliance\n' > "$TEST_DIR/.env"
printf 'evidence\n' > "$TEST_DIR/data/artifacts/check.txt"

openssl genpkey -algorithm Ed25519 -out "$TEST_DIR/private.pem" >/dev/null 2>&1
openssl pkey -in "$TEST_DIR/private.pem" -pubout -out "$TEST_DIR/public.pem" >/dev/null 2>&1
python3 - "$TEST_DIR/manifest.json" <<'PY'
import json, sys
from datetime import UTC, datetime, timedelta
now = datetime.now(UTC)
value = {
  "schema_version": 1, "version": "1.3.0", "channel": "stable",
  "update_type": "security", "severity": "high",
  "published_at": now.isoformat(), "expires_at": (now + timedelta(days=1)).isoformat(),
  "minimum_upgrade_version": "1.0.0", "database_revision": "head",
  "postgres_major_versions": [16], "automatic_update_allowed": True,
  "rollback_mode": "database-restore",
  "backend": {"image": "ghcr.io/cra-norm-engine/crane-backend", "digest": "sha256:" + "a" * 64},
  "frontend": {"image": "ghcr.io/cra-norm-engine/crane-frontend", "digest": "sha256:" + "b" * 64},
  "release_notes_url": "https://github.com/cra-norm-engine/crane/releases/tag/v1.3.0"
}
open(sys.argv[1], "w").write(json.dumps(value))
PY
openssl pkeyutl -sign -rawin -inkey "$TEST_DIR/private.pem" -in "$TEST_DIR/manifest.json" -out "$TEST_DIR/signature"
base64 -w0 "$TEST_DIR/signature" > "$TEST_DIR/signature.b64"

PATH="$TEST_DIR/bin:$PATH" \
CRANE_HOME="$TEST_DIR" \
CRANE_ENV_FILE="$TEST_DIR/.env" \
CRANE_COMPOSE_FILE="$TEST_DIR/docker-compose.prod.yml" \
CRANE_UPDATE_PUBLIC_KEY="$TEST_DIR/public.pem" \
CRANE_UPDATE_MANIFEST_FILE="$TEST_DIR/manifest.json" \
CRANE_UPDATE_SIGNATURE_FILE="$TEST_DIR/signature.b64" \
CRANE_BACKUP_COPY_DIR="$TEST_DIR/offsite" \
CRANE_ALLOW_LOCAL_BACKUP_ONLY=true \
"$REPO/crane-update" apply

grep -q '^CRANE_VERSION=1.3.0$' "$TEST_DIR/.env"
python3 - "$TEST_DIR/data/updates/operation-state.json" <<'PY'
import json, sys
state = json.load(open(sys.argv[1]))
assert state["status"] == "installed"
assert state["from_version"] == "1.2.0"
assert state["version"] == "1.3.0"
PY
test -s "$TEST_DIR/backups/"*/database.dump
test -s "$TEST_DIR/backups/"*/SHA256SUMS
test -s "$TEST_DIR/offsite/"*/database.dump
test ! -e "$TEST_DIR/data/updates/maintenance.json"

printf 'CRANE_VERSION=1.2.0\nPOSTGRES_USER=postgres\nPOSTGRES_DB=cra_compliance\n' > "$TEST_DIR/.env"
rm -f "$TEST_DIR/data/updates/operation-state.json"
if PATH="$TEST_DIR/bin:$PATH" \
  CRANE_HOME="$TEST_DIR" \
  CRANE_ENV_FILE="$TEST_DIR/.env" \
  CRANE_COMPOSE_FILE="$TEST_DIR/docker-compose.prod.yml" \
  CRANE_UPDATE_PUBLIC_KEY="$TEST_DIR/public.pem" \
  CRANE_UPDATE_MANIFEST_FILE="$TEST_DIR/manifest.json" \
  CRANE_UPDATE_SIGNATURE_FILE="$TEST_DIR/signature.b64" \
  CRANE_BACKUP_COPY_DIR="$TEST_DIR/offsite-failure" \
  CRANE_ALLOW_LOCAL_BACKUP_ONLY=true \
  FAKE_DOCKER_FAIL_RESTORE_VERIFY=true \
  "$REPO/crane-update" apply; then
  printf 'expected restore-verification failure\n' >&2
  exit 1
fi
grep -q '^CRANE_VERSION=1.2.0$' "$TEST_DIR/.env"
test ! -e "$TEST_DIR/data/updates/maintenance.json"
test "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$TEST_DIR/data/updates/operation-state.json")" = aborted

printf '{"status":"installing","phase":"maintenance","from_version":"1.2.0","backup":"none"}\n' > "$TEST_DIR/data/updates/operation-state.json"
printf '{}\n' > "$TEST_DIR/data/updates/maintenance.json"
PATH="$TEST_DIR/bin:$PATH" \
CRANE_HOME="$TEST_DIR" \
CRANE_ENV_FILE="$TEST_DIR/.env" \
CRANE_COMPOSE_FILE="$TEST_DIR/docker-compose.prod.yml" \
"$REPO/crane-update" recover
test ! -e "$TEST_DIR/data/updates/maintenance.json"
test "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$TEST_DIR/data/updates/operation-state.json")" = aborted
printf 'crane-update transaction test passed\n'
