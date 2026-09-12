---
id: system-updates
title: Updating CRANE safely
sidebar_position: 3
---

# Updating CRANE safely

Production installations receive signed release metadata from GitHub Releases and immutable backend and frontend images from GHCR. CRANE never gives its web container access to the Docker socket.

## Check and install manually

Run these commands from the installation directory:

```bash
./crane-update check
./crane-update apply
```

The updater verifies the release signature and image digests, checks the installed CRANE and PostgreSQL versions, creates a PostgreSQL and artifact backup, runs the Alembic migration as a one-shot job, starts the matching frontend and backend images, and waits for the health check. A failed installation automatically restores the previous database and images.

## Automatic updates

In **Settings → System updates**, select **Automatic security updates** or **Automatic compatible updates** and choose a UTC maintenance window. Then install the supplied systemd unit and timer:

```bash
sudo cp deploy/crane-update.service deploy/crane-update.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now crane-update.timer
```

The timer checks hourly but installs only during the configured window. Releases marked as requiring manual installation are never installed automatically.

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

Backups are stored under `backups/`. Test restoration regularly and move retained backups to storage protected independently from the CRANE host.
