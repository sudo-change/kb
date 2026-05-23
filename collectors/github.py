"""GitHub collector — trending repos and search."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from collectors.base import BaseCollector
from core.models import Item

GITHUB_API = "https://api.github.com"


class GitHubCollector(BaseCollector):
    name = "github"

    def __init__(self, source_id: str = "github-trending", token: str = "",
                 trending: bool = True, search_queries: list[str] | None = None,
                 category: str | None = None):
        self._source_id = source_id
        self._trending = trending
        self._search_queries = search_queries or []
        self._category = category
        self._headers = {"Accept": "application/vnd.github.v3+json"}
        if token and not token.startswith("$"):
            self._headers["Authorization"] = f"Bearer {token}"

    def validate_config(self) -> bool:
        return True

    def collect(self, since: datetime | None = None) -> list[Item]:
        items = []

        if self._trending:
            batch = self._collect_trending(since)
            items.extend(batch)
            print(f"  [github] Trending: {len(batch)} repos")

        for q in self._search_queries:
            batch = self._search_repos(q, since)
            items.extend(batch)
            print(f"  [github] Search '{q}': {len(batch)} repos")

        return items

    def _collect_trending(self, since: datetime | None) -> list[Item]:
        date_str = since.strftime("%Y-%m-%d") if since else "2024-01-01"
        params = {"q": f"created:>{date_str} stars:>10", "sort": "stars", "order": "desc", "per_page": 30}
        return self._search_api(params)

    def _search_repos(self, query: str, since: datetime | None) -> list[Item]:
        q = query
        if since:
            q += f" pushed:>{since.strftime('%Y-%m-%d')}"
        params = {"q": q, "sort": "updated", "order": "desc", "per_page": 20}
        return self._search_api(params)

    def _search_api(self, params: dict) -> list[Item]:
        try:
            resp = httpx.get(f"{GITHUB_API}/search/repositories", params=params,
                             headers=self._headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  [github] API error: {e}")
            return []

        items = []
        for repo in data.get("items", []):
            item = self._repo_to_item(repo)
            if item:
                items.append(item)
        return items

    def _repo_to_item(self, repo: dict) -> Item | None:
        full_name = repo.get("full_name", "")
        if not full_name:
            return None

        tags = list(repo.get("topics", []))
        lang = repo.get("language")
        if lang:
            tags.append(lang.lower())

        pushed_at = None
        if repo.get("pushed_at"):
            try:
                pushed_at = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        description = repo.get("description") or ""
        stars = repo.get("stargazers_count", 0)

        return Item(
            url=repo.get("html_url", f"https://github.com/{full_name}"),
            title=full_name,
            source_id=f"{self._source_id}:{repo.get('id', full_name)}",
            source_type="rsshub",
            body=description,
            summary=description[:300],
            category=self._category,
            tags=tags,
            score=float(stars),
            metadata={
                "stars": stars,
                "forks": repo.get("forks_count"),
                "language": lang,
                "license": (repo.get("license") or {}).get("spdx_id"),
                "owner": repo.get("owner", {}).get("login", ""),
            },
            published_at=pushed_at,
        )
