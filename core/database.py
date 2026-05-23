"""SQLite + FTS5 storage layer for KnowledgeForge."""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from core.models import CollectionRun, HealthInfo, Item, Source, YTExtract

log = logging.getLogger("kf.database")

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    url          TEXT UNIQUE NOT NULL,
    title        TEXT NOT NULL,
    body         TEXT NOT NULL DEFAULT '',
    summary      TEXT NOT NULL DEFAULT '',
    source_id    TEXT NOT NULL,
    source_type  TEXT NOT NULL,
    category     TEXT,
    quest_id     TEXT,
    score        REAL NOT NULL DEFAULT 0,
    tags         TEXT NOT NULL DEFAULT '[]',
    metadata     TEXT NOT NULL DEFAULT '{}',
    collected_at TEXT NOT NULL,
    published_at TEXT,
    is_read      INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_items_category  ON items(category);
CREATE INDEX IF NOT EXISTS idx_items_source    ON items(source_id);
CREATE INDEX IF NOT EXISTS idx_items_collected ON items(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_items_url       ON items(url);

CREATE TABLE IF NOT EXISTS sources (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    type       TEXT NOT NULL,
    config     TEXT NOT NULL DEFAULT '{}',
    glyph      TEXT NOT NULL DEFAULT '',
    category   TEXT,
    enabled    INTEGER NOT NULL DEFAULT 1,
    last_fetch TEXT,
    error      TEXT
);

CREATE TABLE IF NOT EXISTS yt_extracts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id     TEXT UNIQUE NOT NULL,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    transcript   TEXT NOT NULL DEFAULT '',
    subtitles    TEXT NOT NULL DEFAULT '',
    comments     TEXT NOT NULL DEFAULT '[]',
    duration     INTEGER,
    channel      TEXT NOT NULL DEFAULT '',
    file_path    TEXT NOT NULL DEFAULT '',
    extracted_at TEXT NOT NULL,
    item_id      INTEGER REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS collection_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    items_added INTEGER NOT NULL DEFAULT 0,
    errors      TEXT NOT NULL DEFAULT '[]'
);
"""

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
    title, body, summary, tags,
    content='items',
    content_rowid='id',
    tokenize='porter unicode61'
);
"""

FTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS items_ai AFTER INSERT ON items BEGIN
    INSERT INTO items_fts(rowid, title, body, summary, tags)
    VALUES (new.id, new.title, new.body, new.summary, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS items_au AFTER UPDATE ON items BEGIN
    INSERT INTO items_fts(items_fts, rowid, title, body, summary, tags)
    VALUES ('delete', old.id, old.title, old.body, old.summary, old.tags);
    INSERT INTO items_fts(rowid, title, body, summary, tags)
    VALUES (new.id, new.title, new.body, new.summary, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS items_ad AFTER DELETE ON items BEGIN
    INSERT INTO items_fts(items_fts, rowid, title, body, summary, tags)
    VALUES ('delete', old.id, old.title, old.body, old.summary, old.tags);
END;
"""


class DB:
    def __init__(self, path: str | Path):
        self.db_path = Path(path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=60)
        self.conn.row_factory = sqlite3.Row
        try:
            self.conn.execute("PRAGMA journal_mode=DELETE")
        except sqlite3.OperationalError:
            pass
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA busy_timeout=60000")
        self._init_schema()

    def _init_schema(self):
        deadline = time.time() + 300
        while True:
            try:
                self.conn.executescript(SCHEMA)
                self.conn.executescript(FTS_SCHEMA)
                self.conn.executescript(FTS_TRIGGERS)
                self.conn.commit()
                return
            except sqlite3.OperationalError as e:
                msg = str(e).lower()
                if ("disk i/o" in msg or "locked" in msg) and time.time() < deadline:
                    log.warning("DB busy, retrying in 10s... (%s)", e)
                    time.sleep(10)
                    try:
                        self.conn.close()
                    except Exception:
                        pass
                    self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=60)
                    self.conn.row_factory = sqlite3.Row
                    try:
                        self.conn.execute("PRAGMA journal_mode=DELETE")
                    except sqlite3.OperationalError:
                        pass
                    self.conn.execute("PRAGMA foreign_keys=ON")
                    continue
                raise

    def close(self):
        self.conn.close()

    # ── Items ──────────────────────────────────────────────────────────────────

    def store_items(self, items: list[Item]) -> int:
        """Insert new items, skip duplicates by URL. Returns count added."""
        added = 0
        for item in items:
            try:
                cursor = self.conn.execute(
                    """INSERT INTO items
                       (url, title, body, summary, source_id, source_type,
                        category, quest_id, score, tags, metadata,
                        collected_at, published_at, is_read)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(url) DO NOTHING""",
                    (
                        item.url,
                        item.title,
                        item.body,
                        item.summary,
                        item.source_id,
                        item.source_type,
                        item.category,
                        item.quest_id,
                        item.score,
                        json.dumps(item.tags),
                        json.dumps(item.metadata),
                        item.collected_at.isoformat(),
                        item.published_at.isoformat() if item.published_at else None,
                        int(item.is_read),
                    ),
                )
                if cursor.rowcount > 0:
                    added += 1
            except sqlite3.Error as e:
                log.error("DB error inserting %s: %s", item.url, e)
        self.conn.commit()
        return added

    def get_items(self, opts: dict) -> list[dict]:
        """Query items with optional filters. opts keys: category, source_id,
        since, until, q (FTS), limit, offset."""
        conditions = []
        params: list = []

        q = opts.get("q")
        if q and q.strip():
            safe = " ".join(f'"{w}"' for w in q.strip().split() if w)
            conditions.append("i.id IN (SELECT rowid FROM items_fts WHERE items_fts MATCH ?)")
            params.append(safe)

        if opts.get("category"):
            conditions.append("i.category = ?")
            params.append(opts["category"])

        if opts.get("source_id"):
            conditions.append("i.source_id = ?")
            params.append(opts["source_id"])

        if opts.get("since"):
            since = opts["since"]
            if isinstance(since, datetime):
                since = since.isoformat()
            conditions.append("i.collected_at >= ?")
            params.append(since)

        if opts.get("until"):
            until = opts["until"]
            if isinstance(until, datetime):
                until = until.isoformat()
            conditions.append("i.collected_at <= ?")
            params.append(until)

        where = " AND ".join(conditions) if conditions else "1=1"
        limit = opts.get("limit", 50)
        offset = opts.get("offset", 0)

        rows = self.conn.execute(
            f"SELECT * FROM items i WHERE {where} ORDER BY i.collected_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

        return [self._row_to_dict(r) for r in rows]

    def get_item(self, item_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def update_item(self, opts: dict) -> dict | None:
        """Update category, score, tags, or summary on an item."""
        item_id = opts["id"]
        sets = []
        params = []

        if "category" in opts:
            sets.append("category = ?")
            params.append(opts["category"])
        if "score" in opts and opts["score"] is not None:
            sets.append("score = ?")
            params.append(opts["score"])
        if "tags" in opts and opts["tags"] is not None:
            sets.append("tags = ?")
            params.append(json.dumps(opts["tags"]))
        if "summary" in opts and opts["summary"] is not None:
            sets.append("summary = ?")
            params.append(opts["summary"])

        if not sets:
            return self.get_item(item_id)

        params.append(item_id)
        self.conn.execute(f"UPDATE items SET {', '.join(sets)} WHERE id = ?", params)
        self.conn.commit()
        return self.get_item(item_id)

    # ── Sources ────────────────────────────────────────────────────────────────

    def get_sources(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM sources ORDER BY name").fetchall()
        return [dict(r) for r in rows]

    def add_source(self, source: Source) -> dict:
        self.conn.execute(
            """INSERT INTO sources (id, name, type, config, glyph, category, enabled)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, type=excluded.type, config=excluded.config,
                 glyph=excluded.glyph, category=excluded.category, enabled=excluded.enabled""",
            (
                source.id, source.name, source.type,
                json.dumps(source.config), source.glyph,
                source.category, int(source.enabled),
            ),
        )
        self.conn.commit()
        return dict(self.conn.execute("SELECT * FROM sources WHERE id = ?", (source.id,)).fetchone())

    def remove_source(self, source_id: str) -> None:
        self.conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        self.conn.commit()

    def update_source_fetch(self, opts: dict) -> None:
        self.conn.execute(
            "UPDATE sources SET last_fetch = ?, error = ? WHERE id = ?",
            (
                datetime.now(timezone.utc).isoformat(),
                opts.get("error"),
                opts["id"],
            ),
        )
        self.conn.commit()

    # ── Collection runs ────────────────────────────────────────────────────────

    def log_run(self, opts: dict) -> None:
        """Write a collection_runs row. opts: items_added, errors, started_at."""
        started = opts.get("started_at", datetime.now(timezone.utc))
        if isinstance(started, datetime):
            started = started.isoformat()
        self.conn.execute(
            """INSERT INTO collection_runs (started_at, finished_at, items_added, errors)
               VALUES (?, ?, ?, ?)""",
            (
                started,
                datetime.now(timezone.utc).isoformat(),
                opts.get("items_added", 0),
                json.dumps(opts.get("errors", [])),
            ),
        )
        self.conn.commit()

    def get_health(self) -> HealthInfo:
        last_run_row = self.conn.execute(
            "SELECT finished_at FROM collection_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        last_run = None
        if last_run_row and last_run_row[0]:
            try:
                last_run = datetime.fromisoformat(last_run_row[0])
            except ValueError:
                pass

        today = datetime.now(timezone.utc).date().isoformat()
        items_today = self.conn.execute(
            "SELECT COUNT(*) FROM items WHERE collected_at >= ?", (today,)
        ).fetchone()[0]

        errors_row = self.conn.execute(
            "SELECT errors FROM collection_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        errors: list[str] = []
        if errors_row and errors_row[0]:
            try:
                errors = json.loads(errors_row[0])
            except (ValueError, TypeError):
                pass

        return HealthInfo(last_run=last_run, items_today=items_today, errors=errors)

    # ── YT Extracts ────────────────────────────────────────────────────────────

    def store_yt_extract(self, yt: YTExtract) -> int | None:
        try:
            cursor = self.conn.execute(
                """INSERT INTO yt_extracts
                   (video_id, title, description, transcript, subtitles, comments,
                    duration, channel, file_path, extracted_at, item_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(video_id) DO UPDATE SET
                     transcript=excluded.transcript,
                     file_path=excluded.file_path,
                     extracted_at=excluded.extracted_at""",
                (
                    yt.video_id, yt.title, yt.description,
                    yt.transcript, yt.subtitles,
                    json.dumps(yt.comments),
                    yt.duration, yt.channel, yt.file_path,
                    yt.extracted_at.isoformat(),
                    yt.item_id,
                ),
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            log.error("DB error storing yt_extract %s: %s", yt.video_id, e)
            return None

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_dict(row) -> dict:
        d = dict(row)
        for key in ("tags", "metadata"):
            if key in d and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except (ValueError, TypeError):
                    d[key] = []
        return d
