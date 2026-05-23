"""Keyword-based item classifier using config/categories.yaml rules.

Matches whole words (case-insensitive) against title + body + tags.
Order in categories.yaml matters: first matching category wins.
General is the fallback when no keywords match.
"""

from __future__ import annotations

import re
from functools import lru_cache

from core.config import load_categories


@lru_cache(maxsize=1)
def _load_rules(config_path: str = "config/categories.yaml") -> list[tuple[str, list[re.Pattern[str]]]]:
    """Load category rules and compile keyword patterns once."""
    raw = load_categories(config_path)
    categories = raw.get("categories", [])

    rules: list[tuple[str, list[re.Pattern[str]]]] = []
    for cat in categories:
        cat_id = cat.get("id", "")
        keywords = cat.get("keywords", [])
        if not keywords:
            continue
        patterns = [
            re.compile(r"\b" + re.escape(kw.lower()) + r"\b")
            for kw in keywords
        ]
        rules.append((cat_id, patterns))
    return rules


def classify(title: str, body: str = "", tags: list[str] | None = None) -> str | None:
    """Return the first matching category ID, or None if only general matches.

    Searches title + body + joined tags as a single text blob.
    First category whose keyword matches wins (order from YAML).
    Returns None when no non-general category matches, letting the
    caller decide whether to keep the source-level category or default.
    """
    parts = [title, body]
    if tags:
        parts.append(" ".join(tags))
    text = " ".join(parts).lower()

    for cat_id, patterns in _load_rules():
        for pat in patterns:
            if pat.search(text):
                return cat_id
    return None


def classify_item(item) -> str | None:
    """Convenience wrapper that accepts an Item dataclass."""
    return classify(
        title=item.title,
        body=item.body,
        tags=item.tags if item.tags else None,
    )
