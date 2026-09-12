---
id: system-updates
title: Updating CRANE safely
sidebar_position: 3
---

# Updating CRANE safely

Production installations receive signed release metadata from GitHub Releases and immutable backend and frontend images from GHCR. CRANE never gives its web container access to the Docker socket.

## Check and install manually

Before the first production update, mount backup storage that is independent of the
CRANE host and set its host path in `.env`:

```dotenv
CRANE_BACKUP_COPY_DIR=/mnt/crane-backups
CRANE_ALLOW_LOCAL_BACKUP_ONLY=false
```

The updater rejects a production update if it cannot create this independent copy.
`CRANE_ALLOW_LOCAL_BACKUP_ONLY=true` is intended only for disposable development and
test installations.

Run these commands from the installation directory:

```bash
./crane-update check
./crane-update apply
```

The updater downloads immutable images before downtime, enables maintenance mode,
drains requests, and gracefully stops the application. With writes stopped, it backs
up PostgreSQL, artifacts, and the environment, records checksums, restores the dump
into an isolated temporary PostgreSQL instance, and verifies the independent backup
copy. Only then does it run the migration.

Before reopening CRANE, the updater verifies the expected application version,
Alembic revision, database constraints, database health, and complete audit-log HMAC
chain. A failed migration or verification restores the matching environment,
database, artifacts, and images. Database rollback replaces the migrated database
rather than overlaying it; pre-rollback artifacts are retained separately for
forensic recovery. A crash fails closed: maintenance mode remains in
place for operator review instead of exposing an uncertain state.

Plan a maintenance window. CRANE is unavailable while its cold backup, migration,
verification, and possible rollback run. Keep a separately tested infrastructure
backup and PostgreSQL point-in-time recovery; the application updater does not
replace either one.

If the host or updater stops before a backup or migration starts, inspect
`./crane-update status`, correct the underlying problem, and run
`./crane-update recover`. Recovery is deliberately accepted only when the journal
proves that the database and configured version were not changed. Once migration
may have started, use the confirmed `rollback` command instead.

## Automatic updates

In **Settings → System updates**, select **Automatic security updates** or **Automatic compatible updates** and choose a UTC maintenance window. Then install the supplied systemd unit and timer:

```bash
sudo cp deploy/crane-update.service deploy/crane-update.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now crane-update.timer
```

The timer checks hourly but installs only during the configured window. Releases
marked as requiring manual installation are never installed automatically. Any
release whose database revision differs from the installed revision always requires
a supervised manual update, even if its manifest otherwise permits automation.

## Roll back

```bash
./crane-update rollback
```

Rollback restores the pre-update database, artifacts, environment file, and container images. Data written after that backup is lost, so the command requires explicit confirmation. Failed updates roll back automatically before CRANE returns to service.

## Release compatibility rules

- Frontend and backend always share one CRANE version.
- Production images are selected by immutable SHA-256 digest.
- Direct upgrades below `minimum_upgrade_version` are rejected.
- Only PostgreSQL major versions named in the signed manifest are accepted.
- Database migrations do not run during ordinary backend restarts.
- Destructive schema changes require `database-restore` rollback and must follow expand-and-contract migration practices.

The local restore-tested copy is retained under `backups/`; the independently mounted
copy is written under `CRANE_BACKUP_COPY_DIR`. Encrypt that storage, restrict access,
monitor backup failures, and test a full host-loss restore on a schedule.
