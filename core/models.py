"""Item schema and related dataclasses for KnowledgeForge."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Item:
    """Atomic unit of ingestion. Maps 1:1 to the items table."""

    url: str
    title: str
    source_id: str
    source_type: str  # 'rsshub', 'rss', 'youtube', 'manual', 'telegram'

    body: str = ""
    summary: str = ""
    category: str | None = None
    quest_id: str | None = None
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: datetime | None = None
    is_read: bool = False


@dataclass
class Source:
    """A configured collection source."""

    id: str
    name: str
    type: str  # 'rsshub', 'youtube_channel', 'rss', 'telegram_channel'
    config: dict[str, Any] = field(default_factory=dict)
    glyph: str = ""
    category: str | None = None
    enabled: bool = True
    last_fetch: datetime | None = None
    error: str | None = None


@dataclass
class YTExtract:
    """YouTube video extract linked to an item."""

    video_id: str
    title: str
    description: str = ""
    transcript: str = ""
    subtitles: str = ""
    comments: list[str] = field(default_factory=list)
    duration: int | None = None
    channel: str = ""
    file_path: str = ""
    extracted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    item_id: int | None = None


@dataclass
class CollectionRun:
    """Audit log row for each collection cycle."""

    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    items_added: int = 0
    errors: list[str] = field(default_factory=list)
    id: int | None = None


@dataclass
class HealthInfo:
    last_run: datetime | None
    items_today: int
    errors: list[str]
