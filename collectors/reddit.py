"""Reddit collector using the public JSON API."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone

import httpx

from collectors.base import BaseCollector
from core.models import Item

REDDIT_BASE = "https://www.reddit.com"
USER_AGENT = "KnowledgeForge/0.1 (Personal Knowledge Base)"


class RedditCollector(BaseCollector):
    name = "reddit"

    def __init__(self, subreddits: list[str] | None = None,
                 search_queries: list[str] | None = None,
                 sort: str = "hot", limit: int = 50,
                 category: str | None = None, source_id: str = "reddit"):
        self._subreddits = subreddits or []
        self._search_queries = search_queries or []
        self._sort = sort
        self._limit = limit
        self._category = category
        self._source_id = source_id
        self._headers = {"User-Agent": USER_AGENT}

    def validate_config(self) -> bool:
        if not self._subreddits and not self._search_queries:
            print("  [reddit] No subreddits or search_queries configured")
            return False
        return True

    def collect(self, since: datetime | None = None) -> list[Item]:
        items = []

        for sub in self._subreddits:
            try:
                batch = self._collect_subreddit(sub, since)
                items.extend(batch)
                print(f"  [reddit] r/{sub}: {len(batch)} posts")
                time.sleep(1)
            except Exception as e:
                print(f"  [reddit] Error r/{sub}: {e}")

        for q in self._search_queries:
            try:
                batch = self._search(q, since)
                items.extend(batch)
                print(f"  [reddit] search '{q}': {len(batch)} posts")
                time.sleep(1)
            except Exception as e:
                print(f"  [reddit] Error search '{q}': {e}")

        return items

    def _collect_subreddit(self, subreddit: str, since: datetime | None) -> list[Item]:
        url = f"{REDDIT_BASE}/r/{subreddit}/{self._sort}.json"
        params = {"limit": min(self._limit, 100), "raw_json": 1}
        try:
            resp = httpx.get(url, params=params, headers=self._headers, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            return self._parse_listing(resp.json(), since, subreddit)
        except Exception as e:
            print(f"  [reddit] API error r/{subreddit}: {e}")
            return []

    def _search(self, query: str, since: datetime | None) -> list[Item]:
        params = {"q": query, "sort": "relevance", "limit": min(self._limit, 100), "raw_json": 1}
        try:
            resp = httpx.get(f"{REDDIT_BASE}/search.json", params=params,
                             headers=self._headers, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            return self._parse_listing(resp.json(), since)
        except Exception as e:
            print(f"  [reddit] Search API error: {e}")
            return []

    def _parse_listing(self, data: dict, since: datetime | None, subreddit: str | None = None) -> list[Item]:
        items = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            if not post:
                continue

            created_utc = post.get("created_utc")
            published = datetime.fromtimestamp(created_utc, tz=timezone.utc) if created_utc else None

            if since and published and published < since:
                continue

            permalink = post.get("permalink", "")
            post_url = f"https://reddit.com{permalink}" if permalink else post.get("url", "")
            title = post.get("title", "")
            if not title:
                continue

            sub = post.get("subreddit", subreddit or "")
            flair = post.get("link_flair_text", "")
            tags = [f"r/{sub}"] if sub else []
            if flair:
                tags.append(flair.lower())

            selftext = post.get("selftext", "")
            summary = (selftext[:300] + "...") if len(selftext) > 300 else selftext

            post_id = post.get("id") or hashlib.md5(post_url.encode()).hexdigest()[:12]

            item = Item(
                url=post_url,
                title=title,
                source_id=f"{self._source_id}:{post_id}",
                source_type="rsshub",
                body=selftext,
                summary=summary,
                category=self._category,
                tags=tags,
                score=float(post.get("score") or 0),
                metadata={
                    "subreddit": sub,
                    "upvote_ratio": post.get("upvote_ratio"),
                    "is_self": post.get("is_self", False),
                    "domain": post.get("domain", ""),
                    "external_url": post.get("url") if not post.get("is_self") else None,
                    "flair": flair,
                    "num_comments": post.get("num_comments"),
                    "author": post.get("author", ""),
                },
                published_at=published,
            )
            items.append(item)

        return items
