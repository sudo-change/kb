---
name: yt-extract
description: Extract transcript, description, and top 3 comments (sorted by likes) from YouTube videos using yt-dlp. Outputs markdown named "Title [video_id].md". Supports private/unlisted/shorts/live videos via cookies. Use when user says "extract youtube", "get transcript", "yt extract", pastes a YouTube URL, or wants to ingest video content.
---

# yt-extract

Extract transcript, description, and top 3 comments (by likes) from a YouTube video using yt-dlp.

## On invocation

1. Validate deps: `python scripts/yt_extract.py --check-deps`
2. Run extraction: `python scripts/yt_extract.py <url>`
   - Cookies auto-loaded from `cookies/cookies.txt` if present
3. Verify output file at `data/yt_extracts/<title> [<video_id>].md`
4. Report: title, channel, duration, transcript length, comment count

## When to use

- User says "extract youtube", "get transcript", "yt extract"
- User pastes a YouTube URL (watch, youtu.be, shorts, live, embed)
- User wants to ingest a YouTube video into the knowledge base

## Requirements

- `yt-dlp` >= 2026.03.17 (for `--js-runtimes` flag)
- `node` on PATH (JS runtime for YouTube challenge solving)
- Optional: `cookies/cookies.txt` for private/unlisted/age-restricted videos

## Usage

```bash
# Validate deps only
python scripts/yt_extract.py --check-deps

# Extract a video (auto-loads cookies/cookies.txt if it exists)
python scripts/yt_extract.py "https://youtube.com/watch?v=VIDEO_ID"

# Custom cookies path
python scripts/yt_extract.py "<url>" --cookies path/to/cookies.txt

# Custom output dir + timeout
python scripts/yt_extract.py "<url>" --output-dir data/podcasts --timeout 1200
```

## What it extracts

1. **Transcript** — Manual subtitles preferred (en, en-US, en-GB), falls back to auto-captions (en-orig). Timestamps stripped, consecutive duplicate lines deduplicated.
2. **Description** — Full video description.
3. **Top 3 Comments** — Fetches up to 100 top-level comments from yt-dlp, sorted locally by `like_count` desc, top 3 picked. Replies excluded.
4. **Metadata** — Title, channel, duration, publish date, video ID, URL.

## Output

Markdown file at `data/yt_extracts/{sanitized_title} [{video_id}].md`:

```markdown
# Video Title

**Channel:** Channel Name
**URL:** https://youtube.com/watch?v=VIDEO_ID
**Duration:** 1:23:45
**Published:** 20260101
**Video ID:** VIDEO_ID

## Description
...

## Top Comments
**1. Author** (1234 likes)
> comment text

## Transcript
...
```

Filename always includes `[video_id]` to prevent collisions on shared titles.

## Robustness

- Per-run unique temp dir (`pid + uuid`) — safe for concurrent extractions of same video
- Atomic markdown write (tmp file + `os.replace`) — partial files never visible
- Cleanup only after successful write — no data loss on crash
- 3 retries with exponential backoff on transient yt-dlp failures
- No retry on permanent errors: private, unavailable, age-restricted, members-only, premiere
- Hard subprocess timeout (default 600s)
- Handles all YouTube URL forms: `watch?v=`, `youtu.be/`, `/shorts/`, `/live/`, `/embed/`, `/clip/`, raw 11-char ID
- Windows-safe filenames: strips reserved chars, control chars, trailing dots; renames CON/PRN/AUX/etc.

## Cookie auth for private videos

Place browser cookies at `cookies/cookies.txt` (auto-detected). Export with:

```bash
yt-dlp --cookies-from-browser chrome --cookies-output cookies/cookies.txt
```

Or use a browser extension like "Get cookies.txt LOCALLY".

## Verified working

- "Q&A Session Apr 30 2026" (Critical Thinking Bug Bounty Podcast, 1:16:42) — 71KB markdown, 68846 char transcript

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | Success — markdown written |
| 1    | Extraction failed (no info.json, no output) |
| 2    | Missing dependencies, or `--cookies` path invalid |
| 124  | yt-dlp subprocess timed out |
