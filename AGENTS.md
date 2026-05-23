# Project Rules — KnowledgeForge v2

## Build & Run

```bash
# YouTube extraction (standalone, no Docker needed)
python scripts/yt_extract.py <url> --cookies cookies/cookies.txt

# Full stack (when Docker services are built)
docker-compose up -d
```

## Verification

- YT extraction: Check output .md file has Title, Channel, Duration, Transcript sections
- Collectors: `python run.py stats` shows item counts per source
- API: `curl http://localhost:8000/api/health`

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
