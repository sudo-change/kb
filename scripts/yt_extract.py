# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
YouTube Extractor — Extract transcript, description, top 3 comments from a video.
Falls back to English subtitles if no transcript available.
Output: Markdown file named "{title} [{video_id}].md".

Usage:
    python scripts/yt_extract.py <youtube_url> [--cookies path/to/cookies.txt]
    python scripts/yt_extract.py --check-deps      # validate yt-dlp + node only
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path


REQUIRED_BINS = ["yt-dlp", "node"]
MAX_RETRIES = 3
RETRY_BACKOFF_SEC = 2
DEFAULT_TIMEOUT_SEC = 600
DEFAULT_COOKIES_PATH = "cookies/cookies.txt"
COMMENT_FETCH_COUNT = 100   # Fetch many, then sort by likes locally for top 3
TOP_COMMENT_COUNT = 3

# Windows reserved filenames (case-insensitive)
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def check_dependencies() -> None:
    """Verify required binaries exist on PATH. Exit 2 if any missing."""
    missing = [b for b in REQUIRED_BINS if shutil.which(b) is None]
    if missing:
        print(f"[!] Missing required binaries: {', '.join(missing)}", file=sys.stderr)
        print(f"[!] yt-dlp: pip install yt-dlp", file=sys.stderr)
        print(f"[!] node:   https://nodejs.org/ (JS runtime for YouTube challenges)", file=sys.stderr)
        sys.exit(2)


def extract_video_id(url: str) -> str | None:
    """Extract 11-char video ID from any YouTube URL form (watch, youtu.be, shorts, live, embed)."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/|/live/|/clip/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def sanitize_filename(title: str) -> str:
    """Make a string safe as a filename on Windows, macOS, Linux."""
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.rstrip('. ')  # Windows: trailing dots/spaces invalid
    if title.upper() in _WINDOWS_RESERVED:
        title = f"{title}_video"
    return title[:180] or "untitled"


def parse_srt(srt_path: str) -> str:
    """Parse SRT into plain text. Dedup consecutive identical lines (rolling captions)."""
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
            clean = re.sub(r'<[^>]+>', '', line).strip()
            if not clean:
                continue
            if not lines or lines[-1] != clean:
                lines.append(clean)
    return '\n'.join(lines)


# Lower-cased substrings that mean "do not retry, will never succeed"
_PERMANENT_ERRORS = (
    "private video",
    "video unavailable",
    "sign in to confirm",
    "members-only",
    "age-restricted",
    "this video is private",
    "this video has been removed",
    "no longer available",
    "video is no longer available",
    "premiere",  # not yet aired
    "unavailable in your country",
)


def is_permanent_error(stderr: str) -> bool:
    """Check if yt-dlp error text indicates a permanent (non-retryable) failure."""
    s = (stderr or "").lower()
    return any(p in s for p in _PERMANENT_ERRORS)


def run_ytdlp(cmd: list[str], timeout_sec: int = DEFAULT_TIMEOUT_SEC) -> tuple[int, str, str]:
    """Run yt-dlp with retries on transient failures. Has hard timeout."""
    last_err = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding='utf-8', timeout=timeout_sec,
            )
        except subprocess.TimeoutExpired:
            last_err = f"yt-dlp timed out after {timeout_sec}s"
            print(f"[!] {last_err}", file=sys.stderr)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SEC ** attempt)
                continue
            return 124, "", last_err

        if result.returncode == 0:
            return 0, result.stdout, result.stderr

        last_err = result.stderr or ""
        if is_permanent_error(last_err):
            return result.returncode, result.stdout, last_err

        if attempt < MAX_RETRIES:
            wait = RETRY_BACKOFF_SEC ** attempt
            print(f"[!] yt-dlp attempt {attempt} failed, retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)

    return 1, "", last_err


def _top_comments(comments: list[dict], n: int = TOP_COMMENT_COUNT) -> list[dict]:
    """Pick the n most-liked top-level comments. Replies excluded.

    yt-dlp returns mixed top-level + replies (parent != 'root' for replies).
    Some yt-dlp versions use is_pinned/like_count differently. Be defensive.
    """
    top_level = [c for c in comments if (c.get('parent') in (None, 'root'))]
    return sorted(
        top_level,
        key=lambda c: (c.get('like_count') or 0, c.get('timestamp') or 0),
        reverse=True,
    )[:n]


def extract_video(
    url: str,
    cookies_path: str | None = None,
    output_dir: str = "data/yt_extracts",
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
) -> dict:
    """Extract transcript, description, and top 3 comments from a YouTube video.

    Uses a unique per-run temp dir to avoid races between concurrent extractions.
    Output markdown filename includes video_id to prevent same-title collisions.
    """
    video_id = extract_video_id(url)
    if not video_id:
        print(f"[!] Could not parse video ID from URL: {url}", file=sys.stderr)
        return {}

    os.makedirs(output_dir, exist_ok=True)

    # Unique work dir: pid + uuid makes concurrent same-video runs safe
    run_id = f"{os.getpid()}_{uuid.uuid4().hex[:8]}"
    work_dir = os.path.join(output_dir, f".tmp_{video_id}_{run_id}")
    os.makedirs(work_dir, exist_ok=True)

    cmd = [
        "yt-dlp",
        "--js-runtimes", "node",
        # Manual subs preferred (cleaner); auto-subs as fallback
        "--write-subs",
        "--write-auto-sub",
        "--sub-lang", "en-orig,en,en-US,en-GB",
        "--sub-format", "srt",
        "--skip-download",
        "--ignore-errors",
        "--write-comments",
        # max_comments format: TOTAL,PER_THREAD,REPLIES,REPLIES_PER_PAGE
        # Set REPLIES=0 so we only get top-level comments (we don't render replies anyway).
        # comment_sort=top returns highest-liked first, but we re-sort locally as a safety net.
        "--extractor-args",
        f"youtube:max_comments={COMMENT_FETCH_COUNT},all,0,0;comment_sort=top",
        "--write-info-json",
        "-o", os.path.join(work_dir, "%(id)s.%(ext)s"),
    ]

    if cookies_path and os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])

    cmd.append(url)

    print(f"[*] Extracting: {url}")
    rc, _stdout, stderr = run_ytdlp(cmd, timeout_sec=timeout_sec)

    if rc != 0 and stderr:
        # Don't fail outright — partial output (subs or info) may still exist
        print(f"[!] yt-dlp returned {rc}. stderr (truncated):\n{stderr[:2000]}", file=sys.stderr)

    info_path = os.path.join(work_dir, f"{video_id}.info.json")
    if not os.path.exists(info_path):
        print(f"[!] info.json not found at {info_path}. Extraction failed.", file=sys.stderr)
        _cleanup_dir(work_dir)
        return {}

    with open(info_path, encoding='utf-8') as f:
        info = json.load(f)

    title = info.get('title', f'Unknown_{video_id}')

    # Find subtitle file: manual subs preferred, auto as fallback
    transcript = ""
    sub_source = None
    sub_candidates = ['en', 'en-US', 'en-GB', 'en-orig']
    # Try manual first (yt-dlp names them "{id}.{lang}.srt"), then auto (same naming).
    # Manual vs auto distinguished by which was actually written; we just try each lang.
    for lang in sub_candidates:
        srt_path = os.path.join(work_dir, f"{video_id}.{lang}.srt")
        if os.path.exists(srt_path):
            transcript = parse_srt(srt_path)
            if transcript:
                sub_source = lang
                print(f"[+] Got transcript from '{lang}' subtitles ({len(transcript)} chars)")
                break

    if not transcript:
        print("[!] No transcript/subtitles available", file=sys.stderr)

    comments = info.get('comments') or []
    top_comments = _top_comments(comments, TOP_COMMENT_COUNT)
    desc = info.get('description') or ''

    md = _build_markdown(info, transcript, top_comments, desc, url)

    # Output filename includes video_id — avoids collisions on shared titles
    safe_title = sanitize_filename(title)
    md_filename = f"{safe_title} [{video_id}].md"
    md_path = os.path.join(output_dir, md_filename)

    # Atomic write: tmp -> rename
    tmp_path = md_path + ".tmp"
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(md)
        os.replace(tmp_path, md_path)
    except OSError as e:
        print(f"[!] Failed to write markdown: {e}", file=sys.stderr)
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        _cleanup_dir(work_dir)
        return {}

    print(f"[+] Saved: {md_path}")
    print(f"    Title:      {title}")
    print(f"    Channel:    {info.get('channel')}")
    print(f"    Duration:   {format_duration(info.get('duration', 0))}")
    print(f"    Comments:   {len(top_comments)} (of {len(comments)} fetched)")
    print(f"    Transcript: {('Yes (' + sub_source + ')') if transcript else 'No'} "
          f"({len(transcript)} chars)")

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
        "## Description",
        "",
        desc if desc else "*No description available*",
        "",
        "## Top Comments",
        "",
    ]

    if top_comments:
        for i, c in enumerate(top_comments, 1):
            author = c.get('author', 'Anonymous')
            text = (c.get('text') or '').replace('\n', '\n> ')
            likes = c.get('like_count') or 0
            lines.append(f"**{i}. {author}** ({likes} likes)")
            lines.append(f"> {text}")
            lines.append("")
    else:
        lines.append("*No comments available*")
        lines.append("")

    lines.append("## Transcript")
    lines.append("")
    lines.append(transcript if transcript else "*No transcript available*")
    lines.append("")

    return '\n'.join(lines)


def _cleanup_dir(path: str) -> None:
    """Remove temporary work directory; ignore errors."""
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
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _resolve_cookies(explicit: str | None) -> str | None:
    """Resolve cookies path. Auto-pick default if it exists; error if explicit path missing."""
    if explicit:
        if os.path.exists(explicit):
            return explicit
        print(f"[!] Explicit --cookies path not found: {explicit}", file=sys.stderr)
        sys.exit(2)
    # Silent auto-discovery: use default only if it exists, no warning otherwise
    return DEFAULT_COOKIES_PATH if os.path.exists(DEFAULT_COOKIES_PATH) else None


def main():
    parser = argparse.ArgumentParser(
        description="Extract YouTube video content to markdown",
    )
    parser.add_argument("url", nargs="?", help="YouTube video URL")
    parser.add_argument("--cookies", default=None,
                        help=f"Path to cookies.txt (auto: {DEFAULT_COOKIES_PATH} if exists)")
    parser.add_argument("--output-dir", default="data/yt_extracts", help="Output directory")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC,
                        help="yt-dlp subprocess timeout in seconds")
    parser.add_argument("--check-deps", action="store_true",
                        help="Validate yt-dlp + node are on PATH, then exit")
    parser.add_argument("--skip-dep-check", action="store_true",
                        help="Skip dependency check before extraction (advanced)")
    args = parser.parse_args()

    if args.check_deps:
        check_dependencies()
        print("[+] Dependencies OK")
        return

    if not args.url:
        parser.error("url is required (or pass --check-deps)")

    if not args.skip_dep_check:
        check_dependencies()

    cookies = _resolve_cookies(args.cookies)

    result = extract_video(args.url, cookies, args.output_dir, timeout_sec=args.timeout)
    if not result or not result.get('output_path'):
        sys.exit(1)


if __name__ == "__main__":
    main()
