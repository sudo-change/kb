# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
YouTube Playlist Extractor — batch-extract all videos from a playlist.

Fetches the playlist metadata via yt-dlp, then extracts each video using
the existing yt_extract.py single-video extractor. Processes in configurable
chunk sizes with progress tracking and resume support.

Usage:
    python scripts/yt_playlist.py <playlist_url> [--chunk 5] [--cookies path]
    python scripts/yt_playlist.py <playlist_url> --list-only  # just list videos

Resume: Already-extracted videos (by video_id in filename) are skipped
automatically. Re-run the same command to resume after interruption.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Ensure repo root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.yt_extract import (
    DEFAULT_COOKIES_PATH,
    extract_video,
    check_dependencies,
    format_duration,
)


def get_playlist_info(playlist_url: str, cookies_path: str | None = None) -> dict:
    """Fetch playlist metadata and video list via yt-dlp --flat-playlist."""
    cmd = [
        "yt-dlp",
        "--js-runtimes", "node",
        "--flat-playlist",
        "--dump-json",
        "--no-warnings",
    ]
    if cookies_path and os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])
    cmd.append(playlist_url)

    print(f"[*] Fetching playlist metadata: {playlist_url}")
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", timeout=120,
    )

    if result.returncode != 0:
        print(f"[!] yt-dlp failed: {result.stderr[:500]}", file=sys.stderr)
        return {"entries": []}

    entries = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return {"entries": entries}


def already_extracted(output_dir: str, video_id: str) -> bool:
    """Check if a video was already extracted (by video_id in filename)."""
    for f in os.listdir(output_dir):
        if f.endswith(".md") and f"[{video_id}]" in f:
            return True
    return False


def extract_playlist(
    playlist_url: str,
    cookies_path: str | None = None,
    output_dir: str = "data/yt_extracts",
    chunk_size: int = 5,
    list_only: bool = False,
    timeout_sec: int = 600,
) -> dict:
    """Extract all videos from a YouTube playlist in chunks.

    Returns summary dict with counts and any errors.
    """
    os.makedirs(output_dir, exist_ok=True)

    info = get_playlist_info(playlist_url, cookies_path)
    entries = info.get("entries", [])

    if not entries:
        print("[!] No videos found in playlist")
        return {"total": 0, "extracted": 0, "skipped": 0, "errors": []}

    print(f"\n[+] Playlist has {len(entries)} videos")

    if list_only:
        for i, entry in enumerate(entries, 1):
            vid = entry.get("id", "?")
            title = entry.get("title", "Unknown")
            duration = entry.get("duration")
            dur_str = format_duration(duration) if duration else "?"
            status = "✓ done" if already_extracted(output_dir, vid) else "  todo"
            print(f"  {i:3d}. [{status}] {title} ({dur_str}) [{vid}]")
        done = sum(1 for e in entries if already_extracted(output_dir, e.get("id", "")))
        print(f"\n  {done}/{len(entries)} already extracted")
        return {"total": len(entries), "extracted": 0, "skipped": done, "errors": []}

    extracted = 0
    skipped = 0
    errors = []

    for chunk_start in range(0, len(entries), chunk_size):
        chunk = entries[chunk_start:chunk_start + chunk_size]
        chunk_num = chunk_start // chunk_size + 1
        total_chunks = (len(entries) + chunk_size - 1) // chunk_size
        print(f"\n{'='*60}")
        print(f"  Chunk {chunk_num}/{total_chunks} "
              f"(videos {chunk_start+1}-{min(chunk_start+chunk_size, len(entries))} "
              f"of {len(entries)})")
        print(f"{'='*60}")

        for i, entry in enumerate(chunk, 1):
            video_id = entry.get("id", "")
            title = entry.get("title", "Unknown")
            idx = chunk_start + i

            if not video_id:
                print(f"  [{idx}/{len(entries)}] Skipped (no video ID)")
                skipped += 1
                continue

            if already_extracted(output_dir, video_id):
                print(f"  [{idx}/{len(entries)}] Already done: {title}")
                skipped += 1
                continue

            print(f"\n  [{idx}/{len(entries)}] Extracting: {title}")
            url = f"https://www.youtube.com/watch?v={video_id}"

            try:
                result = extract_video(
                    url=url,
                    cookies_path=cookies_path,
                    output_dir=output_dir,
                    timeout_sec=timeout_sec,
                )
                if result and result.get("output_path"):
                    extracted += 1
                else:
                    errors.append(f"{video_id}: extraction returned empty")
            except Exception as e:
                err = f"{video_id}: {e}"
                print(f"  [!] Error: {err}", file=sys.stderr)
                errors.append(err)

        # Brief pause between chunks to be polite to YouTube
        if chunk_start + chunk_size < len(entries):
            print(f"\n  Pausing 3s between chunks...")
            time.sleep(3)

    print(f"\n{'='*60}")
    print(f"  DONE: {extracted} extracted, {skipped} skipped, {len(errors)} errors")
    print(f"{'='*60}")

    if errors:
        print("\n  Errors:")
        for err in errors:
            print(f"    • {err}")

    return {
        "total": len(entries),
        "extracted": extracted,
        "skipped": skipped,
        "errors": errors,
    }


def _resolve_cookies(explicit: str | None) -> str | None:
    if explicit:
        if os.path.exists(explicit):
            return explicit
        print(f"[!] Cookies path not found: {explicit}", file=sys.stderr)
        sys.exit(2)
    return DEFAULT_COOKIES_PATH if os.path.exists(DEFAULT_COOKIES_PATH) else None


def main():
    parser = argparse.ArgumentParser(
        description="Batch-extract all videos from a YouTube playlist",
    )
    parser.add_argument("url", help="YouTube playlist URL")
    parser.add_argument("--chunk", type=int, default=5,
                        help="Videos per chunk (default: 5)")
    parser.add_argument("--cookies", default=None,
                        help=f"Path to cookies.txt (auto: {DEFAULT_COOKIES_PATH})")
    parser.add_argument("--output-dir", default="data/yt_extracts",
                        help="Output directory")
    parser.add_argument("--timeout", type=int, default=600,
                        help="Per-video timeout in seconds")
    parser.add_argument("--list-only", action="store_true",
                        help="List playlist videos without extracting")
    parser.add_argument("--skip-dep-check", action="store_true",
                        help="Skip dependency check")
    args = parser.parse_args()

    if not args.skip_dep_check:
        check_dependencies()

    cookies = _resolve_cookies(args.cookies)

    result = extract_playlist(
        playlist_url=args.url,
        cookies_path=cookies,
        output_dir=args.output_dir,
        chunk_size=args.chunk,
        list_only=args.list_only,
        timeout_sec=args.timeout,
    )

    if result.get("errors"):
        sys.exit(1)


if __name__ == "__main__":
    main()
