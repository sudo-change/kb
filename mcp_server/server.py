"""MCP stdio server for KnowledgeForge.

Tools registered here; implementations in tools.py.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running as `python mcp_server/server.py` (direct) in addition to
# `python -m mcp_server.server`.  When executed directly, the repo root
# is not on sys.path, so the `mcp_server` package import fails.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from mcp.server.fastmcp import FastMCP

from mcp_server.tools import (
    CATEGORIES,
    tool_get_items,
    tool_get_categories,
    tool_classify_item,
    tool_get_youtube_transcript,
    tool_get_daily_digest,
)

_API_BASE = os.getenv("KB_API_BASE", "http://localhost:8000")

mcp = FastMCP("KnowledgeForge")


@mcp.tool()
def get_items(
    time_range: str = "24h",
    category: str | None = None,
    q: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Return items from the knowledge base.

    time_range: how far back — e.g. '1h', '24h', '7d', '30d'.
    category: one of the 7 valid categories (optional).
    q: full-text search query (optional).
    limit: max results (default 50, max 500).
    """
    return tool_get_items(time_range=time_range, category=category, q=q, limit=limit, api_base=_API_BASE)


@mcp.tool()
def get_categories() -> list[str]:
    """Return all valid item categories."""
    return tool_get_categories()


@mcp.tool()
def classify_item(item_id: int, category: str) -> dict:
    """Set the category on an item. Returns the updated item.

    Writes to SQLite via PATCH /items/{item_id}.
    """
    return tool_classify_item(item_id=item_id, category=category, api_base=_API_BASE)


@mcp.tool()
def get_youtube_transcript(url: str) -> str:
    """Extract transcript, description, and top comments from a YouTube video.

    Invokes scripts/yt_extract.py as subprocess. Requires yt-dlp + node on PATH.
    Returns full markdown content of the extracted file.
    """
    return tool_get_youtube_transcript(url=url)


@mcp.tool()
def get_daily_digest(per_category: int = 15) -> dict[str, dict]:
    """Return today's items grouped by category (compact).

    Each category contains a 'count' (total items) and 'items' (up to
    per_category entries with id/title/url/source_type/published_at).
    Use get_items with a category filter to fetch full details.
    """
    return tool_get_daily_digest(per_category=per_category, api_base=_API_BASE)


if __name__ == "__main__":
    mcp.run()
