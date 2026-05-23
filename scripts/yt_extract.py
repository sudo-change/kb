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
import subprocess
import sys
from pathlib import Path


def sanitize_filename(title: str) -> str:
    """Remove/replace chars invalid in filenames."""
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title[:200]  # cap length


def parse_srt(srt_path: str) -> str:
    """Parse SRT file into plain text (no timestamps)."""
    if not os.path.exists(srt_path):
        return ""
    lines = []
    with open(srt_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip sequence numbers and timestamp lines
            if re.match(r'^\d+$', line):
                continue
            if re.match(r'^\d{2}:\d{2}:\d{2}', line):
                continue
            if line:
                # Remove HTML tags from auto-subs
                clean = re.sub(r'<[^>]+>', '', line)
                if clean and clean not in lines[-1:]:
                    lines.append(clean)
    return '\n'.join(lines)


def extract_video(url: str, cookies_path: str | None = None, output_dir: str = "data/yt_extracts") -> dict:
    """Extract transcript, description, and top 3 comments from a YouTube video."""
    os.makedirs(output_dir, exist_ok=True)

    # Build yt-dlp command for metadata + subtitles
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
        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
    ]

    if cookies_path and os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])

    cmd.append(url)

    print(f"[*] Extracting: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

    if result.returncode != 0:
        print(f"[!] yt-dlp warning/error:\n{result.stderr}", file=sys.stderr)

    # Find the info.json file
    info_files = list(Path(output_dir).glob("*.info.json"))
    # Get the most recently modified one
    if not info_files:
        print("[!] No info.json found. Extraction may have failed.")
        return {}

    info_file = max(info_files, key=lambda p: p.stat().st_mtime)
    with open(info_file, encoding='utf-8') as f:
        info = json.load(f)

    title = info.get('title', 'Unknown')
    safe_title = sanitize_filename(title)

    # Find subtitle file
    transcript = ""
    for lang in ['en-orig', 'en']:
        srt_path = os.path.join(output_dir, f"{title}.{lang}.srt")
        if os.path.exists(srt_path):
            transcript = parse_srt(srt_path)
            if transcript:
                print(f"[+] Got transcript from {lang} subtitles")
                break

    if not transcript:
        # Try glob match (title might have been sanitized differently by yt-dlp)
        for srt in Path(output_dir).glob("*.srt"):
            transcript = parse_srt(str(srt))
            if transcript:
                print(f"[+] Got transcript from {srt.name}")
                break

    if not transcript:
        print("[!] No transcript/subtitles available")

    # Extract comments
    comments = info.get('comments', [])
    top_comments = comments[:3]

    # Build markdown output
    md_lines = [
        f"# {title}",
        "",
        f"**Channel:** {info.get('channel', 'Unknown')}",
        f"**URL:** {info.get('webpage_url', url)}",
        f"**Duration:** {format_duration(info.get('duration', 0))}",
        f"**Published:** {info.get('upload_date', 'Unknown')}",
        "",
    ]

    # Description
    desc = info.get('description', '')
    if desc:
        md_lines.extend(["## Description", "", desc, ""])
    else:
        md_lines.extend(["## Description", "", "*No description available*", ""])

    # Top 3 comments
    if top_comments:
        md_lines.extend(["## Top Comments", ""])
        for i, c in enumerate(top_comments, 1):
            author = c.get('author', 'Anonymous')
            text = c.get('text', '')
            likes = c.get('like_count', 0)
            md_lines.append(f"**{i}. {author}** ({likes} likes)")
            md_lines.append(f"> {text}")
            md_lines.append("")
    else:
        md_lines.extend(["## Top Comments", "", "*No comments available*", ""])

    # Transcript
    if transcript:
        md_lines.extend(["## Transcript", "", transcript, ""])
    else:
        md_lines.extend(["## Transcript", "", "*No transcript available*", ""])

    # Write markdown file
    md_path = os.path.join(output_dir, f"{safe_title}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"[+] Saved: {md_path}")
    print(f"    Title: {title}")
    print(f"    Channel: {info.get('channel')}")
    print(f"    Duration: {format_duration(info.get('duration', 0))}")
    print(f"    Comments: {len(top_comments)}")
    print(f"    Transcript: {'Yes' if transcript else 'No'} ({len(transcript)} chars)")

    # Cleanup intermediate files (keep only .md)
    for ext in ['.info.json', '.en-orig.srt', '.en.srt']:
        p = os.path.join(output_dir, f"{title}{ext}")
        if os.path.exists(p):
            os.remove(p)

    return {
        'title': title,
        'channel': info.get('channel'),
        'url': info.get('webpage_url', url),
        'duration': info.get('duration', 0),
        'description': desc,
        'comments': top_comments,
        'transcript_length': len(transcript),
        'output_path': md_path,
    }


def format_duration(seconds: int) -> str:
    """Format seconds as HH:MM:SS."""
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def main():
    parser = argparse.ArgumentParser(description="Extract YouTube video content to markdown")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--cookies", default="cookies/cookies.txt", help="Path to cookies.txt for authenticated access")
    parser.add_argument("--output-dir", default="data/yt_extracts", help="Output directory")
    args = parser.parse_args()

    result = extract_video(args.url, args.cookies, args.output_dir)
    if not result:
        sys.exit(1)


if __name__ == "__main__":
    main()
