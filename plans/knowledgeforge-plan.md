# Plan: KnowledgeForge Build — Phase 0 → 6

Source PRD: plans/knowledgeforge-build.md

---

## Architectural Decisions

- **Schema:** `items` table (not `documents`). Four tables: `items`, `sources`, `yt_extracts`, `collection_runs`. FTS5 virtual table on `items`. Single SQLite file at `data/kf.db`.
- **Collector pattern:** All collectors inherit `collectors/base.py:BaseCollector`. Each returns `list[Item]`. `core/database.py:DB.store_items()` handles dedup by URL.
- **API:** FastAPI on port 8000. No auth in V1 (localhost only). Routes: `/items`, `/sources`, `/health`.
- **No LLM inside system.** Claude connects externally via MCP. `classify_item` MCP tool writes category back to SQLite.
- **Scheduling:** APScheduler in-process. 15-min interval in `collector/main.py`. Separate daily cron in `telegram_bot/scheduler.py` for digests.
- **Phase 0 is a port, not a rewrite.** All legacy code lives at `D:\KnowledgeBase\kb-clean\projects\knowledgeforge\`. Read before writing anything.
- **Frontend:** Quarry React app. `quarry/api.js` wraps all fetch calls. `quarry/data.js` becomes demo/fallback only.
- **Containers:** Docker Compose. Services: `rsshub`, `collector`, `api`, `mcp_server`, `telegram_bot`. Volumes: `./data`, `./cookies`.
- **Secrets:** `.env` for `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_TOPIC_IDS`. Never committed.

---

## Phases

### Phase 0: Legacy Salvage

User stories: #1

What to build: Port 13 working files from `D:\KnowledgeBase\kb-clean\projects\knowledgeforge\` into KnowledgeBase_Final. No new logic. Adapt imports and absolute paths only. After this phase, all collector and core DB code is importable. This is the fastest unblock — skips weeks of rewriting collectors that already handle rate limits, pagination, dedup, and retries.

Port order (dependency-safe):
1. `core/retry.py` — no deps, copy as-is
2. `core/models.py` — rename `Document` → `Item`, align fields to PRD v1 schema
3. `core/database.py` — adapt to `items` schema, keep FTS5 triggers
4. `core/config.py` — load from `config/sources.yaml` instead of hardcoded paths
5. `core/scheduler.py` — copy as-is
6. `collectors/base.py` — copy as-is
7. `collectors/rss.py` — fix imports
8. `collectors/hackernews.py` — fix imports
9. `collectors/reddit.py` — fix imports
10. `collectors/github.py` — fix imports
11. `collectors/youtube.py` — fix imports
12. `collectors/telegram_channel.py` — fix imports
13. `requirements.txt` — merge legacy deps + add `fastapi uvicorn python-telegram-bot mcp`

Acceptance criteria:
- [ ] `python -c "from collectors.rss import RSSCollector; print('ok')"` exits 0
- [ ] `python -c "from collectors.hackernews import HackerNewsCollector; print('ok')"` exits 0
- [ ] `python -c "from core.database import DB; DB('data/kf.db'); print('ok')"` exits 0, creates `data/kf.db`
- [ ] No string `D:\\KnowledgeBase` remaining in any ported file (grep clean)
- [ ] `pip install -r requirements.txt` succeeds in `.venv`

---

### Phase 1: SQLite Foundation

User stories: #2, #11, #28

What to build: Finalize `core/database.py` with the full v1 schema (4 tables + FTS5 + triggers). Finalize `core/models.py` with `Item`, `Source`, `YTExtract`, `CollectionRun` dataclasses. After this phase, you can insert items, query them, and FTS works. Everything else in the pipeline writes to or reads from this layer.

Acceptance criteria:
- [ ] `data/kf.db` creates all 4 tables on first `DB()` instantiation
- [ ] `db.store_items([item])` inserts row; second call with same URL skips, returns count 0
- [ ] `db.get_items({"q": "xss"})` returns FTS matches across title + body
- [ ] `collection_runs` row written with `items_added` count
- [ ] `db.get_health()` returns `last_run`, `items_today`, `errors` fields

---

### Phase 2: Collectors Running

User stories: #3, #4, #5, #6, #7, #8, #9, #10, #27, #29

What to build: `config/sources.yaml` with 20 default sources (Reddit, HN, GitHub trending, PortSwigger, Trail of Bits, IndieHackers, Pointer, BarelyHuman, Serializer, 5 YouTube channels). `config/categories.yaml` with 7 categories. `collector/main.py` with APScheduler. `scripts/manual_collect.ps1`. After this phase, the pipeline collects real data automatically every 15 minutes and stores it in SQLite. YT on-demand extraction also works.

Acceptance criteria:
- [ ] `python collector/main.py --once` exits 0, SQLite has 20+ items
- [ ] Second run adds 0 duplicate items
- [ ] Failed source (network off) logs error to `collection_runs.errors`, other sources still run
- [ ] `scripts/manual_collect.ps1` triggers collection and prints `Added: N items`
- [ ] `python scripts/yt_extract.py "https://www.youtube.com/watch?v=OuyR77HhL-E"` extracts to `data/yt_extracts/`
- [ ] APScheduler fires every 15 min when `collector/main.py` runs daemonized (check logs)

---

### Phase 3: API + Quarry Wired

User stories: #12, #13, #14, #15, #16, #17, #30

What to build: FastAPI at port 8000 with routes `/items` (filter, FTS, paginate), `/sources` (CRUD), `/health`. `quarry/api.js` wrapping all fetch calls. Patch `quarry/app.jsx` to call API instead of importing `data.js`. After this phase, open Quarry in browser and see real collected data. Category filter works. AddSourceForm persists new sources.

Acceptance criteria:
- [ ] `uvicorn api.main:app` starts without errors
- [ ] `curl http://localhost:8000/health` returns 200 with `last_run` timestamp
- [ ] `curl "http://localhost:8000/items?category=BugBounty"` returns only BugBounty items
- [ ] `curl "http://localhost:8000/items?q=xss"` returns FTS matches
- [ ] `curl "http://localhost:8000/items?since=2026-05-01"` filters by date
- [ ] Open `quarry/Quarry.html` in browser — real items render (not seed data)
- [ ] Category filter in Quarry UI works
- [ ] AddSourceForm → POST /sources → new source visible in GET /sources

---

### Phase 4: Telegram Delivery

User stories: #18, #19, #20, #21

What to build: `telegram_bot/bot.py` that posts daily digests to a private Telegram group with Topics. One topic per category + status topic. `telegram_bot/formatter.py` for message formatting. Daily cron at 8 AM. Pyrogram-based collector for ingesting Telegram channels you follow. After this phase, every morning a digest lands in your Telegram group, categorized. Telegram Premium = full-length messages, no truncation.

Pre-requisites (user must do manually before testing):
- Create bot via @BotFather → `.env: TELEGRAM_BOT_TOKEN`
- Create private group → enable Topics → `.env: TELEGRAM_CHAT_ID`
- Create 8 topics → `.env: TELEGRAM_TOPIC_IDS={"BugBounty":123,...,"Status":456}`
- Add bot as group admin

Acceptance criteria:
- [ ] `python telegram_bot/bot.py --test` posts to each topic and status topic
- [ ] Status topic shows: items added today per source, any errors, timestamp
- [ ] Category with 0 items → topic skipped (no empty posts)
- [ ] Messages not truncated (verify 2000+ char digest sends fully)
- [ ] Telegram API failure → 3 retries logged, other topics still send
- [ ] Pyrogram collector reads 1 configured channel, stores posts in SQLite as `source_type=telegram`

---

### Phase 5: MCP Server

User stories: #22, #23, #24

What to build: MCP stdio server in `mcp_server/server.py` registering 5 tools: `get_items`, `get_categories`, `classify_item`, `get_youtube_transcript`, `get_daily_digest`. Calls API internally at localhost:8000. After this phase, Claude Desktop connects and Claude routines can query the KB, classify items by category, and trigger YT extraction — all without touching SQLite directly.

Acceptance criteria:
- [ ] Claude Desktop connects to MCP server (add to `claude_desktop_config.json`)
- [ ] `get_items(time_range="24h")` returns only last 24h items
- [ ] `get_items(category="BugBounty")` returns only BugBounty items
- [ ] `classify_item(item_id=1, category="BugBounty")` updates `items.category` in SQLite — verify with `GET /items/1`
- [ ] `get_youtube_transcript(url="...")` triggers extraction, returns transcript text
- [ ] `get_daily_digest()` returns today's items grouped by category

---

### Phase 6: Docker Full Stack

User stories: #25, #26

What to build: `docker-compose.yml` with 5 services: `rsshub`, `collector`, `api`, `mcp_server`, `telegram_bot`. Volume mounts `./data` and `./cookies`. Health checks on each service. `collector/Dockerfile` and `api/Dockerfile`. After this phase, a single `docker-compose up -d` starts the entire pipeline. Restarts don't lose data. Cookies for private YT work inside containers.

Acceptance criteria:
- [ ] `docker-compose up -d` starts all 5 services, no container exits
- [ ] `docker-compose ps` shows all services healthy
- [ ] `curl http://localhost:8000/health` returns 200
- [ ] `curl http://localhost:1200/healthz` returns 200 (RSSHub)
- [ ] `docker-compose restart` → `data/kf.db` still has all rows
- [ ] `cookies/cookies.txt` readable from inside collector container
- [ ] `docker-compose logs collector` shows collection running every 15 min
