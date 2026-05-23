# PRD: KnowledgeForge — Personal Intelligence Pipeline

## Problem Statement

You left your job, have 4-month runway, need money flow in 30 days. You're drowning in signal across Twitter, Reddit, YouTube, Substack, GitHub — but can't track what matters across bug bounty, AI, SaaS, crypto, and tooling drops. Opportunities have short lifetimes. You need a system that:

1. Collects everything relevant from your sources automatically
2. Displays it in a scannable, scored dashboard (Quarry)
3. Delivers categorized digests to Telegram
4. Exposes data via MCP so Claude routines can process, classify, and generate actionable intelligence

You don't want to build from scratch. You want to compose existing tools (RSSHub, yt-dlp, Telegram Bot API) into a pipeline that runs 24/7 and surfaces money-making opportunities before they expire.

## Solution

A Docker Compose stack that:

- **RSSHub** (self-hosted) aggregates feeds from Twitter/X, Reddit, YouTube, Substack, HN, GitHub, blogs
- **yt-dlp** extracts transcripts, descriptions, and top comments from YouTube videos (including private via cookies)
- **SQLite** stores all collected items with metadata, timestamps, source info
- **Quarry** (evolved React dashboard) displays items ranked by quest relevance, filterable by category
- **Telegram Bot** delivers daily digests to a group with Topics (one per category + status)
- **MCP Server** exposes the data lake so Claude/Windsurf/Cursor/custom agents can pull items by date, category, or semantic query
- **Claude Routines** (external, not built here) connect via MCP to classify, summarize, and generate newsletters

The system is a DATA LAKE first. Intelligence is applied externally by Claude routines via MCP.

## User Stories

1. As a researcher, I want RSSHub to auto-fetch new posts from my configured Twitter accounts every 15 minutes, so that I never miss time-sensitive opportunities.
2. As a researcher, I want Reddit posts from specific subreddits (netsec, bugbounty, machinelearning) collected automatically, so I can scan them in one place.
3. As a researcher, I want YouTube videos from specific channels collected with their transcripts extracted automatically, so I can search video content as text.
4. As a researcher, I want yt-dlp to extract transcript + description + top 3 comments from any YouTube URL I paste, so I can ingest video knowledge quickly.
5. As a researcher, I want the system to fallback to English subtitles when transcript extraction fails, so no video goes unprocessed.
6. As a researcher, I want extracted YouTube content saved as files named by video title, so I can find them easily.
7. As a researcher, I want all collected items stored in SQLite with source, timestamp, URL, title, body, and raw metadata, so nothing is lost.
8. As a researcher, I want Quarry dashboard to show real data from the SQLite database instead of seed data, so the dashboard reflects actual intelligence.
9. As a researcher, I want items in Quarry filterable by the 7 categories (BugBounty, AI-Money, SaaS-Niches, Crypto/DeFi-Alpha, Attacking-AI, Tools-Drops, General), so I can focus on one vertical at a time.
10. As a researcher, I want items scored by relevance to my quests (reusing quarry's quest system), so high-signal items surface first.
11. As a researcher, I want a Telegram bot to post daily digests to my group, organized by Topics (one per category), so I get intel on my phone.
12. As a researcher, I want a "status" Topic in Telegram that shows what was collected today (counts per source, any errors), so I know the system is healthy.
13. As a researcher, I want an MCP server that exposes endpoints: get items by date range, get items by category, get items by source, full-text search, so Claude routines can pull data.
14. As a researcher, I want Claude routines (external) to connect via MCP, classify uncategorized items into the 7 newsletters, and post results back, so classification happens without API keys in my system.
15. As a researcher, I want to add new RSS/social/video sources via Quarry's existing AddSourceForm UI, so I can expand coverage without editing config files.
16. As a researcher, I want the Docker stack to persist all data via volume mounts, so restarts don't lose collected intelligence.
17. As a researcher, I want the system to handle duplicate URLs gracefully (skip if already collected), so the database stays clean.
18. As a researcher, I want a simple CLI command to manually trigger collection from all sources, so I can force-refresh when needed.
19. As a researcher, I want Substack newsletters I follow collected as full-text items, so I can search newsletter content.
20. As a researcher, I want GitHub trending repos and specific repo releases tracked, so I catch tool drops early.
21. As a researcher, I want the MCP server to support time-windowed queries ("items from last 24h", "items from this week"), so routines get fresh data only.
22. As a researcher, I want Telegram premium features leveraged (larger file uploads, longer messages), so digests aren't truncated.
23. As a researcher, I want the YouTube extractor to work with my cookies.txt for accessing private/unlisted videos, so nothing is gated.
24. As a researcher, I want a health-check endpoint that shows last collection time per source and any failures, so I can diagnose issues quickly.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                Docker Compose Stack                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌───────────┐ │
│  │  RSSHub  │───▶│  Collector   │───▶│  SQLite   │ │
│  │(feeds)   │    │  (Python)    │    │  (data)   │ │
│  └──────────┘    └──────────────┘    └─────┬─────┘ │
│                         │                   │       │
│  ┌──────────┐          │              ┌────┴────┐  │
│  │  yt-dlp  │──────────┘              │   API   │  │
│  │(youtube) │                          │(FastAPI)│  │
│  └──────────┘                          └────┬────┘  │
│                                             │       │
│  ┌──────────┐    ┌──────────────┐          │       │
│  │ Telegram │◀───│  Scheduler   │          │       │
│  │  Bot     │    │  (cron)      │          │       │
│  └──────────┘    └──────────────┘          │       │
│                                             │       │
│  ┌──────────┐                              │       │
│  │   MCP    │◀─────────────────────────────┘       │
│  │  Server  │                                      │
│  └──────────┘                                      │
│                                                      │
├─────────────────────────────────────────────────────┤
│  Volume: ./data → /app/data (SQLite + YT files)     │
│  Volume: ./cookies → /app/cookies (yt-dlp auth)     │
└─────────────────────────────────────────────────────┘

External:
┌───────────┐     MCP      ┌──────────────┐
│  Claude   │◀────────────▶│  MCP Server  │
│  Routines │              │  (in stack)  │
└───────────┘              └──────────────┘

┌───────────┐
│  Quarry   │◀──── API ────▶ FastAPI
│  (React)  │
└───────────┘
```

## Modules

```
CREATE  docker-compose.yml                    (orchestrates all services)
CREATE  collector/Dockerfile                  (Python collector service)
CREATE  collector/requirements.txt            (dependencies)
CREATE  collector/main.py                     (entry point, scheduler)
CREATE  collector/sources/rsshub.py           (RSSHub feed fetcher)
CREATE  collector/sources/youtube.py          (yt-dlp wrapper)
CREATE  collector/sources/telegram_ingest.py  (future: Telegram channel forwarding)
CREATE  collector/db.py                       (SQLite schema + queries)
CREATE  collector/config.py                   (source definitions, categories)
CREATE  api/Dockerfile                        (FastAPI service)
CREATE  api/main.py                           (REST API for Quarry + MCP)
CREATE  api/routes/items.py                   (CRUD + search endpoints)
CREATE  api/routes/sources.py                 (source management)
CREATE  api/routes/health.py                  (health check)
CREATE  mcp_server/server.py                  (MCP protocol server)
CREATE  mcp_server/tools.py                   (MCP tool definitions)
CREATE  telegram_bot/bot.py                   (Telegram digest delivery)
CREATE  telegram_bot/formatter.py             (message formatting)
CREATE  scripts/yt_extract.py                 (standalone YT extraction tool)
CREATE  scripts/manual_collect.sh             (force-collect CLI)
CREATE  data/.gitkeep                         (SQLite DB lives here)
CREATE  cookies/.gitkeep                      (cookies.txt goes here)
CREATE  config/sources.yaml                   (default source list)
CREATE  config/categories.yaml                (7 newsletter categories)
MODIFY  quarry/app.jsx                        (wire to real API instead of seed data)
MODIFY  quarry/data.js                        (becomes fallback/demo mode only)
CREATE  quarry/api.js                         (API client for Quarry)
```

## Schema Changes

### SQLite Schema (new database)

```sql
CREATE TABLE items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    url         TEXT UNIQUE NOT NULL,
    title       TEXT NOT NULL,
    body        TEXT,
    summary     TEXT,
    source_id   TEXT NOT NULL,
    source_type TEXT NOT NULL,  -- 'rsshub', 'youtube', 'manual'
    category    TEXT,           -- NULL until classified
    quest_id    TEXT,           -- maps to quarry quest
    score       REAL DEFAULT 0,
    tags        TEXT,           -- JSON array
    metadata    TEXT,           -- JSON blob (comments, points, etc)
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME,
    is_read     BOOLEAN DEFAULT 0
);

CREATE INDEX idx_items_category ON items(category);
CREATE INDEX idx_items_source ON items(source_id);
CREATE INDEX idx_items_collected ON items(collected_at DESC);
CREATE INDEX idx_items_url ON items(url);

-- FTS5 virtual table for full-text search across title + body + summary + tags
CREATE VIRTUAL TABLE items_fts USING fts5(
    title, body, summary, tags,
    content='items',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Triggers to keep FTS5 in sync with items table
CREATE TRIGGER items_ai AFTER INSERT ON items BEGIN
    INSERT INTO items_fts(rowid, title, body, summary, tags)
    VALUES (new.id, new.title, new.body, new.summary, new.tags);
END;

CREATE TRIGGER items_ad AFTER DELETE ON items BEGIN
    INSERT INTO items_fts(items_fts, rowid, title, body, summary, tags)
    VALUES ('delete', old.id, old.title, old.body, old.summary, old.tags);
END;

CREATE TRIGGER items_au AFTER UPDATE ON items BEGIN
    INSERT INTO items_fts(items_fts, rowid, title, body, summary, tags)
    VALUES ('delete', old.id, old.title, old.body, old.summary, old.tags);
    INSERT INTO items_fts(rowid, title, body, summary, tags)
    VALUES (new.id, new.title, new.body, new.summary, new.tags);
END;

CREATE TABLE sources (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,  -- 'rsshub', 'youtube_channel', 'manual'
    config      TEXT NOT NULL,  -- JSON (rsshub route, channel ID, etc)
    glyph       TEXT,
    category    TEXT,           -- default category for items from this source
    enabled     BOOLEAN DEFAULT 1,
    last_fetch  DATETIME,
    error       TEXT
);

CREATE TABLE yt_extracts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id    TEXT UNIQUE NOT NULL,
    title       TEXT NOT NULL,
    description TEXT,
    transcript  TEXT,
    subtitles   TEXT,
    comments    TEXT,           -- JSON array of top 3
    duration    INTEGER,
    channel     TEXT,
    file_path   TEXT,           -- path to saved file
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    item_id     INTEGER REFERENCES items(id)
);

CREATE TABLE collection_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    items_added INTEGER DEFAULT 0,
    errors      TEXT           -- JSON array of error messages
);
```

## Service Interfaces

### Collector Service

```python
# collector/sources/rsshub.py
async def fetch_feed(source: Source) -> list[RawItem]:
    """Fetch items from an RSSHub feed URL. Returns parsed items."""

async def collect_all_feeds(sources: list[Source]) -> CollectionResult:
    """Fetch all enabled RSS sources, deduplicate, store new items."""

# collector/sources/youtube.py
async def extract_video(opts: {
    url: str,
    cookies_path: str | None,
    output_dir: str
}) -> YTExtract:
    """Extract transcript, description, top 3 comments from a YouTube video.
    Falls back to English subtitles if transcript unavailable.
    Saves to file named by video title."""

async def monitor_channels(channels: list[Source]) -> list[RawItem]:
    """Check configured YT channels for new videos, extract each."""

# collector/db.py
def store_items(items: list[RawItem]) -> int:
    """Insert new items (skip duplicates by URL). Returns count added."""

def get_items(opts: {
    category: str | None,
    source_id: str | None,
    since: datetime | None,
    until: datetime | None,
    limit: int,
    offset: int
}) -> list[Item]:
    """Query items with filters."""
```

### API Service

```python
# api/routes/items.py
@router.get("/items")
async def list_items(
    category: str | None,
    source: str | None,
    since: str | None,
    until: str | None,
    q: str | None,          # full-text search
    limit: int = 50,
    offset: int = 0
) -> ItemsResponse

@router.get("/items/{id}")
async def get_item(id: int) -> Item

@router.patch("/items/{id}")
async def update_item(id: int, body: ItemUpdate) -> Item  # classify, tag, score

# api/routes/sources.py
@router.get("/sources")
async def list_sources() -> list[Source]

@router.post("/sources")
async def add_source(body: SourceCreate) -> Source

@router.delete("/sources/{id}")
async def remove_source(id: str) -> None

# api/routes/health.py
@router.get("/health")
async def health() -> HealthResponse  # last run, items today, errors
```

### MCP Server

```python
# mcp_server/tools.py
@tool("get_items")
async def get_items(opts: {
    category: str | None,
    time_range: str,        # "24h", "7d", "30d", or ISO range
    source: str | None,
    search: str | None,
    limit: int
}) -> list[Item]:
    """Get collected items filtered by category, time, source, or search query."""

@tool("get_categories")
async def get_categories() -> list[Category]:
    """List all newsletter categories with item counts."""

@tool("classify_item")
async def classify_item(opts: {
    item_id: int,
    category: str,
    score: float | None,
    tags: list[str] | None
}) -> Item:
    """Classify an item into a category (called by Claude routines)."""

@tool("get_youtube_transcript")
async def get_youtube_transcript(opts: {
    url: str
}) -> YTExtract:
    """Extract and return YouTube video transcript + metadata."""

@tool("get_daily_digest")
async def get_daily_digest(opts: {
    date: str | None        # defaults to today
}) -> DailyDigest:
    """Get all items collected today, grouped by category."""
```

### Telegram Bot

```python
# telegram_bot/bot.py
async def send_digest(opts: {
    chat_id: str,
    topic_id: int,
    items: list[Item],
    category: str
}) -> None:
    """Post formatted digest to a Telegram topic."""

async def send_status(opts: {
    chat_id: str,
    topic_id: int,
    run: CollectionRun
}) -> None:
    """Post collection status update."""
```

## Inter-module Dependencies

```
Quarry (React)      -> API (GET /items, /sources, /health)
Collector           -> RSSHub (HTTP fetch)
Collector           -> yt-dlp (subprocess)
Collector           -> SQLite (direct, via db.py)
API                 -> SQLite (read, via db.py)
MCP Server          -> API (internal HTTP calls)
Telegram Bot        -> API (GET /items for digest)
Telegram Bot        -> Telegram API (send messages)
Claude Routines     -> MCP Server (external, via MCP protocol)
scripts/yt_extract  -> yt-dlp (standalone, no API needed)
```

## Build Order

1. **SQLite schema + db.py** — No deps. Foundation for everything.
2. **config/sources.yaml + config.py** — Source definitions. No deps.
3. **collector/sources/youtube.py + scripts/yt_extract.py** — yt-dlp wrapper. Test with sample video immediately.
4. **collector/sources/rsshub.py** — RSSHub feed fetcher. Needs RSSHub running.
5. **docker-compose.yml (RSSHub only)** — Get RSSHub container running.
6. **collector/main.py** — Scheduler that runs collection. Depends on 1-4.
7. **api/main.py + routes** — FastAPI serving data. Depends on 1.
8. **quarry/api.js + app.jsx modifications** — Wire dashboard to real API. Depends on 7.
9. **mcp_server/** — MCP protocol server. Depends on 7.
10. **telegram_bot/** — Digest delivery. Depends on 7.
11. **Full docker-compose.yml** — All services orchestrated. Depends on all above.

## Implementation Phases

### Durable Decisions

- **Language:** Python 3.12+ (FastAPI, yt-dlp, MCP SDK all Python)
- **Database:** SQLite (single file, no server, portable, good enough for personal use)
- **Container runtime:** Docker Compose
- **Feed aggregation:** RSSHub (self-hosted Docker container)
- **YouTube extraction:** yt-dlp (subprocess with cookies support)
- **API framework:** FastAPI (async, auto-docs, fast)
- **MCP SDK:** `mcp` Python package (official Anthropic MCP SDK)
- **Telegram:** python-telegram-bot library
- **Frontend:** Existing Quarry React app, wired to API
- **Scheduling:** APScheduler (in-process cron)
- **No LLM API keys in the system** — intelligence applied externally via MCP

### Phase 1: YouTube Extractor + SQLite Foundation (Days 1-2)

User stories: #3, #4, #5, #6, #7, #23

What to build: Standalone YouTube extraction tool that works immediately. SQLite schema. Store results. Test with https://www.youtube.com/watch?v=OuyR77HhL-E

Acceptance criteria:
- [ ] `python scripts/yt_extract.py <url>` extracts transcript, description, top 3 comments
- [ ] Falls back to English subtitles when no transcript available
- [ ] Output file named by video title (sanitized)
- [ ] Data stored in SQLite yt_extracts table
- [ ] Works with cookies.txt for authenticated access
- [ ] Test video successfully extracted and readable

### Phase 2: RSSHub + Collector (Days 3-4)

User stories: #1, #2, #7, #17, #19, #20

What to build: RSSHub Docker container running. Python collector fetches feeds, parses, stores in SQLite. Cron schedule (every 15 min). Default sources configured.

Acceptance criteria:
- [ ] RSSHub container accessible at localhost:1200
- [ ] Collector fetches from 5+ default sources (HN, netsec, bugbounty subs, etc.)
- [ ] Items stored in SQLite with deduplication (URL-based)
- [ ] Scheduler runs every 15 minutes
- [ ] collection_runs table tracks each run
- [ ] `scripts/manual_collect.sh` triggers immediate collection

### Phase 3: API + Quarry Wiring (Days 5-6)

User stories: #8, #9, #10, #15, #24

What to build: FastAPI serving items from SQLite. Quarry dashboard reads from API instead of seed data. Filtering by category, source, time.

Acceptance criteria:
- [ ] GET /items returns real collected data with pagination
- [ ] GET /items?category=BugBounty filters correctly
- [ ] GET /items?q=ssrf full-text search works
- [ ] GET /health shows last collection time + errors
- [ ] Quarry renders real items from API
- [ ] AddSourceForm in Quarry creates sources via POST /sources
- [ ] Quest filtering maps to categories

### Phase 4: Telegram Delivery (Days 7-8)

User stories: #11, #12, #22

What to build: Telegram bot that posts daily digests to a group with Topics. One topic per category. Status topic shows collection health.

Acceptance criteria:
- [ ] Bot posts to 7 category topics + 1 status topic
- [ ] Daily digest triggered at configured time (e.g., 8 AM)
- [ ] Each category topic gets relevant items formatted cleanly
- [ ] Status topic shows: items collected, sources checked, errors
- [ ] Telegram Premium features used (longer messages)
- [ ] Manual trigger available via bot command

### Phase 5: MCP Server (Days 9-10)

User stories: #13, #14, #21

What to build: MCP server exposing KB data. Any MCP-compatible tool (Claude, Windsurf, Cursor) can query items, classify them, get transcripts.

Acceptance criteria:
- [ ] MCP server registers tools: get_items, get_categories, classify_item, get_youtube_transcript, get_daily_digest
- [ ] Claude Desktop can connect and query items
- [ ] Time-windowed queries work ("last 24h", "this week")
- [ ] classify_item writes back to SQLite (Claude routine can categorize)
- [ ] get_youtube_transcript triggers on-demand extraction

### Phase 6: Docker Compose Full Stack (Day 11)

User stories: #16, #18

What to build: Single `docker-compose up` brings up everything. Volume mounts persist data. Production-ready.

Acceptance criteria:
- [ ] `docker-compose up -d` starts: RSSHub, Collector, API, MCP Server, Telegram Bot
- [ ] Data persists across container restarts (volume: ./data)
- [ ] Cookies mounted correctly (volume: ./cookies)
- [ ] All services healthy after restart
- [ ] README with setup instructions

## Acceptance Criteria

### YouTube Extraction
- Given a public video URL → extracts transcript + description + top 3 comments
- Given a private video URL + valid cookies.txt → extracts same
- Given a video with no transcript → falls back to English subtitles
- Given a video with no subtitles at all → stores description + comments only, logs warning
- Output file named: `{sanitized_title}.md`

### Feed Collection
- Given RSSHub is running → collector fetches all enabled feeds on schedule
- Given a duplicate URL → item is skipped, no error
- Given a source that errors → error logged, other sources still processed
- Given manual trigger → all sources fetched immediately

### API
- Given no filters → returns most recent 50 items
- Given category filter → returns only items in that category
- Given date range → returns items within range
- Given search query → full-text search across title + body
- Given invalid category → returns 400 with valid categories list

### Telegram Delivery
- Given items exist for today → digest posted to correct topics
- Given no items for a category → that topic skipped (no empty posts)
- Given collection errors → status topic shows error details
- Given Telegram API failure → retries 3x, logs failure

### MCP Server
- Given Claude connects → tools listed and callable
- Given get_items with time_range="24h" → only last 24h items returned
- Given classify_item called → item's category updated in SQLite
- Given get_youtube_transcript with new URL → extracts on-demand and returns

## Auth Rules

- No multi-user auth. Single-user personal tool.
- API: No auth in V1 (local network only). Add API key if exposed externally.
- Telegram Bot: Token stored in .env, not committed.
- yt-dlp cookies: cookies.txt in mounted volume, not committed.
- MCP: No auth (local stdio transport).

## Out of Scope

- Multi-user support
- LLM classification within the system (done externally via MCP)
- Memos integration
- claude-obsidian / LLM Wiki
- Public-facing web UI (local only)
- Mobile app
- Email newsletters
- Paid SaaS features
- Vector embeddings / semantic search (Phase 2+ via Claude routines)
- Twitter scraping (use RSSHub's Twitter routes instead)
- Custom ML models

## Further Notes

### Newsletter Categories

| # | Category | Signal | Example Sources |
|---|----------|--------|-----------------|
| 1 | BugBounty | Vulns, techniques, CTFs, writeups | r/netsec, r/bugbounty, HackerOne, PortSwigger |
| 2 | AI-Money | Dev money-making with AI, money glitches | r/SideProject, IndieHackers, AI tool launches |
| 3 | SaaS-Niches | Value + monetize ideas, market gaps | ProductHunt, r/SaaS, Indie Hackers |
| 4 | Crypto/DeFi-Alpha | Exploits, MEV, yield, market signals | r/defi, CT accounts, Rekt.news |
| 5 | Attacking-AI | Adversarial ML, LLM jailbreaks, AI security | arXiv, AI security researchers |
| 6 | Tools-Drops | New tools, trending repos, developer tooling | GitHub trending, HN Show, r/commandline |
| 7 | General | Uncategorizable high-signal items | Catch-all |

### Default Sources (Day 1)

```yaml
rsshub:
  - reddit/netsec
  - reddit/bugbounty  
  - reddit/machinelearning
  - reddit/SideProject
  - hackernews/best
  - hackernews/show
  - github/trending/daily
youtube_channels:
  - "@LiveOverflow"
  - "@JohnHammond"
  - "@IppSec"
  - "@NetworkChuck"
  - "@ThePrimeagen"
rss:
  - https://portswigger.net/research/rss
  - https://blog.trailofbits.com/feed
```

### Key Constraints

- **No API keys in the system**: LLM intelligence applied externally via MCP by Claude routines
- **Compose existing tools**: RSSHub, yt-dlp, python-telegram-bot. Don't reinvent.
- **Money flow in 30 days**: The tool helps SPOT opportunities. Execution is on you.
- **4-month runway**: Keep infra costs near zero. Local Docker or cheapest VPS.
- **Data persistence**: Volume mounts. Never lose collected data.

### Cost Estimate

- RSSHub: Free (self-hosted)
- yt-dlp: Free
- SQLite: Free
- Telegram Bot: Free
- VPS (optional): $4-6/mo (Hetzner CX22)
- Claude routines: Within existing Claude subscription usage
- **Total: $0-6/month**

### Future Expansion (V2+)

- Memos as optional data browser
- Vector embeddings for semantic search
- Automated opportunity scoring (via Claude routines)
- Telegram bot commands for search/query
- Additional sources: Telegram channel forwarding, Discord servers
- Public newsletter for audience building
- Monetization: Sell curated intel to specific niches
