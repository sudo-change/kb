"""MCP tool implementations for KnowledgeForge.

Imported and registered by server.py via @mcp.tool() decorators.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

API_BASE_DEFAULT = "http://localhost:8000"

CATEGORIES = [
    "bugbounty", "ai-money", "saas-niches",
    "crypto-defi", "attacking-ai", "tools-drops", "general",
]

CATEGORY_LABELS = {
    "bugbounty":    "BugBounty",
    "ai-money":     "AI-Money",
    "saas-niches":  "SaaS-Niches",
    "crypto-defi":  "Crypto/DeFi-Alpha",
    "attacking-ai": "Attacking-AI",
    "tools-drops":  "Tools-Drops",
    "general":      "General",
}

_DISPLAY_TO_ID = {v.lower(): k for k, v in CATEGORY_LABELS.items()}
_DISPLAY_TO_ID.update({k: k for k in CATEGORIES})

_RANGE_UNITS: dict[str, int] = {"h": 3600, "d": 86400, "w": 604800}


def api_get(path: str, params: dict | None = None, base: str = API_BASE_DEFAULT) -> list | dict:
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{base}{path}", params=params)
        r.raise_for_status()
        return r.json()


def api_patch(path: str, body: dict, base: str = API_BASE_DEFAULT) -> dict:
    with httpx.Client(timeout=10) as client:
        r = client.patch(f"{base}{path}", json=body)
        r.raise_for_status()
        return r.json()


def parse_time_range(time_range: str) -> str | None:
    unit = time_range[-1].lower()
    if unit not in _RANGE_UNITS:
        return None
    try:
        n = int(time_range[:-1])
    except ValueError:
        return None
    delta = timedelta(seconds=n * _RANGE_UNITS[unit])
    return (datetime.now(timezone.utc) - delta).isoformat()


def tool_get_items(
    time_range: str = "24h",
    category: str | None = None,
    q: str | None = None,
    limit: int = 50,
    api_base: str = API_BASE_DEFAULT,
) -> list[dict]:
    params: dict = {"limit": min(limit, 500)}
    since = parse_time_range(time_range)
    if since:
        params["since"] = since
    if category:
        cat_id = _DISPLAY_TO_ID.get(category.lower(), category.lower())
        if cat_id not in CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Valid: {CATEGORIES}")
        params["category"] = cat_id
    if q:
        params["q"] = q
    return api_get("/items", params, api_base)  # type: ignore[return-value]


def tool_get_categories() -> list[str]:
    return list(CATEGORY_LABELS.values())


def tool_classify_item(
    item_id: int,
    category: str,
    api_base: str = API_BASE_DEFAULT,
) -> dict:
    cat_id = _DISPLAY_TO_ID.get(category.lower(), category.lower())
    if cat_id not in CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Valid: {CATEGORIES}")
    return api_patch(f"/items/{item_id}", {"category": cat_id}, api_base)  # type: ignore[return-value]


def tool_get_youtube_transcript(url: str) -> str:
    repo_root = Path(__file__).parent.parent
    script = repo_root / "scripts" / "yt_extract.py"

    result = subprocess.run(
        [sys.executable, str(script), url],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=str(repo_root),
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"yt_extract failed (rc={result.returncode}):\n{result.stderr[:2000]}"
        )

    for line in result.stdout.splitlines():
        if line.startswith("[+] Saved: "):
            md_path = Path(line[len("[+] Saved: "):].strip())
            if md_path.exists():
                return md_path.read_text(encoding="utf-8")

    raise RuntimeError(
        f"yt_extract succeeded but no output path found in stdout:\n{result.stdout[:500]}"
    )


_DIGEST_FIELDS = ("id", "title", "url", "source_type", "published_at")


def _compact_item(item: dict) -> dict:
    return {k: item[k] for k in _DIGEST_FIELDS if k in item}


def tool_get_daily_digest(
    per_category: int = 15,
    api_base: str = API_BASE_DEFAULT,
) -> dict[str, dict]:
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()

    items: list[dict] = api_get("/items", {"since": today, "limit": 500}, api_base)  # type: ignore[assignment]

    buckets: dict[str, list[dict]] = {CATEGORY_LABELS.get(c, c): [] for c in CATEGORIES}
    buckets["Uncategorized"] = []

    for item in items:
        raw = item.get("category")
        label = CATEGORY_LABELS.get(raw, raw) if raw else "Uncategorized"
        buckets.setdefault(label, []).append(item)

    digest: dict[str, dict] = {}
    for cat, rows in buckets.items():
        if not rows:
            continue
        digest[cat] = {
            "count": len(rows),
            "items": [_compact_item(r) for r in rows[:per_category]],
        }

    return digest
