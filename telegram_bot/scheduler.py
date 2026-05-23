"""Telegram digest scheduler — fires daily at 8 AM local time."""

from __future__ import annotations

import logging
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from telegram_bot.bot import send_digest

log = logging.getLogger(__name__)


def _shutdown(signum, frame):
    log.info("Telegram bot shutting down")
    sys.exit(0)


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        send_digest,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_digest",
        name="Telegram daily digest",
        misfire_grace_time=3600,
    )
    log.info("Telegram digest scheduler started — fires at 08:00 local")
    scheduler.start()


if __name__ == "__main__":
    run()
