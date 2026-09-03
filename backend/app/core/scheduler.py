# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""
In-process background scheduler for recurring CRANE maintenance jobs.

A single APScheduler ``BackgroundScheduler`` runs inside the FastAPI process
(no extra container). Task reminders and Jira event retries always run; the
networked SBOM vulnerability sweep remains opt-in.

Concurrency: the sweep job takes a Postgres *transaction-less* advisory lock so
that if more than one worker/process starts a scheduler, only one actually runs
the sweep at a time (the others no-op that tick).
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.scan_orchestration_service import run_scheduled_sweep

logger = logging.getLogger(__name__)

# Dedicated advisory-lock key for the scheduled sweep (distinct from the audit
# chain lock in models/audit_log_event.py).
_SWEEP_LOCK_KEY = 73194216
_JIRA_LOCK_KEY = 73194217

_scheduler: BackgroundScheduler | None = None


def _sweep_job() -> None:
    """Cron entry point — run the sweep only if we win the advisory lock."""
    from sqlalchemy import text

    with SessionLocal() as db:
        got_lock = db.execute(
            text("SELECT pg_try_advisory_lock(:k)"), {"k": _SWEEP_LOCK_KEY}
        ).scalar()
        if not got_lock:
            logger.info("Scheduled sweep skipped — another worker holds the lock")
            return
        try:
            run_scheduled_sweep()
        finally:
            db.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _SWEEP_LOCK_KEY})


def _task_notification_job() -> None:
    """Generate deduplicated due-soon and overdue task notifications."""
    from app.services.manual_task_service import ManualTaskService

    with SessionLocal() as db:
        ManualTaskService(db).generate_due_notifications()


def _jira_sync_job() -> None:
    """Retry durable inbound Jira events, with one consumer across workers."""
    from sqlalchemy import text

    from app.services.jira_integration_service import JiraIntegrationService

    with SessionLocal() as db:
        got_lock = db.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": _JIRA_LOCK_KEY}).scalar()
        if not got_lock:
            return
        try:
            JiraIntegrationService(db).process_pending_events()
        finally:
            db.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _JIRA_LOCK_KEY})


def start_scheduler() -> None:
    """Start background maintenance jobs. Idempotent."""
    global _scheduler
    if _scheduler is not None:
        return

    scheduler = BackgroundScheduler(daemon=True)
    if settings.scan_scheduler_enabled:
        try:
            trigger = CronTrigger.from_crontab(settings.scan_schedule_cron)
            scheduler.add_job(
                _sweep_job, trigger=trigger, id="sbom_vulnerability_sweep",
                max_instances=1, coalesce=True, replace_existing=True,
            )
        except ValueError:
            logger.error("Invalid scan_schedule_cron %r — scan job disabled", settings.scan_schedule_cron)
    scheduler.add_job(
        _task_notification_job,
        trigger=CronTrigger(hour=8, minute=0),
        id="manual_task_due_notifications",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.add_job(
        _jira_sync_job,
        trigger=IntervalTrigger(minutes=1),
        id="jira_sync_events",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Background scheduler started (scan cron=%s, Jira sync every minute)",
        settings.scan_schedule_cron if settings.scan_scheduler_enabled else "disabled",
    )


def shutdown_scheduler() -> None:
    """Stop the background scheduler if running."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Background scheduler stopped")
