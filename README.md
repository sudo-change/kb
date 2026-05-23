# KnowledgeForge v2

Personal intelligence pipeline. Collects from Twitter, Reddit, YouTube, HN, GitHub, Substack. Displays in Quarry dashboard. Delivers via Telegram. Exposes via MCP for Claude routines.

## Quick Start

```bash
# YouTube extraction (works standalone, no Docker)
python scripts/yt_extract.py "https://youtube.com/watch?v=VIDEO_ID"

# Start RSSHub (feed aggregation)
docker-compose up -d rsshub

# Full stack (when all services built)
docker-compose up -d
```

## Structure

```
.devin/skills/      # Portable agent skills (yt-extract, etc.)
collectors/         # Source-specific fetchers (RSS, YT, Reddit, etc.)
core/               # Database, models, config, scheduler
config/             # sources.yaml, categories.yaml
scripts/            # Standalone CLI tools
quarry/             # React dashboard (frontend)
docs/               # Architecture docs
plans/              # PRDs and implementation plans
cookies/            # Auth cookies (gitignored)
data/               # SQLite DB + extracts (gitignored)
```

## Skills (`.devin/skills/`)

Reusable, agent-invocable tools. Copy the skill folder to any project.

| Skill | What it does |
|-------|--------------|
| `yt-extract` | Extract transcript + metadata from YouTube videos |

## Newsletter Categories

1. **BugBounty** — Vulns, techniques, CTFs
2. **AI-Money** — Dev money-making with AI
3. **SaaS-Niches** — Market gaps, monetization ideas
4. **Crypto/DeFi-Alpha** — Exploits, MEV, yield
5. **Attacking-AI** — Adversarial ML, LLM security
6. **Tools-Drops** — New tools, trending repos
7. **General** — High-signal uncategorizable

## Requirements

- Python 3.10+
- Docker + Docker Compose
- yt-dlp + Node.js (for YouTube JS challenges)
- Telegram Bot token (for delivery)

## Docs

- [PRD](plans/knowledge-forge-v1.md)
- [Architecture](docs/ARCHITECTURE.md)
- [AGENTS.md](AGENTS.md) — AI agent project rules
