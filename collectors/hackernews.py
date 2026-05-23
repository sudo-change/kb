"""HackerNews collector using Algolia HN Search API."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from collectors.base import BaseCollector
from core.models import Item

ALGOLIA_BASE = "https://hn.algolia.com/api/v1"


class HackerNewsCollector(BaseCollector):
    name = "hackernews"

    def __init__(self, source_id: str = "hackernews", min_score: int = 5,
                 num_results: int = 50, search_queries: list[str] | None = None,
                 category: str | None = None):
        self._source_id = source_id
        self._min_score = min_score
        self._num_results = num_results
        self._search_queries = search_queries or []
        self._category = category

    def validate_config(self) -> bool:
        return True

    def collect(self, since: datetime | None = None) -> list[Item]:
        if self._search_queries:
            items = []
            for q in self._search_queries:
                items.extend(self._search(q, since))
            return items
        return self._fetch_recent(since)

    def _fetch_recent(self, since: datetime | None) -> list[Item]:
        params: dict = {"tags": "story", "hitsPerPage": self._num_results}
        if since:
            params["numericFilters"] = f"created_at_i>{int(since.timestamp())}"
        return self._do_search(params)

    def _search(self, query: str, since: datetime | None) -> list[Item]:
        params: dict = {"query": query, "tags": "story", "hitsPerPage": self._num_results}
        if since:
            params["numericFilters"] = f"created_at_i>{int(since.timestamp())}"
        return self._do_search(params)

    def _do_search(self, params: dict) -> list[Item]:
        try:
            resp = httpx.get(f"{ALGOLIA_BASE}/search_by_date", params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  [hackernews] API error: {e}")
            return []

        items = []
        for hit in data.get("hits", []):
            points = hit.get("points") or 0
            if points < self._min_score:
                continue

            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
            title = hit.get("title") or ""
            if not title:
                continue

            hn_tags = hit.get("_tags", [])
            tags = [t for t in hn_tags
                    if t not in ("story", "comment", "poll", "pollopt")
                    and not t.startswith("author_")
                    and not t.startswith("story_")]

            if "show_hn" in hn_tags:
                tags.append("show-hn")
            elif "ask_hn" in hn_tags:
                tags.append("ask-hn")

            published = None
            if hit.get("created_at"):
                try:
                    published = datetime.fromisoformat(hit["created_at"].replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            item = Item(
                url=url,
                title=title,
                source_id=f"{self._source_id}:{hit['objectID']}",
                source_type="rsshub",
                body=hit.get("story_text") or "",
                category=self._category,
                tags=tags,
                score=float(points),
                metadata={
                    "hn_url": f"https://news.ycombinator.com/item?id={hit['objectID']}",
                    "author": hit.get("author") or "",
                    "num_comments": hit.get("num_comments"),
                },
                published_at=published,
            )
            items.append(item)

        return items
