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
    "BugBounty", "AI-Money", "SaaS-Niches",
    "Crypto-DeFi-Alpha", "Attacking-AI", "Tools-Drops", "General",
]

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
        if category not in CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Valid: {CATEGORIES}")
        params["category"] = category
    if q:
        params["q"] = q
    return api_get("/items", params, api_base)  # type: ignore[return-value]


def tool_get_categories() -> list[str]:
    return CATEGORIES


def tool_classify_item(
    item_id: int,
    category: str,
    api_base: str = API_BASE_DEFAULT,
) -> dict:
    if category not in CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Valid: {CATEGORIES}")
    return api_patch(f"/items/{item_id}", {"category": category}, api_base)  # type: ignore[return-value]


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


def tool_get_daily_digest(api_base: str = API_BASE_DEFAULT) -> dict[str, list[dict]]:
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()

    items: list[dict] = api_get("/items", {"since": today, "limit": 500}, api_base)  # type: ignore[assignment]

    digest: dict[str, list[dict]] = {cat: [] for cat in CATEGORIES}
    digest["Uncategorized"] = []

    for item in items:
        cat = item.get("category") or "Uncategorized"
        digest.setdefault(cat, []).append(item)

    return {cat: rows for cat, rows in digest.items() if rows}
