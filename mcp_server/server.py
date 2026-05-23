"""MCP stdio server for KnowledgeForge.

Tools:
  get_items           — query items by time_range / category / FTS
  get_categories      — list valid categories
  classify_item       — write category back to SQLite via API
  get_youtube_transcript — trigger yt_extract.py, return markdown
  get_daily_digest    — today's items grouped by category
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = "http://localhost:8000"

CATEGORIES = [
    "BugBounty", "AI-Money", "SaaS-Niches",
    "Crypto-DeFi-Alpha", "Attacking-AI", "Tools-Drops", "General",
]

_RANGE_UNITS: dict[str, int] = {"h": 3600, "d": 86400, "w": 604800}

mcp = FastMCP("KnowledgeForge")


def _api_get(path: str, params: dict | None = None) -> list | dict:
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{API_BASE}{path}", params=params)
        r.raise_for_status()
        return r.json()


def _api_patch(path: str, body: dict) -> dict:
    with httpx.Client(timeout=10) as client:
        r = client.patch(f"{API_BASE}{path}", json=body)
        r.raise_for_status()
        return r.json()


def _parse_time_range(time_range: str) -> str | None:
    """Convert '24h' / '7d' / '2w' to ISO-8601 datetime string."""
    unit = time_range[-1].lower()
    if unit not in _RANGE_UNITS:
        return None
    try:
        n = int(time_range[:-1])
    except ValueError:
        return None
    delta = timedelta(seconds=n * _RANGE_UNITS[unit])
    return (datetime.now(timezone.utc) - delta).isoformat()


@mcp.tool()
def get_items(
    time_range: str = "24h",
    category: str | None = None,
    q: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Return items from the knowledge base.

    time_range: how far back to look — e.g. '1h', '24h', '7d', '30d'.
    category: one of the 7 valid categories (optional).
    q: full-text search query (optional).
    limit: max results (default 50, max 500).
    """
    params: dict = {"limit": min(limit, 500)}

    since = _parse_time_range(time_range)
    if since:
        params["since"] = since

    if category:
        if category not in CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Valid: {CATEGORIES}")
        params["category"] = category

    if q:
        params["q"] = q

    return _api_get("/items", params)  # type: ignore[return-value]


@mcp.tool()
def get_categories() -> list[str]:
    """Return all valid item categories."""
    return CATEGORIES


@mcp.tool()
def classify_item(item_id: int, category: str) -> dict:
    """Set the category on an item. Returns the updated item.

    Writes directly to SQLite via PATCH /items/{item_id}.
    """
    if category not in CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Valid: {CATEGORIES}")
    return _api_patch(f"/items/{item_id}", {"category": category})  # type: ignore[return-value]


@mcp.tool()
def get_youtube_transcript(url: str) -> str:
    """Extract transcript, description, and top comments from a YouTube video.

    Invokes scripts/yt_extract.py as a subprocess. Requires yt-dlp + node on PATH.
    Returns the full markdown content of the extracted file.
    """
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


@mcp.tool()
def get_daily_digest() -> dict[str, list[dict]]:
    """Return today's items grouped by category.

    Fetches items collected since midnight UTC, groups them by category.
    Empty categories are omitted.
    """
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()

    items: list[dict] = _api_get("/items", {"since": today, "limit": 500})  # type: ignore[assignment]

    digest: dict[str, list[dict]] = {cat: [] for cat in CATEGORIES}
    digest["Uncategorized"] = []

    for item in items:
        cat = item.get("category") or "Uncategorized"
        digest.setdefault(cat, []).append(item)

    return {cat: rows for cat, rows in digest.items() if rows}


if __name__ == "__main__":
    mcp.run()
