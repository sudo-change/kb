# KnowledgeForge — Current State & Build Plan

_Last updated: 2026-05-23_

---

## What This System Is

Personal intelligence pipeline. Zero AI inside the system — data collection + display only. Claude pulls from MCP later to classify + generate newsletters. Goal: catch opportunities (bug bounty, SaaS niches, AI money) before they expire.

No SaaS. No multi-user. One person, one server, $0-6/mo.

---

## Current State Assessment

### What's BUILT (KnowledgeBase_Final)

| Component | Status | Notes |
|-----------|--------|-------|
| `plans/knowledge-forge-v1.md` | ✅ Done | Detailed PRD, 6 phases, full schema |
| `plans/legacy-salvage.md` | ✅ Done | Plan to pull from D:\KnowledgeBase |
| `docs/ARCHITECTURE.md` | ✅ Done | Stack decisions locked |
| `AGENTS.md` | ✅ Done | Agent rules |
| `quarry/` (React dashboard) | ✅ Exists | Runs on SEED DATA only — not wired to API |
| `scripts/yt_extract.py` | ✅ Working | Tested with OuyR77HhL-E |
| `.devin/skills/yt-extract/` | ✅ Done | Portable skill |
| `data/yt_extracts/` | ✅ Has 1 file | Q&A Session Apr 30 2026 extract |
| SQLite schema | ❌ Not created | Defined in PRD but no db file |
| Python collectors | ❌ None | Not ported yet |
| FastAPI | ❌ None | Phase 3 |
| Telegram bot | ❌ None | Phase 4 |
| MCP server | ❌ None | Phase 5 |
| Docker Compose | ❌ None | Phase 6 |

### What's in Legacy (D:\KnowledgeBase\kb-clean) — REUSABLE

**Gold tier — copy and adapt:**

| Legacy path | Maps to Final | Verdict |
|-------------|---------------|---------|
| `knowledgeforge/collectors/rss.py` | `collectors/rss.py` | refactor-port |
| `knowledgeforge/collectors/hackernews.py` | `collectors/hackernews.py` | refactor-port |
| `knowledgeforge/collectors/reddit.py` | `collectors/reddit.py` | refactor-port |
| `knowledgeforge/collectors/github_collector.py` | `collectors/github.py` | refactor-port |
| `knowledgeforge/collectors/youtube.py` | `collectors/youtube.py` | refactor-port |
| `knowledgeforge/collectors/telegram.py` | `collectors/telegram.py` | refactor-port |
| `knowledgeforge/collectors/base.py` | `collectors/base.py` | copy-as-is |
| `knowledgeforge/core/database.py` | `core/database.py` | refactor-port |
| `knowledgeforge/core/models.py` | `core/models.py` | refactor-port |
| `knowledgeforge/core/scheduler.py` | `core/scheduler.py` | refactor-port |
| `knowledgeforge/core/config.py` | `core/config.py` | refactor-port |
| `knowledgeforge/core/retry.py` | `core/retry.py` | copy-as-is |
| `knowledgeforge/core/validation.py` | `core/validation.py` | reference-only |
| `knowledgeforge/docker-compose.yml` | `docker-compose.yml` | refactor-port |
| `knowledgeforge/Dockerfile` | `Dockerfile` | refactor-port |
| `knowledgeforge/requirements.txt` | `requirements.txt` | refactor-port |

**Discard:**
- `data/` (182 GB SQLite + extracts) — never touch
- `__pycache__/`, `*.session`, `*.tmp.*`, `cookies/` — noise
- `web/` (Flask+HTMX) — replaced by Quarry+FastAPI
- `kb-clean/data/knowledge-notes/00-07` — AI crew playlist notes, reference only

**Note:** `kb-clean/projects/quarry/` likely identical to `KnowledgeBase_Final/quarry/` — diff before touching.

---

## Source Map (what to collect)

Based on user's actual consumption patterns from bookmark list:

### Bug Bounty / Security
- `r/netsec`, `r/bugbounty` (Reddit via RSSHub)
- PortSwigger Research RSS: `https://portswigger.net/research/rss`
- Trail of Bits: `https://blog.trailofbits.com/feed`
- PayloadsAllTheThings (GitHub releases)
- HackerOne Hacktivity (RSS or scrape)
- GitHub trending (security-tagged)

### AI / Attacking AI
- arXiv CS.CR + CS.AI (RSSHub: `/arxiv/category/cs.AI`)
- GitHub trending ML/AI
- `r/MachineLearning`, `r/LocalLLaMA`
- Anthropic blog RSS

### SaaS / AI Money
- IndieHackers (`https://www.indiehackers.com/feed`)
- ProductHunt (RSSHub: `/producthunt/today`)
- `r/SideProject`, `r/SaaS`

### Crypto / DeFi Alpha
- Rekt.news RSS
- `r/defi`, `r/ethdev`

### Tools / Dev Drops
- GitHub trending (daily)
- HN Best + HN Show (RSSHub: `/hackernews/best`, `/hackernews/show`)
- `r/commandline`, `r/programming`

### General
- HN Best (catch-all for what doesn't fit above)
- Lobsters RSS
- Marginalia search (manual trigger only)

---

## Build Order (revised from PRD)

### Phase 0 — Legacy Salvage (½ day, do FIRST)
Port working collector + DB code from `D:\KnowledgeBase\kb-clean\projects\knowledgeforge\` into `KnowledgeBase_Final`. Don't rewrite what already works.

Steps:
1. Copy `collectors/base.py`, `collectors/rss.py`, `collectors/hackernews.py`, `collectors/reddit.py`, `collectors/github_collector.py`, `collectors/youtube.py`
2. Copy `core/database.py`, `core/models.py`, `core/config.py`, `core/scheduler.py`, `core/retry.py`
3. Adapt imports + paths to Final structure
4. Reconcile schema: legacy uses `documents` table, PRD v1 uses `items` table — pick one (recommend `items` per PRD to match Quarry categories)
5. Create `requirements.txt` from legacy + adapt

### Phase 1 — SQLite Foundation (done after salvage)
- `core/database.py` working with v1 `items` schema + FTS5
- `core/models.py` with v1 field names
- Standalone test: `python -c "from core.database import DB; db = DB('data/kf.db'); print('ok')"`

### Phase 2 — Collectors + Config (1-2 days)
- `config/sources.yaml` with default sources (see Source Map above)
- `config/categories.yaml` with 7 categories
- All collectors ported and runnable
- `collector/main.py` with APScheduler (15-min interval)
- `scripts/manual_collect.sh` (PowerShell: `manual_collect.ps1`)
- Test: run collector, check SQLite has rows

### Phase 3 — FastAPI + Quarry (1 day)
- `api/main.py` with routes: `/items`, `/sources`, `/health`
- Quarry `quarry/api.js` + wire `app.jsx` to fetch from `http://localhost:8000`
- Test: open Quarry in browser, real data renders

### Phase 4 — Telegram (1 day)
- `telegram_bot/bot.py` — group with Topics (one per category + status)
- Daily digest cron (8 AM)
- Telegram Premium: longer messages, no 4096-char truncation

### Phase 5 — MCP Server (1 day)
- `mcp_server/server.py` — tools: `get_items`, `classify_item`, `get_daily_digest`, `get_youtube_transcript`
- Wire to Claude Desktop for testing
- `classify_item` writes category back to SQLite so Claude routines can categorize

### Phase 6 — Docker Compose (½ day)
- Full stack: RSSHub + Collector + API + MCP + Telegram Bot
- Volume mounts: `./data`, `./cookies`
- `docker-compose up -d` = everything live

---

## Newsletter Categories (7)

| # | Name | Signal | Sources |
|---|------|--------|---------|
| 1 | BugBounty | Vulns, CVEs, techniques, CTFs | r/netsec, r/bugbounty, PortSwigger, HackerOne |
| 2 | AI-Money | Dev money-making, AI tool launches | r/SideProject, IndieHackers, PH |
| 3 | SaaS-Niches | Market gaps, monetize ideas | r/SaaS, IndieHackers, Lobsters |
| 4 | Crypto/DeFi-Alpha | MEV, exploits, yield | r/defi, Rekt.news |
| 5 | Attacking-AI | Adversarial ML, LLM security, jailbreaks | arXiv, r/LocalLLaMA, sec researchers |
| 6 | Tools-Drops | New tools, repos, CLIs | GitHub trending, HN Show, r/commandline |
| 7 | General | High-signal uncategorizable | HN Best, Lobsters, catch-all |

---

## Telegram Premium Leverage

Telegram Premium unlocks:
- **4 linked accounts** — can forward channels you follow into a group
- **Longer messages** — 4096 → no limit for premium bots  
- **Faster uploads** — file-based extracts, PDFs
- **Stories** — skip

Strategy:
1. Create private Telegram group with Topics (one per category)
2. Bot posts daily digests per topic
3. Subscribe to Telegram security/AI channels (e.g. @tg_cve, @offensive_security, @dailydoseofds)
4. Phase 2+: Telegram collector reads those channels' posts and ingests into SQLite

Known Telegram collector exists at: `D:\KnowledgeBase\kb-clean\projects\knowledgeforge\collectors\telegram.py`

---

## Key Constraints (locked)

- No LLM API keys in the system. Intelligence = external Claude via MCP.
- No rewrite what legacy has working. Port, adapt, move on.
- Quarry = display only. No AI inside.
- SQLite only. No Postgres.
- Phase 0 (salvage) before Phase 1. Don't reinvent existing working code.

---

## Open Questions (to resolve before starting Phase 0)

1. Schema: `items` table (PRD v1 names) vs `documents` (legacy names)? Recommend `items` since Quarry's quest/category system maps to it.
2. `collectors/` at root vs `collector/` (PRD says singular)? Recommend `collectors/` (plural, matches legacy).
3. Telegram group already exists? Need group ID + topic IDs before Phase 4.
4. `cookies.txt` — does user have Netscape-format cookies from browser export? Needed for private YT.
5. Docker installed? Needed for RSSHub container.

---

## Ideas to Go Deeper on Existing Sites

Sites from bookmark list worth building dedicated collectors for:

| Site | What it has | How to ingest |
|------|-------------|---------------|
| `marginalia-search.com` | Independent web search, blogosphere filter | API (free, no key needed) |
| `miniflux.app` | Self-hosted RSS reader | Already does RSS aggregation — consider using as RSSHub alternative |
| `hackertab.dev` | Curated dev content | Has RSS or JSON feed |
| `buzzing.cc` | HN/Reddit/Twitter translated Chinese tech | RSS feed |
| `gerikson.com/hnlo/` | HN top links archive | RSS scrape |
| `hntoplinks.com` | HN top by month | Scrape |
| `news.barelyhuman.xyz` | Curated dev news | RSS |
| `serializer.io` | Dev newsletter aggregator | RSS |
| `pointer.io` | Engineering leadership reads | RSS: `https://www.pointer.io/archives/feed` |

All of these map to **Tools-Drops** or **General** category and can be added as RSS sources without custom collectors.

---

## Future Ideas (V2+)

- **Telegram channel ingestion**: Pyrogram-based collector reads subscribed channels → ingest to SQLite
- **alphaxiv.org integration**: arXiv paper discovery with community discussion layer — RSS feed exists
- **ralph-loop**: Self-referential validation loop that checks KB coverage gaps weekly
- **AI playlist pipeline**: YouTube playlist URL → extract all transcripts → summarize → single KB entry
- **MCP + Claude Code hook**: Live trigger when new bug bounty / Attacking-AI item lands, Claude Code skill auto-processes
- **Miniflux as frontend alternative**: Self-hosted RSS reader that could replace Quarry for feed consumption
- **Semantic search**: Vector embeddings via Claude API, stored in SQLite-vec (Phase 3+ via MCP routines)
