# Legacy Salvage Manifest

Source: `D:\KnowledgeBase\kb-clean\projects\knowledgeforge\`

| Legacy File | Destination | Status | Notes |
|-------------|-------------|--------|-------|
| `collectors/base.py` | `collectors/base.py` | Ported | Imports fixed |
| `collectors/rss.py` | `collectors/rss.py` | Ported | feedparser + timestamp cursors |
| `collectors/hackernews.py` | `collectors/hackernews.py` | Ported | HN API pagination + scoring |
| `collectors/reddit.py` | `collectors/reddit.py` | Ported | Reddit RSS + PRAW hybrid |
| `collectors/github_collector.py` | `collectors/github.py` | Ported | Renamed; imports fixed |
| `collectors/youtube.py` | `collectors/youtube.py` | Ported | yt-dlp subprocess wiring |
| `collectors/telegram.py` | `collectors/telegram_channel.py` | Ported | Renamed; Pyrogram MTProto |
| `core/database.py` | `core/database.py` | Adapted | `documents` → `items`; added `yt_extracts`, `collection_runs` |
| `core/models.py` | `core/models.py` | Adapted | `Document` → `Item`; field names aligned to PRD v1 |
| `core/config.py` | `core/config.py` | Ported | YAML loader adapted |
| `core/scheduler.py` | `core/scheduler.py` | Ported | APScheduler wiring unchanged |
| `core/retry.py` | `core/retry.py` | Copied | No changes |
| `Dockerfile` | `Dockerfile` (root) | Referenced | Single root image covers all services |
| `docker-compose.yml` | `docker-compose.yml` | Replaced | Full 5-service compose written from scratch |
| `config.yaml` | `config/sources.yaml` + `config/categories.yaml` | Split | Single config split into sources + categories |
| `requirements.txt` | `requirements.txt` | Merged | Legacy deps + fastapi, uvicorn, python-telegram-bot, mcp |
| `scripts/` | `scripts/` | Partial | `yt_extract.py` ported; kg-query/similar/tag not needed |
| `web/` | `quarry/` | Reference only | Quarry approach used instead of legacy web UI |
| `specgen/` | — | Skipped | Not needed in v2 |
| `core/embedder.py` | — | Skipped | v2+ (semantic search out of scope) |
| `core/graph.py` | — | Skipped | v2+ (graph features out of scope) |
| `core/validation.py` | — | Skipped | Pydantic used instead |
