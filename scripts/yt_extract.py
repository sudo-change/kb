# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
YouTube Extractor — Extract transcript, description, top 3 comments from a video.
Falls back to English subtitles if no transcript available.
Output: Markdown file named by video title.

Usage:
    python scripts/yt_extract.py <youtube_url> [--cookies path/to/cookies.txt] [--output-dir data/yt_extracts]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


REQUIRED_BINS = ["yt-dlp", "node"]
MAX_RETRIES = 3
RETRY_BACKOFF_SEC = 2


def check_dependencies() -> None:
    """Verify required binaries exist on PATH before doing any work."""
    missing = []
    for binary in REQUIRED_BINS:
        if shutil.which(binary) is None:
            missing.append(binary)
    if missing:
        print(f"[!] Missing required binaries: {', '.join(missing)}", file=sys.stderr)
        print(f"[!] yt-dlp: pip install yt-dlp", file=sys.stderr)
        print(f"[!] node: https://nodejs.org/ (needed for YouTube JS challenges)", file=sys.stderr)
        sys.exit(2)


def extract_video_id(url: str) -> str | None:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def sanitize_filename(title: str) -> str:
    """Remove/replace chars invalid in filenames."""
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.rstrip('.')  # Windows: trailing dots invalid
    return title[:200] or "untitled"


def parse_srt(srt_path: str) -> str:
    """Parse SRT file into plain text (no timestamps)."""
    if not os.path.exists(srt_path):
        return ""
    lines: list[str] = []
    with open(srt_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^\d+$', line):
                continue
            if re.match(r'^\d{2}:\d{2}:\d{2}', line):
                continue
            # Strip HTML tags from auto-subs
            clean = re.sub(r'<[^>]+>', '', line).strip()
            if not clean:
                continue
            # Dedup consecutive identical lines (auto-sub rolling captions)
            if not lines or lines[-1] != clean:
                lines.append(clean)
    return '\n'.join(lines)


def run_ytdlp(cmd: list[str]) -> tuple[int, str, str]:
    """Run yt-dlp with retries on transient failures."""
    last_err = ""
    for attempt in range(1, MAX_RETRIES + 1):
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            return 0, result.stdout, result.stderr
        last_err = result.stderr or ""
        # Permanent failures: do not retry
        permanent = ("Private video", "Video unavailable", "Sign in to confirm", "members-only")
        if any(p in last_err for p in permanent):
            return result.returncode, result.stdout, last_err
        if attempt < MAX_RETRIES:
            wait = RETRY_BACKOFF_SEC ** attempt
            print(f"[!] yt-dlp attempt {attempt} failed, retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)
    return 1, "", last_err


def extract_video(url: str, cookies_path: str | None = None, output_dir: str = "data/yt_extracts") -> dict:
    """Extract transcript, description, and top 3 comments from a YouTube video.

    Each extraction writes to its own subdir (by video ID) to avoid
    cross-contamination when multiple extractions run.
    """
    video_id = extract_video_id(url)
    if not video_id:
        print(f"[!] Could not parse video ID from URL: {url}", file=sys.stderr)
        return {}

    # Per-video temp dir avoids picking wrong info.json across runs
    work_dir = os.path.join(output_dir, f".tmp_{video_id}")
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "yt-dlp",
        "--js-runtimes", "node",
        "--write-auto-sub",
        "--sub-lang", "en-orig,en",
        "--sub-format", "srt",
        "--skip-download",
        "--ignore-errors",
        "--write-comments",
        "--extractor-args", "youtube:max_comments=3",
        "--write-info-json",
        "-o", os.path.join(work_dir, "%(id)s.%(ext)s"),
    ]

    if cookies_path and os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])

    cmd.append(url)

    print(f"[*] Extracting: {url}")
    rc, _stdout, stderr = run_ytdlp(cmd)

    if rc != 0 and stderr:
        # Print but continue: partial extraction (subs without metadata) is possible
        print(f"[!] yt-dlp returned non-zero. stderr:\n{stderr}", file=sys.stderr)

    # Find info.json by video ID (deterministic, not by mtime)
    info_path = os.path.join(work_dir, f"{video_id}.info.json")
    if not os.path.exists(info_path):
        print(f"[!] info.json not found at {info_path}. Extraction failed.", file=sys.stderr)
        _cleanup_dir(work_dir)
        return {}

    with open(info_path, encoding='utf-8') as f:
        info = json.load(f)

    title = info.get('title', f'Unknown_{video_id}')
    safe_title = sanitize_filename(title)

    # Find subtitle file using deterministic video ID
    transcript = ""
    sub_source = None
    for lang in ['en-orig', 'en']:
        srt_path = os.path.join(work_dir, f"{video_id}.{lang}.srt")
        if os.path.exists(srt_path):
            transcript = parse_srt(srt_path)
            if transcript:
                sub_source = lang
                print(f"[+] Got transcript from {lang} subtitles ({len(transcript)} chars)")
                break

    if not transcript:
        print("[!] No transcript/subtitles available")

    comments = info.get('comments') or []
    top_comments = comments[:3]
    desc = info.get('description') or ''

    md = _build_markdown(info, transcript, top_comments, desc, url)
    md_path = os.path.join(output_dir, f"{safe_title}.md")

    # Write atomically: write to .tmp then rename
    tmp_path = md_path + ".tmp"
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(md)
        os.replace(tmp_path, md_path)
    except OSError as e:
        print(f"[!] Failed to write markdown: {e}", file=sys.stderr)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        _cleanup_dir(work_dir)
        return {}

    print(f"[+] Saved: {md_path}")
    print(f"    Title:      {title}")
    print(f"    Channel:    {info.get('channel')}")
    print(f"    Duration:   {format_duration(info.get('duration', 0))}")
    print(f"    Comments:   {len(top_comments)}")
    print(f"    Transcript: {'Yes (' + sub_source + ')' if transcript else 'No'} ({len(transcript)} chars)")

    # Only cleanup after successful write
    _cleanup_dir(work_dir)

    return {
        'video_id': video_id,
        'title': title,
        'channel': info.get('channel'),
        'url': info.get('webpage_url', url),
        'duration': info.get('duration', 0),
        'description': desc,
        'comments': top_comments,
        'transcript_length': len(transcript),
        'has_transcript': bool(transcript),
        'output_path': md_path,
    }


def _build_markdown(info: dict, transcript: str, top_comments: list, desc: str, url: str) -> str:
    """Build the markdown output from extracted data."""
    lines = [
        f"# {info.get('title', 'Unknown')}",
        "",
        f"**Channel:** {info.get('channel', 'Unknown')}",
        f"**URL:** {info.get('webpage_url', url)}",
        f"**Duration:** {format_duration(info.get('duration', 0))}",
        f"**Published:** {info.get('upload_date', 'Unknown')}",
        f"**Video ID:** {info.get('id', 'Unknown')}",
        "",
    ]

    lines.extend(["## Description", ""])
    lines.append(desc if desc else "*No description available*")
    lines.append("")

    lines.extend(["## Top Comments", ""])
    if top_comments:
        for i, c in enumerate(top_comments, 1):
            author = c.get('author', 'Anonymous')
            text = (c.get('text') or '').replace('\n', '\n> ')
            likes = c.get('like_count', 0)
            lines.append(f"**{i}. {author}** ({likes} likes)")
            lines.append(f"> {text}")
            lines.append("")
    else:
        lines.append("*No comments available*")
        lines.append("")

    lines.extend(["## Transcript", ""])
    lines.append(transcript if transcript else "*No transcript available*")
    lines.append("")

    return '\n'.join(lines)


def _cleanup_dir(path: str) -> None:
    """Remove temporary work directory."""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
    except OSError as e:
        print(f"[!] Could not cleanup {path}: {e}", file=sys.stderr)


def format_duration(seconds: int) -> str:
    """Format seconds as HH:MM:SS or M:SS."""
    if not seconds:
        return "0:00"
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def main():
    parser = argparse.ArgumentParser(description="Extract YouTube video content to markdown")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--cookies", default="cookies/cookies.txt",
                        help="Path to cookies.txt for authenticated access")
    parser.add_argument("--output-dir", default="data/yt_extracts", help="Output directory")
    parser.add_argument("--skip-dep-check", action="store_true",
                        help="Skip dependency check (advanced)")
    args = parser.parse_args()

    if not args.skip_dep_check:
        check_dependencies()

    # cookies arg may be a default path that doesn't exist — treat as optional
    cookies = args.cookies if os.path.exists(args.cookies) else None
    if args.cookies and not cookies:
        print(f"[!] Cookies path not found: {args.cookies} (continuing without auth)", file=sys.stderr)

    result = extract_video(args.url, cookies, args.output_dir)
    # Exit success if we produced a markdown file (even with partial data)
    if not result or not result.get('output_path'):
        sys.exit(1)


if __name__ == "__main__":
    main()
