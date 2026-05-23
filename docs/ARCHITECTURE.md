# KnowledgeForge v2 — Architecture

## What is this?

Personal intelligence pipeline. Collects content from 11+ sources, stores in SQLite, displays in Quarry dashboard, delivers via Telegram, exposes via MCP for Claude routines.

**NOT a SaaS.** Personal tool for spotting money opportunities across bug bounty, AI, SaaS, crypto, and tooling.

---

## High-Level Data Flow

```
Sources (RSSHub, yt-dlp, Telegram)
       │
       ▼
┌─────────────────────────────────────────────────────┐
│  Collectors (one per source type)                    │
│  RSS · YouTube · Reddit · HN · GitHub · Telegram    │
│  Each: fetch → normalize → [Item]                   │
└───────────────────┬─────────────────────────────────┘
                    │ list[Item]
                    ▼
┌─────────────────────────────────────────────────────┐
│  SQLite + FTS5 (core/database.py)                    │
│  • Dedup by URL                                      │
│  • Full-text search across title + body              │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
   Quarry UI     Telegram     MCP Server
   (React)       Bot           (for Claude)
```

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Collection | RSSHub (Docker) + yt-dlp | Existing tools, no API keys needed |
| Storage | SQLite + FTS5 | Zero infra, portable, fast for personal scale |
| API | FastAPI | Async, auto-docs, typed |
| Frontend | Quarry (React) | Already built, wired to API |
| Delivery | Telegram Bot | Group with Topics per category |
| Intelligence | MCP → Claude Routines | No LLM API keys in system |
| Scheduling | APScheduler | In-process cron |
| Containers | Docker Compose | Single `docker-compose up` |

---

## Key Decisions

1. **No LLM API keys in the system** — Intelligence applied externally via MCP by Claude routines
2. **Compose existing tools** — RSSHub, yt-dlp, python-telegram-bot. Don't reinvent.
3. **SQLite not Postgres** — Single user, portable, zero ops
4. **Skills as portable tools** — `.devin/skills/` for reusable extraction/processing tools
5. **Categories are classification labels, not folders** — Items tagged with category, not stored separately

---

## Newsletter Categories

| # | Name | Signal |
|---|------|--------|
| 1 | BugBounty | Vulns, techniques, CTFs, writeups |
| 2 | AI-Money | Dev money-making with AI |
| 3 | SaaS-Niches | Value + monetize ideas |
| 4 | Crypto/DeFi-Alpha | Exploits, MEV, yield |
| 5 | Attacking-AI | Adversarial ML, LLM security |
| 6 | Tools-Drops | New tools, trending repos |
| 7 | General | Uncategorizable high-signal |

---

## Directory Structure

```
KnowledgeBase_Final/
├── .devin/skills/       # Portable agent skills
│   └── yt-extract/      # YouTube extraction skill
├── collectors/          # Source-specific fetchers
├── core/                # Database, models, config, scheduler
├── scripts/             # Standalone CLI tools
├── quarry/              # React dashboard (frontend)
├── docs/                # Architecture, roadmap docs
├── plans/               # PRDs and implementation plans
├── config/              # Source lists, category definitions
├── cookies/             # Auth cookies (gitignored)
├── data/                # SQLite DB + extracted content (gitignored)
├── docker-compose.yml   # Full stack orchestration
└── AGENTS.md            # Project rules for AI agents
```
