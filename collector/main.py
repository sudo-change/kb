"""Collector entry point. Run once or daemonized with APScheduler."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure repo root is on path when run as: python collector/main.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import load_sources
from core.database import DB
from core.models import Item
from core.scheduler import CollectionScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger("kf.collector")

DB_PATH = os.environ.get("KF_DB_PATH", "data/kf.db")
RSSHUB_URL = os.environ.get("RSSHUB_URL", "http://localhost:1200")
COOKIES_PATH = os.environ.get("KF_COOKIES", "cookies/cookies.txt")


def _build_rss_items(sources_cfg: dict) -> list[dict]:
    """Merge rsshub feeds and rss feeds into a flat list for RSSCollector."""
    feeds = []

    # RSSHub feeds → prepend instance URL
    rsshub = sources_cfg.get("rsshub", {})
    instance = rsshub.get("instance", RSSHUB_URL).rstrip("/")
    for feed in rsshub.get("feeds", []):
        route = feed.get("route", "")
        feeds.append({
            "id": f"rsshub:{route.lstrip('/').replace('/', '-')}",
            "url": f"{instance}{route}",
            "category": feed.get("category"),
            "name": feed.get("name", route),
        })

    # Direct RSS feeds
    for feed in sources_cfg.get("rss", {}).get("feeds", []):
        feeds.append({
            "id": f"rss:{feed.get('name', feed['url'])[:20]}",
            "url": feed["url"],
            "category": feed.get("category"),
            "name": feed.get("name", feed["url"]),
        })

    return feeds


def run_once(db: DB) -> int:
    """Run all collectors once. Returns total items added."""
    sources_cfg = load_sources()
    errors: list[str] = []
    total_added = 0
    started = datetime.now(timezone.utc)

    # RSS + RSSHub
    feeds = _build_rss_items(sources_cfg)
    if feeds:
        try:
            from collectors.rss import RSSCollector
            collector = RSSCollector(feeds=feeds)
            if collector.validate_config():
                items = collector.collect()
                added = db.store_items(items)
                total_added += added
                log.info("[rss] stored %d/%d items", added, len(items))
                if collector.errors:
                    errors.extend(collector.errors)
        except Exception as e:
            msg = f"rss: {e}"
            log.error(msg)
            errors.append(msg)

    # YouTube channels
    yt_cfg = sources_cfg.get("youtube", {})
    yt_channels = yt_cfg.get("channels", [])
    if yt_channels:
        for ch_cfg in yt_channels:
            handle = ch_cfg.get("handle", "")
            category = ch_cfg.get("category")
            try:
                from collectors.youtube import YouTubeCollector
                collector = YouTubeCollector(
                    channels=[f"@{handle}"],
                    source_id=f"yt-{handle.lower()}",
                    category=category,
                )
                items = collector.collect()
                added = db.store_items(items)
                total_added += added
                log.info("[youtube] %s: stored %d/%d items", handle, added, len(items))
            except Exception as e:
                msg = f"youtube:{handle}: {e}"
                log.error(msg)
                errors.append(msg)

    db.log_run({"started_at": started, "items_added": total_added, "errors": errors})
    log.info("Collection run done — added %d items, %d errors", total_added, len(errors))
    return total_added


def main():
    parser = argparse.ArgumentParser(description="KnowledgeForge collector")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    db = DB(DB_PATH)

    if args.once:
        added = run_once(db)
        print(f"Added: {added} items")
        return

    # Daemon mode — APScheduler
    scheduler = CollectionScheduler(db=db, collect_fn=lambda: run_once(db))
    scheduler.start()
    log.info("Collector running. Ctrl+C to stop.")

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()
        log.info("Collector stopped.")


if __name__ == "__main__":
    main()
