"""Telegram digest delivery — posts daily digests to group topics."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, datetime, timezone
from typing import Any

import httpx
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from telegram_bot.formatter import CATEGORIES, format_digest, format_status

log = logging.getLogger(__name__)

API_BASE = os.getenv("KB_API_BASE", "http://localhost:8000")
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


_LABEL_TO_ID = {
    "bugbounty": "bugbounty",
    "ai-money": "ai-money",
    "saas-niches": "saas-niches",
    "crypto-defi": "crypto-defi",
    "crypto-defi-alpha": "crypto-defi",
    "crypto/defi-alpha": "crypto-defi",
    "attacking-ai": "attacking-ai",
    "tools-drops": "tools-drops",
    "general": "general",
    "status": "status",
}


def _topic_ids() -> dict[str, int]:
    """Load topic IDs from TELEGRAM_TOPIC_IDS env var (JSON map).

    Normalizes keys to lowercase category IDs from categories.yaml.
    Accepts keys like "BugBounty", "Crypto-DeFi-Alpha", "crypto-defi", etc.
    """
    raw = os.getenv("TELEGRAM_TOPIC_IDS", "{}")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("TELEGRAM_TOPIC_IDS is not valid JSON")
        return {}

    result: dict[str, int] = {}
    for key, val in parsed.items():
        normalized = _LABEL_TO_ID.get(key.lower(), key.lower())
        result[normalized] = val
    return result


def _fetch_items_for_category(category: str, run_date: date) -> list[dict[str, Any]]:
    since = datetime.combine(run_date, datetime.min.time()).replace(tzinfo=timezone.utc).isoformat()
    with httpx.Client(base_url=API_BASE, timeout=30) as client:
        resp = client.get("/items", params={"category": category, "since": since, "limit": 500})
        resp.raise_for_status()
        return resp.json()


def _fetch_health() -> dict[str, Any]:
    with httpx.Client(base_url=API_BASE, timeout=10) as client:
        resp = client.get("/health")
        resp.raise_for_status()
        return resp.json()


def _send_message_with_retry(
    bot: Bot,
    chat_id: int | str,
    text: str,
    thread_id: int | None,
) -> bool:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            kwargs: dict[str, Any] = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": ParseMode.MARKDOWN_V2,
                "disable_web_page_preview": True,
            }
            if thread_id:
                kwargs["message_thread_id"] = thread_id
            loop.run_until_complete(bot.send_message(**kwargs))
            return True
        except TelegramError as exc:
            log.warning("Telegram send failed (attempt %d/%d): %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    log.error("Telegram send failed after %d retries", MAX_RETRIES)
    return False


def send_digest(run_date: date | None = None) -> None:
    """Fetch today's items from API and post digest to each category topic."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

    run_date = run_date or date.today()
    topic_ids = _topic_ids()

    import asyncio
    bot = Bot(token=token)

    errors: list[str] = []
    per_source: dict[str, int] = {}

    for category in CATEGORIES:
        try:
            items = _fetch_items_for_category(category, run_date)
        except Exception as exc:
            msg = f"Failed fetching {category}: {exc}"
            log.error(msg)
            errors.append(msg)
            continue

        if not items:
            log.info("No items for %s today — skipping topic", category)
            continue

        # tally per-source counts
        for item in items:
            src = item.get("source_id", "unknown")
            per_source[src] = per_source.get(src, 0) + 1

        text = format_digest(category, items, run_date)
        thread_id = topic_ids.get(category)
        ok = _send_message_with_retry(bot, chat_id, text, thread_id)
        if not ok:
            errors.append(f"Delivery failed for {category}")

    # status topic
    try:
        health = _fetch_health()
    except Exception as exc:
        health = {}
        errors.append(f"Health fetch failed: {exc}")

    status_text = format_status(health, per_source, errors)
    status_thread = topic_ids.get("status")
    _send_message_with_retry(bot, chat_id, status_text, status_thread)
    log.info("Digest complete. Sources: %d, Errors: %d", len(per_source), len(errors))
