"""APScheduler wrapper for KnowledgeForge collectors."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    _HAS_APSCHEDULER = True
except ImportError:
    _HAS_APSCHEDULER = False

log = logging.getLogger("kf.scheduler")

INTERVAL_MINUTES = 15


class CollectionScheduler:
    def __init__(self, db, collect_fn):
        if not _HAS_APSCHEDULER:
            raise RuntimeError("APScheduler not installed. Run: pip install apscheduler")
        self._db = db
        self._collect_fn = collect_fn
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._running = False

    def start(self):
        self._scheduler.add_job(
            self._collect_job,
            trigger=IntervalTrigger(minutes=INTERVAL_MINUTES),
            id="collect_all",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=120,
        )
        self._scheduler.start()
        log.info("Scheduler started — every %d min", INTERVAL_MINUTES)

    def stop(self):
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            log.info("Scheduler stopped.")

    async def _collect_job(self):
        if self._running:
            log.debug("Collection already running, skipping.")
            return
        self._running = True
        try:
            log.info("[scheduler] Starting collection run")
            added = await asyncio.get_event_loop().run_in_executor(None, self._collect_fn)
            log.info("[scheduler] Collection run finished: +%d items", added)
        except Exception as e:
            log.error("[scheduler] Collection run error: %s", e)
        finally:
            self._running = False

    def trigger_now(self):
        job = self._scheduler.get_job("collect_all")
        if job:
            job.modify(next_run_time=datetime.now(timezone.utc))

    def get_status(self) -> dict:
        job = self._scheduler.get_job("collect_all")
        return {
            "running": self._running,
            "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
        }
