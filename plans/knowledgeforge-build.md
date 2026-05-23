# PRD: KnowledgeForge Build Plan — Phase 0 → 6

## Problem Statement

You consume hundreds of signals per week across bug bounty writeups, AI security research, SaaS niche drops, crypto alpha, and dev tooling — spread across Reddit, HN, GitHub, YouTube, Twitter, Telegram, and 50+ blogs. By the time you see something, the opportunity window may be closed. You have a 4-month runway and need money flow in 30 days.

You have a prior (unfinished) Python codebase at `D:\KnowledgeBase` with working collectors and a working database layer. You have a fresh repo (`KnowledgeBase_Final`) with a solid PRD, a working YT extractor, and a Quarry React dashboard that runs on seed data.

The gap: nothing collects, nothing stores, nothing surfaces, nothing delivers.

## Solution

Port the working legacy collectors into KnowledgeBase_Final (Phase 0), then build each layer in dependency order: SQLite → collectors → API → Quarry wiring → Telegram delivery → MCP exposure → Docker full stack.

The system is a **data lake + display pipeline only**. No LLM API keys inside. Intelligence (classification, summarization, newsletter generation) is applied externally by Claude routines connecting via MCP.

```
Sources → Collectors → SQLite → API → Quarry (display)
                                    → Telegram (deliver)
                                    → MCP (Claude routines pull)
```

## User Stories

1. As a researcher, I want the working legacy collector code ported from `D:\KnowledgeBase\kb-clean\projects\knowledgeforge\` into KnowledgeBase_Final so I don't rewrite what already works.
2. As a researcher, I want a SQLite database with FTS5 created at `data/kf.db` with the `items` schema so all collected content has a single source of truth.
3. As a researcher, I want RSS/Atom feeds collected from PortSwigger, Trail of Bits, IndieHackers, Pointer, news.barelyhuman.xyz, and 10+ other sources so blog posts land in my KB automatically.
4. As a researcher, I want Reddit posts from r/netsec, r/bugbounty, r/MachineLearning, r/LocalLLaMA, r/SideProject, r/SaaS, r/defi collected every 15 minutes so I never miss time-sensitive posts.
5. As a researcher, I want HN Best and HN Show collected so high-signal tech discussions land in my KB.
6. As a researcher, I want GitHub trending repos (daily) collected so new tool drops surface immediately.
7. As a researcher, I want YouTube channels (LiveOverflow, JohnHammond, IppSec, NetworkChuck, ThePrimeagen) monitored for new videos with transcripts auto-extracted so video content is searchable as text.
8. As a researcher, I want yt-dlp to extract transcript + description + top 3 comments from any YouTube URL I paste so I can ingest any video on demand.
9. As a researcher, I want fallback to English subtitles when transcript extraction fails so no video goes unprocessed.
10. As a researcher, I want extracted YouTube content saved as markdown files named by video title at `data/yt_extracts/` so I can find them by name.
11. As a researcher, I want all items stored in SQLite with URL deduplication so the database stays clean across repeated collection runs.
12. As a researcher, I want a FastAPI service at localhost:8000 exposing GET /items, GET /sources, and GET /health so the Quarry dashboard and MCP server have a single data interface.
13. As a researcher, I want GET /items to support filtering by category, source, date range, and full-text search query so I can slice the data any way I need.
14. As a researcher, I want Quarry dashboard to read from the real API instead of seed data so it shows actual collected intelligence.
15. As a researcher, I want Quarry to filter items by the 7 newsletter categories so I can focus one vertical at a time.
16. As a researcher, I want items scored by quest relevance in Quarry so high-signal items surface first.
17. As a researcher, I want to add new sources via Quarry's AddSourceForm UI so I can expand coverage without editing config files.
18. As a researcher, I want a Telegram bot that posts daily digests to a private group with Topics — one topic per newsletter category plus a status topic — so I get intelligence on my phone.
19. As a researcher, I want the Telegram status topic to show items collected per source, errors, and last run time so I know the pipeline is healthy.
20. As a researcher, I want Telegram Premium features used (no 4096-char truncation) so digests are never cut off.
21. As a researcher, I want Telegram channels I follow (security, AI, crypto) ingested as KB sources via the Pyrogram-based collector so Telegram content joins the same pipeline.
22. As a researcher, I want an MCP server exposing get_items, get_categories, classify_item, get_youtube_transcript, and get_daily_digest tools so Claude routines can pull and process data.
23. As a researcher, I want classify_item to write a category back to SQLite so Claude routines can categorize items without me touching the DB.
24. As a researcher, I want time-windowed MCP queries ("last 24h", "this week") so Claude routines always get fresh data only.
25. As a researcher, I want a single `docker-compose up -d` to start all services (RSSHub, Collector, API, MCP, Telegram Bot) so the full stack runs in one command.
26. As a researcher, I want data persisted via volume mounts (`./data`, `./cookies`) so restarts never lose collected intelligence.
27. As a researcher, I want a `scripts/manual_collect.ps1` CLI to force-refresh all sources immediately so I can trigger collection on demand.
28. As a researcher, I want collection errors logged to a `collection_runs` table so I can diagnose source failures without reading raw logs.
29. As a researcher, I want marginalia-search.com, buzzing.cc, hackertab.dev, pointer.io, and serializer.io added as RSS sources so independent web content enters my KB.
30. As a researcher, I want a GET /health endpoint showing last collection time per source and any failures so I can monitor pipeline health without opening logs.

## Modules

```
# Phase 0 — Legacy Salvage (port from D:\KnowledgeBase\kb-clean\projects\knowledgeforge\)
CREATE  collectors/__init__.py
CREATE  collectors/base.py                   (ported from legacy collectors/base.py)
CREATE  collectors/rss.py                    (ported from legacy collectors/rss.py)
CREATE  collectors/hackernews.py             (ported from legacy collectors/hackernews.py)
CREATE  collectors/reddit.py                 (ported from legacy collectors/reddit.py)
CREATE  collectors/github.py                 (ported from legacy collectors/github_collector.py)
CREATE  collectors/youtube.py                (ported from legacy collectors/youtube.py)
CREATE  collectors/telegram_channel.py       (ported from legacy collectors/telegram.py)
CREATE  core/__init__.py
CREATE  core/database.py                     (ported from legacy, adapted to items schema)
CREATE  core/models.py                       (ported from legacy, adapted field names)
CREATE  core/config.py                       (ported from legacy)
CREATE  core/scheduler.py                    (ported from legacy)
CREATE  core/retry.py                        (ported from legacy, copy-as-is)
CREATE  requirements.txt                     (merged from legacy + new deps)

# Phase 1 — SQLite Foundation
MODIFY  core/database.py                     (reason: use items/sources/yt_extracts/collection_runs schema from PRD v1)
MODIFY  core/models.py                       (reason: Item/Source/YTExtract dataclasses matching new schema)

# Phase 2 — Collectors + Config
CREATE  config/sources.yaml                  (default source list — see Source Map)
CREATE  config/categories.yaml              (7 newsletter categories with keywords)
CREATE  collector/main.py                    (entry point, APScheduler 15-min interval)
CREATE  scripts/manual_collect.ps1           (PowerShell force-collect trigger)

# Phase 3 — FastAPI + Quarry Wiring
CREATE  api/__init__.py
CREATE  api/main.py                          (FastAPI app, CORS, lifespan)
CREATE  api/routes/__init__.py
CREATE  api/routes/items.py                  (GET /items, GET /items/{id}, PATCH /items/{id})
CREATE  api/routes/sources.py                (GET /sources, POST /sources, DELETE /sources/{id})
CREATE  api/routes/health.py                 (GET /health)
CREATE  api/Dockerfile
MODIFY  quarry/app.jsx                       (reason: fetch from API instead of importing data.js)
CREATE  quarry/api.js                        (API client, base URL config)

# Phase 4 — Telegram Delivery
CREATE  telegram_bot/__init__.py
CREATE  telegram_bot/bot.py                  (digest delivery, topic routing)
CREATE  telegram_bot/formatter.py            (message formatting, Telegram markdown)
CREATE  telegram_bot/scheduler.py            (daily cron at 8 AM local)

# Phase 5 — MCP Server
CREATE  mcp_server/__init__.py
CREATE  mcp_server/server.py                 (MCP stdio server, tool registration)
CREATE  mcp_server/tools.py                  (get_items, get_categories, classify_item, get_youtube_transcript, get_daily_digest)

# Phase 6 — Docker Full Stack
CREATE  docker-compose.yml                   (RSSHub + Collector + API + MCP + Telegram Bot)
CREATE  collector/Dockerfile
MODIFY  README.md                            (reason: update Quick Start with working commands)
MODIFY  AGENTS.md                            (reason: add legacy reference section)
CREATE  docs/legacy-manifest.md             (salvage audit table)
CREATE  .env.example                         (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, etc.)
```

## Schema Changes

```sql
-- Primary items table (replaces legacy 'documents')
CREATE TABLE items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    url          TEXT UNIQUE NOT NULL,
    title        TEXT NOT NULL,
    body         TEXT,
    summary      TEXT,
    source_id    TEXT NOT NULL,
    source_type  TEXT NOT NULL,           -- 'rsshub', 'youtube', 'manual', 'telegram'
    category     TEXT,                    -- NULL until classified by Claude via MCP
    quest_id     TEXT,                    -- maps to quarry quest
    score        REAL DEFAULT 0,
    tags         TEXT,                    -- JSON array
    metadata     TEXT,                    -- JSON blob (comments, points, etc.)
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME,
    is_read      BOOLEAN DEFAULT 0
);

CREATE INDEX idx_items_category   ON items(category);
CREATE INDEX idx_items_source     ON items(source_id);
CREATE INDEX idx_items_collected  ON items(collected_at DESC);
CREATE INDEX idx_items_url        ON items(url);

-- FTS5 for full-text search
CREATE VIRTUAL TABLE items_fts USING fts5(
    title, body, summary, tags,
    content='items', content_rowid='id',
    tokenize='porter unicode61'
);

-- Sources registry
CREATE TABLE sources (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    type       TEXT NOT NULL,             -- 'rsshub', 'youtube_channel', 'rss', 'telegram_channel'
    config     TEXT NOT NULL,             -- JSON (url, channel_id, subreddit, etc.)
    glyph      TEXT,
    category   TEXT,                      -- default category for items from this source
    enabled    BOOLEAN DEFAULT 1,
    last_fetch DATETIME,
    error      TEXT
);

-- YouTube extracts (linked to items)
CREATE TABLE yt_extracts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id     TEXT UNIQUE NOT NULL,
    title        TEXT NOT NULL,
    description  TEXT,
    transcript   TEXT,
    subtitles    TEXT,
    comments     TEXT,                    -- JSON array of top 3
    duration     INTEGER,
    channel      TEXT,
    file_path    TEXT,
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    item_id      INTEGER REFERENCES items(id)
);

-- Collection run audit log
CREATE TABLE collection_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    items_added INTEGER DEFAULT 0,
    errors      TEXT                      -- JSON array of error messages
);
```

## Service Interfaces

```python
# core/database.py
class DB:
    def __init__(self, path: str): ...

    def store_items(self, items: list[Item]) -> int:
        """Insert new items (skip duplicates by URL). Returns count added."""

    def get_items(self, opts: {
        "category": str | None,
        "source_id": str | None,
        "since": datetime | None,
        "until": datetime | None,
        "q": str | None,           # FTS query
        "limit": int,
        "offset": int
    }) -> list[Item]: ...

    def get_item(self, id: int) -> Item | None: ...

    def update_item(self, opts: {
        "id": int,
        "category": str | None,
        "score": float | None,
        "tags": list[str] | None,
        "summary": str | None
    }) -> Item: ...

    def get_sources(self) -> list[Source]: ...
    def add_source(self, source: Source) -> Source: ...
    def remove_source(self, id: str) -> None: ...
    def update_source_fetch(self, opts: {"id": str, "error": str | None}) -> None: ...

    def log_run(self, opts: {"items_added": int, "errors": list[str]}) -> None: ...
    def get_health(self) -> HealthInfo: ...

# collectors/base.py
class BaseCollector:
    name: str

    def validate_config(self) -> bool: ...

    def collect(self, opts: {
        "since": datetime | None,
        "cookies_path": str | None
    }) -> list[RawItem]: ...

# api/routes/items.py
@router.get("/items")
async def list_items(
    category: str | None = None,
    source: str | None = None,
    since: str | None = None,        # ISO datetime string
    until: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0
) -> ItemsResponse: ...

@router.patch("/items/{id}")
async def update_item(id: int, body: ItemUpdate) -> Item: ...

# mcp_server/tools.py
async def get_items(opts: {
    "category": str | None,
    "time_range": str,               # "24h", "7d", "30d"
    "source": str | None,
    "search": str | None,
    "limit": int
}) -> list[Item]: ...

async def classify_item(opts: {
    "item_id": int,
    "category": str,
    "score": float | None,
    "tags": list[str] | None
}) -> Item: ...

async def get_youtube_transcript(opts: {"url": str}) -> YTExtract: ...

async def get_daily_digest(opts: {"date": str | None}) -> DailyDigest: ...
```

## Inter-module Dependencies

```
quarry/app.jsx         -> quarry/api.js -> api (GET /items, /sources, /health)
collector/main.py      -> collectors/* (collect)
collector/main.py      -> core/database.py (store_items)
collector/main.py      -> core/scheduler.py (APScheduler)
collectors/youtube.py  -> scripts/yt_extract.py (subprocess)
collectors/rss.py      -> RSSHub (HTTP)
api/main.py            -> core/database.py (read-only)
api/routes/items.py    -> core/database.py (get_items, update_item)
api/routes/sources.py  -> core/database.py (get_sources, add_source, remove_source)
api/routes/health.py   -> core/database.py (get_health)
mcp_server/server.py   -> api (internal HTTP to localhost:8000)
telegram_bot/bot.py    -> api (GET /items for digest)
telegram_bot/bot.py    -> Telegram Bot API
Claude routines        -> mcp_server (external, MCP stdio)
```

## Build Order

1. **Phase 0 — Legacy salvage** — copy collectors + core from `D:\KnowledgeBase\kb-clean\projects\knowledgeforge\`, adapt imports. No original logic written.
2. **Phase 1 — Schema** — adapt `core/database.py` to `items` schema. Create `core/models.py` with dataclasses. Test: `python -c "from core.database import DB; DB('data/kf.db')"`.
3. **Phase 2a — Config** — `config/sources.yaml`, `config/categories.yaml`, `core/config.py` loads them.
4. **Phase 2b — Collectors running** — each collector tested standalone. APScheduler wired in `collector/main.py`.
5. **Phase 3a — FastAPI** — API routes, SQLite reads. Test with curl.
6. **Phase 3b — Quarry wired** — `quarry/api.js`, patch `app.jsx`. Test in browser.
7. **Phase 4 — Telegram** — bot posts to group topics. Test with manual trigger.
8. **Phase 5 — MCP** — register tools, connect Claude Desktop. Test `get_items`.
9. **Phase 6 — Docker** — full compose, volumes, restart persistence. Test `docker-compose up -d`.

## Implementation Phases

**Durable decisions:**
- Language: Python 3.12+
- DB: SQLite + FTS5 (single file, zero ops)
- Table name: `items` (not `documents` — matches Quarry quest/category system)
- Collectors dir: `collectors/` (plural)
- No LLM API keys anywhere in this system
- Intelligence: external Claude via MCP only
- Scheduling: APScheduler (in-process)
- Feed aggregation: RSSHub Docker container (don't build RSS fetching from scratch — legacy already works)
- Frontend: Quarry React (existing, wire to real API)

---

### Phase 0: Legacy Salvage

**User stories:** #1

**What to build:** Port working code from `D:\KnowledgeBase\kb-clean\projects\knowledgeforge\` into KnowledgeBase_Final. Zero new logic. Adapt imports and paths only.

Files to port (in order):
1. `core/retry.py` — copy as-is
2. `core/models.py` — copy, rename `Document` → `Item`, align field names to PRD v1 schema
3. `core/database.py` — copy, swap `documents` → `items` table, add `yt_extracts` + `collection_runs` tables
4. `core/config.py` — copy, adapt to load from `config/sources.yaml`
5. `core/scheduler.py` — copy as-is
6. `collectors/base.py` — copy as-is
7. `collectors/rss.py` — copy, fix imports
8. `collectors/hackernews.py` — copy, fix imports
9. `collectors/reddit.py` — copy, fix imports
10. `collectors/github.py` — copy, fix imports
11. `collectors/youtube.py` — copy, fix imports
12. `collectors/telegram_channel.py` — copy, fix imports
13. `requirements.txt` — merge legacy deps + add fastapi, uvicorn, python-telegram-bot, mcp

**Acceptance criteria:**
- [ ] `python -c "from collectors.rss import RSSCollector; print('ok')"` exits 0
- [ ] `python -c "from core.database import DB; DB('data/kf.db'); print('ok')"` exits 0, creates `data/kf.db`
- [ ] No absolute paths (`D:\KnowledgeBase\...`) remaining in ported files

---

### Phase 1: SQLite Foundation

**User stories:** #2, #11, #28

**What to build:** Finalize `core/database.py` with v1 schema. `core/models.py` with `Item`, `Source`, `YTExtract`, `CollectionRun` dataclasses. Verify FTS5 triggers work.

**Acceptance criteria:**
- [ ] `data/kf.db` created with all 4 tables + FTS5 virtual table on first run
- [ ] Insert item, query by URL — dedup works (second insert skipped)
- [ ] FTS query on `items_fts` returns matching rows
- [ ] `collection_runs` row written after each collect cycle

---

### Phase 2: Collectors + Config

**User stories:** #3, #4, #5, #6, #7, #8, #9, #10, #11, #27, #28, #29

**What to build:** `config/sources.yaml` with all default sources. `config/categories.yaml` with 7 categories. All collectors runnable. APScheduler wiring in `collector/main.py`. PowerShell manual trigger.

Default sources (`config/sources.yaml`):
```yaml
rsshub:
  # Bug Bounty
  - id: reddit-netsec
    route: /reddit/subreddit/netsec
    category: BugBounty
  - id: reddit-bugbounty
    route: /reddit/subreddit/bugbounty
    category: BugBounty
  # Attacking AI
  - id: reddit-localllama
    route: /reddit/subreddit/LocalLLaMA
    category: Attacking-AI
  - id: reddit-ml
    route: /reddit/subreddit/MachineLearning
    category: Attacking-AI
  # AI Money
  - id: reddit-sideproject
    route: /reddit/subreddit/SideProject
    category: AI-Money
  - id: reddit-saas
    route: /reddit/subreddit/SaaS
    category: SaaS-Niches
  # Crypto
  - id: reddit-defi
    route: /reddit/subreddit/defi
    category: Crypto-DeFi-Alpha
  # Tools Drops
  - id: hackernews-best
    route: /hackernews/best
    category: General
  - id: hackernews-show
    route: /hackernews/show
    category: Tools-Drops
  - id: github-trending
    route: /github/trending/daily
    category: Tools-Drops

rss:
  # Bug Bounty
  - id: portswigger-research
    url: https://portswigger.net/research/rss
    category: BugBounty
  - id: trailofbits-blog
    url: https://blog.trailofbits.com/feed
    category: BugBounty
  # Tools / General
  - id: pointer-io
    url: https://www.pointer.io/archives/feed
    category: Tools-Drops
  - id: barely-human-news
    url: https://news.barelyhuman.xyz/top/1
    category: General
  - id: serializer-io
    url: https://serializer.io/feed
    category: Tools-Drops
  # AI Money
  - id: indiehackers
    url: https://www.indiehackers.com/feed
    category: AI-Money

youtube_channels:
  - id: yt-liveoverflow
    channel: "@LiveOverflow"
    category: BugBounty
  - id: yt-johnhammond
    channel: "@JohnHammond"
    category: BugBounty
  - id: yt-ippsec
    channel: "@IppSec"
    category: BugBounty
  - id: yt-networkchuck
    channel: "@NetworkChuck"
    category: Tools-Drops
  - id: yt-theprimeagen
    channel: "@ThePrimeagen"
    category: Tools-Drops
```

**Acceptance criteria:**
- [ ] `python collector/main.py --once` runs all collectors, exits 0
- [ ] SQLite has 20+ items after first run
- [ ] Duplicate run adds 0 items (dedup works)
- [ ] `scripts/manual_collect.ps1` triggers collection and prints count
- [ ] APScheduler runs every 15 minutes when `collector/main.py` runs daemonized
- [ ] Failed source logs error to `collection_runs.errors`, doesn't abort other sources

---

### Phase 3: FastAPI + Quarry Wiring

**User stories:** #12, #13, #14, #15, #16, #17, #30

**What to build:** FastAPI at port 8000. Quarry `app.jsx` patched to fetch from API. Filtering, FTS, pagination.

**Acceptance criteria:**
- [ ] `curl http://localhost:8000/health` returns 200 with last run timestamp
- [ ] `curl http://localhost:8000/items` returns 50 items JSON
- [ ] `curl "http://localhost:8000/items?category=BugBounty"` returns only BugBounty items
- [ ] `curl "http://localhost:8000/items?q=xss"` returns FTS matches
- [ ] `curl "http://localhost:8000/items?since=2026-05-01"` returns date-filtered items
- [ ] Quarry opens in browser and shows real items (not seed data)
- [ ] Category filter in Quarry filters correctly
- [ ] AddSourceForm posts to POST /sources, new source appears in GET /sources

---

### Phase 4: Telegram Delivery

**User stories:** #18, #19, #20, #21

**What to build:** Bot posts daily digests to Telegram group with Topics. One topic per category + status topic. Uses Telegram Premium for full-length messages. Pyrogram collector for ingesting followed channels.

Setup required (user must do manually):
1. Create bot via @BotFather → get `TELEGRAM_BOT_TOKEN`
2. Create private group → enable Topics → get `TELEGRAM_CHAT_ID`
3. Create 8 topics: BugBounty, AI-Money, SaaS-Niches, Crypto-DeFi-Alpha, Attacking-AI, Tools-Drops, General, Status → get topic IDs
4. Add bot to group as admin
5. Store in `.env`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_TOPIC_IDS` (JSON map)

**Acceptance criteria:**
- [ ] Daily digest triggers at 8 AM, posts to correct topic per category
- [ ] Each message has title + URL + 1-line summary
- [ ] Status topic posts: items added today per source, any errors, timestamp
- [ ] Empty categories → topic skipped (no empty posts)
- [ ] Telegram API failure → 3 retries, then log error, don't crash
- [ ] Messages not truncated (Telegram Premium = no 4096 char limit issue)

---

### Phase 5: MCP Server

**User stories:** #22, #23, #24

**What to build:** MCP stdio server. Tools: `get_items`, `get_categories`, `classify_item`, `get_youtube_transcript`, `get_daily_digest`. Connects to API internally.

**Acceptance criteria:**
- [ ] Claude Desktop connects to MCP server
- [ ] `get_items(time_range="24h")` returns only last 24h items
- [ ] `classify_item(item_id=1, category="BugBounty")` writes to SQLite, verifiable with GET /items/1
- [ ] `get_youtube_transcript(url="...")` triggers on-demand extraction and returns result
- [ ] `get_daily_digest()` returns today's items grouped by category

---

### Phase 6: Docker Full Stack

**User stories:** #25, #26

**What to build:** `docker-compose.yml` with services: rsshub, collector, api, mcp_server, telegram_bot. Volume mounts: `./data`, `./cookies`. Health checks.

**Acceptance criteria:**
- [ ] `docker-compose up -d` starts all 5 services without errors
- [ ] `docker-compose ps` shows all services healthy
- [ ] `curl http://localhost:8000/health` returns 200 after stack start
- [ ] `curl http://localhost:1200/healthz` returns 200 (RSSHub running)
- [ ] Restart (`docker-compose restart`) — data survives, `data/kf.db` intact
- [ ] `cookies/cookies.txt` mounted and accessible to collector container

---

## Acceptance Criteria

### Collectors
- Given RSS source → new posts appear in `items` table within 15 min of publication
- Given duplicate URL → `store_items` skips it, no error, count not incremented
- Given source network error → error logged in `collection_runs.errors`, other sources still run
- Given manual trigger → all enabled sources fetched immediately

### YouTube Extraction
- Given public URL → transcript + description + top 3 comments extracted
- Given URL with no transcript → falls back to English subtitles
- Given no subtitles either → description + comments stored, warning logged
- Given private URL + valid `cookies/cookies.txt` → extracted same as public
- Output file: `data/yt_extracts/{title} [{video_id}].md`

### API
- Given no filters → 50 most recent items returned, newest first
- Given `?category=X` → only items where `category = X` returned
- Given `?q=ssrf` → FTS matches across title + body + summary
- Given `?since=2026-05-01&until=2026-05-23` → only items in range
- Given invalid category → 400 with valid category list in body
- Given `POST /sources` with valid body → source persisted, returned with 201

### Telegram
- Given items exist today → digest posted to correct topic
- Given no items for category → that topic skipped
- Given Telegram API down → 3 retries, failure logged, other topics still sent

### MCP
- Given Claude Desktop connected → all 5 tools listed
- Given `classify_item` called → `items.category` updated in SQLite
- Given `get_items` with `time_range="24h"` → only items collected in last 24h

## Auth Rules

- No multi-user auth. Single-operator personal tool.
- API: No auth in V1 (localhost only). Add API key header if ever exposed externally.
- Telegram Bot: Token in `.env` — never committed.
- yt-dlp cookies: `cookies/cookies.txt` in mounted volume — never committed.
- MCP: No auth (local stdio transport only).
- `.env`, `cookies/`, `data/` all in `.gitignore`.

## Out of Scope

- Multi-user support
- LLM classification inside the system (external via MCP only)
- Vector embeddings / semantic search (v2+ via Claude routines)
- Twitter/X scraping (use RSSHub Twitter routes instead)
- Discord source
- Email newsletters (Telegram only for delivery)
- Public web UI (local only)
- Mobile app
- Paid SaaS features
- Claude-obsidian / LLM wiki integration
- Memos integration
- Automated opportunity scoring inside the system
- Substack full-text (RSSHub Substack route is optional add-on)

## Further Notes

### Source of Truth for Legacy Code

Legacy project at `D:\KnowledgeBase\kb-clean\projects\knowledgeforge\` has working implementations for all collectors. Before writing any collector from scratch, read the legacy version first.

Highest-value salvage items:
- `collectors/hackernews.py` — HN API pagination + scoring, fully working
- `collectors/reddit.py` — Reddit RSS + PRAW hybrid, handles rate limits
- `collectors/rss.py` — feedparser + per-feed timestamp cursors (avoids re-fetching old items)
- `core/database.py` — SQLite + FTS5 triggers, migration support
- `core/scheduler.py` — APScheduler + retry logic

### Telegram Premium Features

Telegram Premium users can:
- Use bots with no message length cap (send full digest, not truncated)
- Upload files up to 4 GB (for large transcript files)
- Get 4 linked accounts (forward content from followed channels)

For channel ingestion: use Pyrogram (MTProto client) not Bot API. Requires user API credentials from my.telegram.org (api_id, api_hash), not just a bot token.

### Suggested Additional Sources (from bookmark analysis)

All map to existing categories, zero custom collector needed:

| URL | Category | Type |
|-----|----------|------|
| `https://marginalia-search.com/search?query=X&profile=blogosphere` | General | API (no key) |
| `https://www.buzzing.cc/lite/` | General | RSS |
| `https://hackertab.dev/` | Tools-Drops | RSS |
| `https://hntoplinks.com/month` | General | Scrape |
| `https://gerikson.com/hnlo/` | General | Scrape |
| `https://blog.zsec.uk/` | BugBounty | RSS |
| `https://xdavidhu.me/` | BugBounty | RSS (security researcher) |
| `https://securing.dev/` | BugBounty | RSS |
| `https://blog.doyensec.com/` | BugBounty | RSS |

### Cost

- RSSHub: free (self-hosted Docker)
- yt-dlp: free
- SQLite: free
- Telegram Bot API: free
- Pyrogram (Telegram): free (uses own account)
- VPS optional: $4-6/mo Hetzner CX22 (or run local)
- **Total: $0-6/month**
