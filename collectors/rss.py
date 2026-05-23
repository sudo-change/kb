"""Generic RSS/Atom feed collector."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

try:
    import feedparser
except ImportError:
    feedparser = None

from collectors.base import BaseCollector
from core.models import Item


class RSSCollector(BaseCollector):
    name = "rss"

    def __init__(self, feeds: list[dict], per_feed_since: dict[str, datetime] | None = None):
        """feeds: list of {id, url, category, name}"""
        self._feeds = feeds
        self._per_feed_since: dict[str, datetime] = per_feed_since or {}
        self.per_feed_last: dict[str, datetime] = {}
        self.errors: list[str] = []

    def validate_config(self) -> bool:
        if feedparser is None:
            print("  [rss] feedparser not installed")
            return False
        if not self._feeds:
            print("  [rss] No feeds configured")
            return False
        return True

    def collect(self, since: datetime | None = None) -> list[Item]:
        items = []
        self.per_feed_last = {}
        self.errors = []

        for feed_cfg in self._feeds:
            url = feed_cfg.get("url", "")
            if not url:
                continue
            category = feed_cfg.get("category", "")
            feed_name = feed_cfg.get("name", feed_cfg.get("id", ""))
            source_id = feed_cfg.get("id", hashlib.md5(url.encode()).hexdigest()[:8])
            feed_since = self._per_feed_since.get(url, since)

            try:
                feed_items, max_pub = self._collect_feed(url, category, feed_name, source_id, feed_since)
                items.extend(feed_items)
                print(f"  [rss] {feed_name or url}: {len(feed_items)} items")
                if max_pub:
                    self.per_feed_last[url] = max_pub
                elif feed_since:
                    self.per_feed_last[url] = feed_since
            except Exception as e:
                msg = f"rss:{feed_name or url}: {e}"
                print(f"  [rss] Error fetching {url}: {e}")
                self.errors.append(msg)
                if url in self._per_feed_since:
                    self.per_feed_last[url] = self._per_feed_since[url]

        return items

    def _collect_feed(
        self, url: str, category: str, feed_name: str, source_id: str, since: datetime | None
    ) -> tuple[list[Item], datetime | None]:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            raise RuntimeError(str(feed.bozo_exception))

        result = []
        max_pub: datetime | None = None

        for entry in feed.entries:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            if since and published and published <= since:
                continue

            tags = []
            if hasattr(entry, "tags"):
                tags = [t.term.lower() for t in entry.tags if hasattr(t, "term") and t.term]

            body = ""
            if hasattr(entry, "content") and entry.content:
                body = entry.content[0].get("value", "")
            elif hasattr(entry, "summary"):
                body = entry.summary or ""

            summary = ""
            if hasattr(entry, "summary") and entry.get("summary") != body:
                summary = (entry.get("summary") or "")[:500]

            entry_id = entry.get("id", entry.get("link", entry.get("title", "")))
            item_source_id = f"{source_id}:{hashlib.md5(entry_id.encode()).hexdigest()[:8]}"

            item = Item(
                url=entry.get("link", ""),
                title=entry.get("title", "Untitled"),
                source_id=item_source_id,
                source_type="rss",
                body=body,
                summary=summary,
                category=category or None,
                tags=tags,
                metadata={"feed_url": url, "feed_name": feed_name, "author": entry.get("author", "")},
                published_at=published,
            )
            result.append(item)

            if published and (max_pub is None or published > max_pub):
                max_pub = published

        return result, max_pub
