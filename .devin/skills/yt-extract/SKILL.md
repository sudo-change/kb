---
name: yt-extract
description: Extract transcript, description, and top 3 comments from YouTube videos using yt-dlp. Outputs clean markdown named by video title. Supports private videos via cookies. Use when user says "extract youtube", "get transcript", "yt extract", pastes a YouTube URL, or wants to ingest video content.
---

# yt-extract

Extract transcript, description, and top comments from YouTube videos using yt-dlp.

## On invocation

1. Run `python scripts/yt_extract.py <url> --cookies cookies/cookies.txt`
2. Verify output file exists in `data/yt_extracts/`
3. Report: title, channel, duration, transcript length

## When to use

- User says "extract youtube", "get transcript", "yt extract"
- User pastes a YouTube URL and wants content extracted
- User wants to ingest a YouTube video into the knowledge base

## Requirements

- `yt-dlp` installed and on PATH
- `node` (Node.js) installed (required as JS runtime for YouTube challenges)
- Optional: `cookies/cookies.txt` for private/unlisted video access

## Usage

```bash
python scripts/yt_extract.py <youtube_url> [--cookies cookies/cookies.txt] [--output-dir data/yt_extracts]
```

## What it extracts

1. **Transcript** — Auto-generated captions (en-orig or en), cleaned of timestamps
2. **Description** — Full video description
3. **Top 3 Comments** — Most relevant comments (if available)
4. **Metadata** — Title, channel, duration, publish date, URL

## Output

Markdown file named by video title in `data/yt_extracts/`:

```
# Video Title

**Channel:** Channel Name
**URL:** https://youtube.com/watch?v=...
**Duration:** 1:23:45
**Published:** 20260101

## Description
...

## Top Comments
...

## Transcript
...
```

## Fallback behavior

1. Try `en-orig` (original language auto-captions)
2. Fall back to `en` (English auto-captions)
3. If no subtitles at all → saves description + comments only, logs warning

## Cookie auth for private videos

Place browser cookies at `cookies/cookies.txt`. Export using browser extension or:
```bash
yt-dlp --cookies-from-browser chrome --cookies cookies/cookies.txt
```

## Verified working

- Tested: "Q&A Session Apr 30 2026" (Critical Thinking Bug Bounty Podcast)
- 1890 lines, 71KB markdown, full 1:16:42 transcript extracted
