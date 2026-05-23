"""Telegram MarkdownV2 formatting for digest messages."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any


# Use lowercase category IDs matching DB/classifier (categories.yaml)
CATEGORIES = [
    "bugbounty",
    "ai-money",
    "saas-niches",
    "crypto-defi",
    "attacking-ai",
    "tools-drops",
    "general",
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

CATEGORY_EMOJI = {
    "bugbounty":    "🐛",
    "ai-money":     "💰",
    "saas-niches":  "📦",
    "crypto-defi":  "🔐",
    "attacking-ai": "🤖",
    "tools-drops":  "🛠",
    "general":      "📰",
}

_ESCAPE_RE = re.compile(r"([_*\[\]()~`>#+\-=|{}.!\\])")


def escape(text: str) -> str:
    """Escape special chars for Telegram MarkdownV2."""
    return _ESCAPE_RE.sub(r"\\\1", text)


def format_item(item: dict[str, Any]) -> str:
    title = escape(item.get("title", "Untitled")[:120])
    url = item.get("url", "")
    summary = item.get("summary") or ""
    if summary:
        summary_line = f"\n_{escape(summary[:200])}_"
    else:
        summary_line = ""
    return f"• [{title}]({url}){summary_line}"


def format_digest(category: str, items: list[dict[str, Any]], run_date: date | None = None) -> str:
    """Build full digest message for one category topic."""
    day = (run_date or date.today()).strftime("%Y-%m-%d")
    label = CATEGORY_LABELS.get(category, category)
    emoji = CATEGORY_EMOJI.get(category, "📌")
    header = escape(f"{emoji} {label} — {day}")
    lines = [f"*{header}*", ""]
    for item in items:
        lines.append(format_item(item))
    lines.append("")
    lines.append(escape(f"{len(items)} item(s)"))
    return "\n".join(lines)


def format_status(
    health: dict[str, Any],
    per_source: dict[str, int],
    errors: list[str],
) -> str:
    """Build status topic message."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"*{escape('📊 Pipeline Status — ' + ts)}*", ""]

    if per_source:
        lines.append(escape("Items collected by source:"))
        for src, count in sorted(per_source.items()):
            lines.append(escape(f"  {src}: {count}"))
        lines.append("")

    last_run = health.get("last_run")
    if last_run:
        lines.append(escape(f"Last run: {last_run}"))

    items_today = health.get("items_today", 0)
    lines.append(escape(f"Items today: {items_today}"))

    if errors:
        lines.append("")
        lines.append(escape("⚠️ Errors:"))
        for err in errors[:10]:
            lines.append(escape(f"  • {err[:200]}"))
    else:
        lines.append(escape("✅ No errors"))

    return "\n".join(lines)
