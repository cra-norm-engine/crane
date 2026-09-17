# CRANE release workflow

Use this checklist for every production release, including hotfixes and security releases. Copy it into a release issue or ticket; do not mark the canonical template as completed. The release owner must retain that completed record with links to the evidence.

## Release record

- [ ] Release version: `v____.____.____`
- [ ] Release type: feature / maintenance / security / emergency
- [ ] Security severity: none / low / medium / high / critical
- [ ] Release owner:
- [ ] Technical reviewer:
- [ ] Security reviewer:
- [ ] Planned publication time (UTC):
- [ ] Private commit (`amh1036/CRA-Compliance-Tool`):
- [ ] Public commit (`cra-norm-engine/crane`):
- [ ] Previous supported release:
- [ ] Previous and target Alembic revisions:
- [ ] Host updater/Compose change required: yes / no
- [ ] Approved RPO / RTO and measured restore time:
- [ ] GitHub release URL:
- [ ] Render deployment URL and deploy ID:
- [ ] Backup/restore evidence:
- [ ] Go/no-go decision and approvers:

## Non-negotiable release gates

Do not create or push a release tag until every applicable item below is complete.

- [ ] The public and private repositories contain the intended equivalent backend, frontend, migration, configuration, deployment, test, and documentation changes.
- [ ] No unrelated files, generated files, `.pyc`, `__pycache__`, credentials, local `.env` files, database dumps, customer data, or signing private keys are staged.
- [ ] Required reviews are approved and all required CI checks are green.
- [ ] Backend tests, frontend tests, frontend type checking, linting, production builds, security scans, and migration tests pass.
- [ ] A restorable database and artifact backup exists before a production migration.
- [ ] The installation has an encrypted, independently mounted `CRANE_BACKUP_COPY_DIR`; local-only backup mode is disabled.
- [ ] Release metadata, compatibility limits, release notes, upgrade instructions, and rollback instructions are accurate.
- [ ] `automatic_update_allowed` is false when the database revision, `crane-update`, `docker-compose.prod.yml`, `install.sh`, update key, or required host configuration changes.
- [ ] The update signing key is available only through the protected GitHub Actions secret.
- [ ] Staging installation and rollback have been exercised for any release containing migrations or deployment changes.
- [ ] A named person owns production monitoring and rollback during the release window.

## 1. Select and freeze the release

- [ ] Choose the next semantic version. Use:
  - patch for compatible fixes and security patches;
  - minor for compatible features;
  - major for intentionally breaking API, configuration, or data-model changes.
- [ ] Confirm the version is greater than every published version.
- [ ] Define the exact release scope and defer unrelated work.
- [ ] Resolve or explicitly accept every release-blocking defect.
- [ ] Identify affected and fixed versions for security changes.
- [ ] Confirm support status for the release's Python, Node.js, PostgreSQL, Docker, browser, and integration versions.
- [ ] Freeze database schema changes and public API changes before final migration testing.
- [ ] Assign a maintenance window, communication owner, rollback owner, and observation period.

## 2. Prepare both repositories safely

The repositories have unrelated histories. Never merge them with `--allow-unrelated-histories`, never force-push one history over the other, and never assume equal commit hashes.

Private development repository:

```text
/home/ali/Desktop/CRA Project/CRA-Compliance-Tool
git@github.com-amh1036:amh1036/CRA-Compliance-Tool.git
```

Public production repository:

```text
/home/ali/Desktop/crane-oss
git@github.com-cra-norm-engine:cra-norm-engine/crane.git
```

- [ ] Fetch both remotes and confirm neither local `main` has diverged from its remote:

  ```bash
  git -C "/home/ali/Desktop/CRA Project/CRA-Compliance-Tool" fetch origin --prune
  git -C /home/ali/Desktop/crane-oss fetch origin --prune
  git -C "/home/ali/Desktop/CRA Project/CRA-Compliance-Tool" rev-list --left-right --count main...origin/main
  git -C /home/ali/Desktop/crane-oss rev-list --left-right --count main...origin/main
  ```

- [ ] Review private changes and exclude compiled bytecode:

  ```bash
  git -C "/home/ali/Desktop/CRA Project/CRA-Compliance-Tool" status --short
  git -C "/home/ali/Desktop/CRA Project/CRA-Compliance-Tool" diff --check
  ```

- [ ] Commit and push the private repository first.
- [ ] Copy only intended backend/frontend and required supporting files into the public repository.
- [ ] Compare every synchronized source file with `cmp` or checksums.
- [ ] Preserve public-only website, report, and local utility changes unless they are explicitly part of the release.
- [ ] Commit the public repository separately; never merge the complete unrelated histories. If cherry-picking, use only focused commits on a branch based on the target repository's own `main`.
- [ ] Push public `main` and confirm local and remote commit IDs match.
- [ ] Record both unrelated commit IDs in the release record.

## 3. Review code, configuration, and compatibility

- [ ] Review the complete diff since the previous release, not only the final commit.
- [ ] Obtain at least one independent approval for normal releases and two-person approval for security-sensitive authentication, authorization, cryptography, migrations, backup, and updater changes.
- [ ] Confirm new API inputs validate untrusted data and authorization is enforced server-side.
- [ ] Confirm audit events exist for security-sensitive and administrative state changes.
- [ ] Confirm logs do not contain access tokens, passwords, database URLs, signing material, personal data, SBOM contents, or customer evidence.
- [ ] Document every new, renamed, or removed environment variable and safe default.
- [ ] Check frontend/backend API compatibility and deploy them as one version.
- [ ] Exercise Dependency-Track, Jira, LDAP/SSO, SBOM ingestion, vulnerability scanning-disabled mode, and other changed integrations.
- [ ] Verify upgrade paths from every supported source version, not only a clean install.
- [ ] Verify configuration remains compatible or provide an explicit migration procedure.
- [ ] Compare host-managed files (`crane-update`, `docker-compose.prod.yml`, `install.sh`, `deploy/`, `updates/`) with the previous release. If any required file changed, document and test the manual host-tooling upgrade before running `apply`.

## 4. Run the release test suite

Use clean dependencies and do not treat a successful Vite bundle as a substitute for TypeScript validation.

Backend:

```bash
cd backend
ruff check .
pytest app/tests -v --cov=app --cov-report=term-missing
alembic heads
```

- [ ] Ruff passes with no ignored new violations.
- [ ] All backend unit and integration tests pass.
- [ ] Coverage regressions are reviewed.
- [ ] `alembic heads` reports exactly one head.

Frontend:

```bash
cd frontend
npm ci --legacy-peer-deps
npm run type-check
npx eslint . --ext .vue,.js,.jsx,.ts,.tsx
npm run test:run
npx vite build
```

- [ ] Type checking passes. The release image currently invokes Vite directly, so this must be checked independently.
- [ ] ESLint passes without using `--fix` as the verification step.
- [ ] All frontend tests pass.
- [ ] The production bundle succeeds and important bundle-size warnings are reviewed.
- [ ] Keyboard navigation, focus, labels, contrast, mobile layout, loading, empty, permission-denied, and failure states are manually smoke-tested for changed UI.

Deployment and updater:

```bash
bash -n crane-update install.sh scripts/test_crane_update.sh
./scripts/test_crane_update.sh
docker compose --env-file .env -f docker-compose.prod.yml config -q
docker build --build-arg VITE_APP_VERSION=vX.Y.Z -t crane-frontend-release-test:local frontend
```

- [ ] Shell syntax, updater transaction test, and production Compose parsing pass.
- [ ] Backend and frontend production images build from a clean checkout.
- [ ] Health checks fail closed when the application or database is unavailable.

## 5. Validate migrations, backup, and rollback

- [ ] Review every new Alembic migration for locks, table rewrites, data loss, runtime, and backward compatibility.
- [ ] Prefer expand-and-contract migrations; do not combine destructive schema removal with code that may need rollback.
- [ ] Test upgrade from a copy of the previous production database to `head`.
- [ ] Record the previous release manifest's `database_revision` and the candidate Alembic head; treat any difference as a supervised database migration.
- [ ] Confirm the upgraded application can read old data and new writes remain valid.
- [ ] Create a PostgreSQL custom-format backup and validate it with `pg_restore --list`.
- [ ] Include retained artifact storage in the backup.
- [ ] Restore the backup into an isolated database and run health and data-integrity checks.
- [ ] Confirm maintenance mode rejects application traffic, permits health probes, drains in-flight requests, and remains enabled after an interrupted update.
- [ ] Confirm the updater verifies checksums, restores the dump, validates constraints and Alembic revision, and verifies the complete audit-log HMAC chain before reopening traffic.
- [ ] Confirm the independent backup destination is a different mounted filesystem, has enough free space, preserves restrictive permissions for the backed-up `.env`, and is covered by encryption, retention, and access-control policy.
- [ ] Run `./crane-update apply` on a staging Docker Compose installation.
- [ ] Run `./crane-update rollback` and confirm the previous images, environment, database, and artifacts are restored.
- [ ] Interrupt staging once before backup and once after migration; verify `recover` only resumes the unchanged release and requires `rollback` after possible data changes.
- [ ] Document expected downtime, migration duration, required free space, backup retention, and the point after which rollback loses new writes.
- [ ] Set `rollback_mode` accurately. Use `database-restore` whenever the previous application cannot safely use the migrated schema.

## 6. Perform security and supply-chain checks

- [ ] Review GitHub Dependabot/dependency alerts and Code Scanning findings.
- [ ] Run filesystem and container-image vulnerability scans; resolve or document risk acceptance for every critical/high finding.
- [ ] Run `npm audit --omit=dev` and review production dependency findings.
- [ ] Review Python dependencies for known vulnerabilities using the project's approved scanner.
- [ ] Confirm dependency lockfiles are committed and builds are reproducible.
- [ ] Confirm the release workflow generates SBOM and provenance attestations for both images.
- [ ] Confirm Cosign keyless signing completes for both immutable image digests.
- [ ] Review licenses and attribution for new dependencies.
- [ ] Confirm GitHub secret scanning and push protection are enabled where available.
- [ ] Search the staged diff for secrets and confidential data before push.
- [ ] Rotate any credential that appeared in terminal output, logs, commits, issues, screenshots, or build artifacts.

For a security release:

- [ ] Create a private GitHub Security Advisory before public disclosure.
- [ ] Request a CVE when applicable.
- [ ] Record affected versions, fixed version, severity rationale, exploitation status, mitigations, and credits.
- [ ] Coordinate publication time and avoid leaking embargoed details in commits or public metadata.
- [ ] Set `update_type` to `security`, choose the correct severity, and populate `advisory_url`.
- [ ] Decide whether automatic installation is safe; criticality alone does not justify unsafe automatic migration.
- [ ] Prepare customer/user notification text and support responses before publication.

## 7. Prepare release metadata and documentation

Update `updates/release-metadata.json` deliberately:

- [ ] `update_type` is `security`, `maintenance`, or `feature`.
- [ ] `severity` is correct; security updates must not use `none`.
- [ ] `minimum_upgrade_version` is the oldest directly supported version and has been tested.
- [ ] `postgres_major_versions` lists only tested versions.
- [ ] `automatic_update_allowed` is true only when unattended backup, migration, health verification, and rollback are safe.
- [ ] Treat every database-revision change as supervised/manual; the updater must refuse it in automatic mode.
- [ ] Set `automatic_update_allowed` to false when administrators must first update host files or add/change required environment variables.
- [ ] `rollback_mode` matches actual recovery requirements.
- [ ] Use `database-restore` until an end-to-end test proves that both the previous and target images can safely use the same schema; the current updater restores the matching database backup during rollback.
- [ ] `advisory_url` is set for a published security advisory or is `null`.
- [ ] Frontend and backend report the intended release version.

Documentation:

- [ ] Update user, administrator, API, installation, upgrade, rollback, integration, and environment-variable documentation affected by the release.
- [ ] Add explicit operator actions for breaking changes or configuration changes.
- [ ] Add screenshots only when they match the final UI and contain no confidential data.
- [ ] Confirm public documentation links resolve.
- [ ] Prepare release notes with these sections:

  ```markdown
  ## Summary
  ## Security fixes
  ## Added
  ## Changed
  ## Fixed
  ## Breaking changes and required actions
  ## Database migrations
  ## Compatibility
  ## Update instructions
  ## Rollback instructions
  ## Known issues
  ## Contributors and acknowledgements
  ```

- [ ] Write notes for operators and users; do not rely only on autogenerated commit titles.

## 8. Verify signing keys and GitHub configuration

- [ ] `UPDATE_SIGNING_PRIVATE_KEY_B64` exists as an Actions secret in `cra-norm-engine/crane`.
- [ ] The private signing key is stored in an approved secrets manager with restricted access and recovery ownership; it is never committed.
- [ ] The two distributed public-key files are identical:

  ```bash
  cmp updates/update-public.pem backend/app/core/update-public.pem
  ```

- [ ] Confirm the private key matches the distributed public key in a safe environment.
- [ ] Confirm the release workflow has only required permissions: `contents: write`, `packages: write`, and `id-token: write`.
- [ ] Confirm branch protection requires reviews and all applicable CI checks on public `main`.
- [ ] Confirm GHCR backend/frontend packages have the intended visibility and retention rules.
- [ ] Confirm the weekly `refresh-update-manifest.yml` workflow is enabled and its last run succeeded.
- [ ] Test key rotation as a planned, dual-key transition before the current key expires or is revoked. A suspected private-key compromise is an immediate release stop.

## 9. Stage and approve the release

- [ ] Deploy the exact public release candidate to a staging environment.
- [ ] Use production-like PostgreSQL, persistent artifacts, HTTPS, CORS, authentication, and integrations.
- [ ] Run representative workflows: login, permissions, product/release management, SBOM upload, external finding ingestion, vulnerability handling, evidence upload/download, reports, and audit log.
- [ ] Confirm **Settings → System updates → Check now** handles current, available, expired, invalid-signature, unreachable, and postponed states clearly.
- [ ] Test one manual update and one eligible automatic update on Docker Compose staging.
- [ ] Confirm Render-specific deployment and recovery steps separately; Render cannot run the host Docker/systemd updater.
- [ ] Record test evidence and obtain formal go/no-go approval.

## 10. Publish the public GitHub release

Release tags are published from `/home/ali/Desktop/crane-oss` only. Do not tag the private repository unless its release workflow is deliberately disabled or changed, because its workflow targets the same public GHCR image names.

Pushing the tag triggers immediate image publication and GitHub Release creation; it is the production release action, not a harmless preparation step. Have the approved release-note text ready before pushing the tag. The workflow currently generates notes automatically, so review and replace them with the approved notes before notifying users.

- [ ] Confirm public `main` is clean, current, reviewed, and green:

  ```bash
  cd /home/ali/Desktop/crane-oss
  git fetch origin --prune
  git status --short
  git rev-list --left-right --count main...origin/main
  git log -1 --oneline --decorate
  ```

- [ ] Confirm the tag does not exist locally or remotely:

  ```bash
  git tag --list vX.Y.Z
  git ls-remote --tags origin refs/tags/vX.Y.Z
  ```

- [ ] Prefer a cryptographically signed tag when maintainer signing is configured:

  ```bash
  git tag -s vX.Y.Z -m "CRANE vX.Y.Z"
  git push origin vX.Y.Z
  ```

- [ ] If maintainer signing is not configured, use an annotated tag instead:

  ```bash
  git tag -a vX.Y.Z -m "CRANE vX.Y.Z"
  git push origin vX.Y.Z
  ```

- [ ] Never move, overwrite, or force-push a published tag. Correct a failed or incorrect release with the next patch version.
- [ ] Monitor `.github/workflows/release.yml` until both image jobs and the release job succeed.
- [ ] If any job fails, diagnose it, commit the fix to both repositories, and publish a new patch tag.

The workflow must:

- [ ] Verify the bundled and updater public keys match.
- [ ] Build and push backend and frontend images.
- [ ] Generate SBOM and provenance attestations.
- [ ] Sign both immutable image digests with Cosign.
- [ ] Generate and sign `update-manifest.json`.
- [ ] Publish `update-manifest.json` and `update-manifest.json.sig` as GitHub release assets.

## 11. Verify published artifacts independently

- [ ] The GitHub release is public, non-draft, non-prerelease unless intentionally marked otherwise, and has reviewed release notes.
- [ ] Both manifest assets download through the stable `releases/latest/download` URLs.
- [ ] Verify the manifest signature:

  ```bash
  curl -fsSL https://github.com/cra-norm-engine/crane/releases/download/vX.Y.Z/update-manifest.json -o /tmp/crane-manifest.json
  curl -fsSL https://github.com/cra-norm-engine/crane/releases/download/vX.Y.Z/update-manifest.json.sig -o /tmp/crane-manifest.json.sig.b64
  base64 --decode /tmp/crane-manifest.json.sig.b64 > /tmp/crane-manifest.sig
  openssl pkeyutl -verify -pubin -inkey updates/update-public.pem -rawin -in /tmp/crane-manifest.json -sigfile /tmp/crane-manifest.sig
  ```

- [ ] Inspect the manifest and confirm version, channel, update type, severity, timestamps, expiry, minimum source version, Alembic revision, PostgreSQL versions, automatic-update flag, rollback mode, release/advisory links, image names, and digests.
- [ ] Confirm manifest image digests equal the GHCR image digests produced by the workflow.
- [ ] Verify both Cosign signatures and GitHub Actions identity against immutable digests.
- [ ] Verify SBOM and provenance attestations are present for both images.
- [ ] Pull both images by digest on a clean machine and run health checks.
- [ ] Run `./crane-update check` from a supported previous Docker Compose installation and confirm it reports the new version.

## 12. Deploy and verify Render

Render deploys from `amh1036/CRA-Compliance-Tool/main`; GitHub Releases in `cra-norm-engine/crane` remain the trusted public update catalogue.

Before deployment:

- [ ] Confirm the private commit recorded above contains the same intended application changes as the public release.
- [ ] Create and verify a Render PostgreSQL backup; export retained artifacts separately if they are not in managed persistent storage.
- [ ] Record the exact Render recovery point, backup identifier, previous backend/frontend deploy IDs, measured restore time, and named rollback operator.
- [ ] Confirm the Render PostgreSQL major version is listed in the release manifest.
- [ ] Review all Render environment variables without copying secret values into tickets or logs.
- [ ] Set `BACKEND_ENVIRONMENT=production`, `BACKEND_DEBUG=false`, and `BACKEND_APP_VERSION=X.Y.Z`.
- [ ] Keep `BACKEND_UPDATE_MANIFEST_URL=https://github.com/cra-norm-engine/crane/releases/latest/download/update-manifest.json`.
- [ ] Remove an obsolete `BACKEND_UPDATE_PUBLIC_KEY_PATH=/etc/crane/update-public.pem` override, or explicitly use `/workspace/backend/app/core/update-public.pem`.
- [ ] Set `BACKEND_AUTO_MIGRATE=false` when migrations are executed as a controlled pre-deploy/one-off operation.
- [ ] Confirm CORS contains only the real frontend origin(s).

Deployment:

- [ ] Block new application writes at the Render ingress/application layer and allow in-flight requests and background jobs to drain before the final backup or migration.
- [ ] Keep the application unavailable throughout any incompatible migration; do not rely on a rolling deployment across incompatible schemas.
- [ ] Run the migration against the Render database from the exact release commit in a controlled job.
- [ ] Deploy the backend from the recorded private commit.
- [ ] Deploy the frontend with `VITE_APP_VERSION=X.Y.Z` and the correct `VITE_API_BASE_URL`.
- [ ] Confirm both deployments succeed and no unexpected migration, authentication, CORS, or scheduler errors appear in Render logs.

Smoke test:

- [ ] `/api/v1/health` returns `status: ok`, `database: true`, and the expected version.
- [ ] Administrator login, core create/read/update workflows, evidence access, background jobs, and changed integrations work.
- [ ] **Settings → System updates → Check now** succeeds and reports the installed release as current.
- [ ] Browser console and Render logs have no new errors or secret leakage.
- [ ] Alerting and service notifications are active.

Render rollback:

- [ ] Record the previous Render deploy ID before rollout.
- [ ] If no incompatible migration ran, roll back both services to the previous deploy.
- [ ] If an incompatible migration ran, stop writes, restore the matching pre-release database/artifact backup, then roll back both services.
- [ ] Do not use CRANE's Docker Compose automatic updater on Render; Render owns deployment and application rollback.

## 13. Roll out self-hosted installations

- [ ] Notify administrators that the release is available, including severity, required action, expected downtime, compatibility, and rollback guidance.
- [ ] Roll out to a canary installation first.
- [ ] Confirm the in-app notification appears and links to the correct notes/advisory.
- [ ] If the release changes host-managed files, set automation off and have the administrator update the public checkout with `git pull --ff-only`, verify the expected public commit, review configuration changes, and run Compose validation before `./crane-update apply`.
- [ ] For manual rollout, run `./crane-update check` and `./crane-update apply` from the installation directory.
- [ ] Confirm `CRANE_BACKUP_COPY_DIR` is mounted, writable, encrypted, monitored, and independent of the application host before running `apply`.
- [ ] Enable automatic rollout only when the manifest explicitly allows it and the administrator selected an automatic policy.
- [ ] Monitor backup creation, migration, image pull, startup, and health verification.
- [ ] Confirm the updater retained a usable backup and recorded a successful operation state.
- [ ] Pause broader rollout immediately if canary health, data integrity, or integrations regress.

## 14. Post-release monitoring and closure

- [ ] Monitor GitHub Actions, GHCR pulls, update-check failures, application errors, Render metrics/logs, database health, latency, scheduled jobs, and support channels throughout the observation period.
- [ ] Confirm a sample of self-hosted installations can retrieve and verify the signed manifest.
- [ ] Confirm the weekly manifest-refresh workflow will run before the 30-day manifest expiry.
- [ ] Triage every release regression and decide rollback, hotfix, or documented workaround.
- [ ] Publish corrections transparently; do not silently replace release binaries, manifests, tags, or notes that change security meaning.
- [ ] Complete the GitHub Security Advisory/CVE publication and user notification for security releases.
- [ ] Record actual migration duration, downtime, incidents, rollback actions, and lessons learned.
- [ ] Close the release record only after the observation period and evidence review are complete.

## Emergency hotfix path

Emergency does not mean unverified.

- [ ] Limit scope to the smallest safe fix.
- [ ] Require technical and security approval.
- [ ] Run all tests directly related to the fault plus authentication, migration, updater, and smoke tests.
- [ ] Create and verify backups before deployment.
- [ ] Use a new patch version; never rewrite the affected tag or assets.
- [ ] Publish clear provisional notes and update them after the incident review.
- [ ] Complete deferred non-critical checks immediately after containment and record the exception and approver.

## Final sign-off

- [ ] Product/release owner: scope and notes approved.
- [ ] Engineering reviewer: code, tests, compatibility, and operations approved.
- [ ] Security reviewer: vulnerabilities, signing, advisories, and secrets approved.
- [ ] Database owner: migration, backup, restore, and rollback approved.
- [ ] Render operator: deploy and rollback evidence approved.
- [ ] Release owner: GitHub assets, signatures, images, update discovery, monitoring, and communications verified.

**Final decision:** GO / NO-GO

**Decision time (UTC):**

**Approvers:**
**Evidence/ticket URL:**
