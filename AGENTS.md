# Project Rules — KnowledgeForge v2

## Build & Run

```bash
# YouTube extraction (standalone, no Docker needed)
python scripts/yt_extract.py <url> --cookies cookies/cookies.txt

# Full stack (when Docker services are built)
docker-compose up -d
```

## Verification

- Dependencies: `python scripts/yt_extract.py --check-deps` (exits 0 if yt-dlp + node on PATH)
- YT extraction: Output `.md` at `data/yt_extracts/<title> [<id>].md` with Title/Channel/Duration/Transcript sections
- RSSHub healthz: `curl -s http://localhost:1200/healthz` returns 200
- RSSHub route check after `docker compose up rsshub`:
  ```bash
  for r in /reddit/subreddit/netsec /hackernews/best /github/trending/daily; do
    curl -s -o /dev/null -w "%{http_code} $r\n" "http://localhost:1200$r"
  done
  ```
- API (Phase 3+): `curl http://localhost:8000/health`

## Conventions

- **Collectors** inherit from `collectors/base.py` BaseCollector
- **No LLM API keys** in this system — classification via external MCP
- **Skills** in `.devin/skills/<name>/SKILL.md` — portable, agent-invocable
- **Config** in `config/` as YAML — sources, categories, schedules
- **Data** never committed — SQLite + extracts in `data/` (gitignored)
- **Cookies** never committed — `cookies/` (gitignored)

## yt-dlp requires

- `--js-runtimes node` flag (Node.js must be on PATH)
- `cookies/cookies.txt` for private video access

## Key paths

- PRD: `plans/knowledge-forge-v1.md`
- Architecture: `docs/ARCHITECTURE.md`
- YT Skill: `.devin/skills/yt-extract/SKILL.md`
- Frontend: `quarry/`

## Legacy Reference

Working legacy implementations live at `D:\KnowledgeBase\kb-clean\projects\knowledgeforge\`.

Before writing any collector from scratch, read the legacy version. See `docs/legacy-manifest.md` for full salvage audit.

High-value legacy files:
- `collectors/hackernews.py` — HN API pagination + scoring
- `collectors/reddit.py` — Reddit RSS + PRAW, rate-limit handling
- `collectors/rss.py` — feedparser + per-feed timestamp cursors
- `core/database.py` — SQLite + FTS5 triggers, migration support
- `core/scheduler.py` — APScheduler + retry logic
