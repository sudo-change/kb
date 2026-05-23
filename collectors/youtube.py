"""YouTube collector — channel RSS feeds + transcript extraction."""

from __future__ import annotations

import re
from datetime import datetime, timezone

import httpx

from collectors.base import BaseCollector
from core.models import Item

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

OEMBED_URL = "https://www.youtube.com/oembed"


class YouTubeCollector(BaseCollector):
    name = "youtube"

    def __init__(self, channels: list[str] | None = None,
                 video_urls: list[str] | None = None,
                 source_id: str = "yt", category: str | None = None):
        """channels: list of channel handles like '@LiveOverflow' or channel IDs."""
        self._channels = channels or []
        self._video_urls = video_urls or []
        self._source_id = source_id
        self._category = category

    def validate_config(self) -> bool:
        if YouTubeTranscriptApi is None:
            print("  [youtube] youtube-transcript-api not installed")
        if not self._channels and not self._video_urls:
            print("  [youtube] No channels or video_urls configured")
            return False
        return True

    def collect(self, since: datetime | None = None) -> list[Item]:
        items = []

        for url in self._video_urls:
            try:
                video_id = self._extract_video_id(url)
                if not video_id:
                    print(f"  [youtube] Can't parse video ID from: {url}")
                    continue
                item = self._collect_video(video_id)
                if item:
                    items.append(item)
            except Exception as e:
                print(f"  [youtube] Error processing {url}: {e}")

        for channel in self._channels:
            try:
                batch = self._collect_channel(channel, since)
                items.extend(batch)
                print(f"  [youtube] {channel}: {len(batch)} videos")
            except Exception as e:
                print(f"  [youtube] Error channel {channel}: {e}")

        return items

    def _collect_channel(self, channel: str, since: datetime | None) -> list[Item]:
        import feedparser

        if channel.startswith("UC") and len(channel) == 24:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
        else:
            handle = channel.lstrip("@")
            channel_id = self._resolve_handle(handle)
            if channel_id:
                feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            else:
                feed_url = f"https://www.youtube.com/feeds/videos.xml?user={handle}"

        feed = feedparser.parse(feed_url)
        items = []

        for entry in feed.entries[:10]:
            video_id = entry.get("yt_videoid", "")
            if not video_id:
                video_id = self._extract_video_id(entry.get("link", ""))
            if not video_id:
                continue

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            if since and published and published <= since:
                continue

            transcript = self._get_transcript(video_id)

            item = Item(
                url=entry.get("link", f"https://www.youtube.com/watch?v={video_id}"),
                title=entry.get("title", f"YouTube {video_id}"),
                source_id=f"{self._source_id}:{video_id}",
                source_type="youtube",
                body=transcript,
                summary=transcript[:300] + "..." if len(transcript) > 300 else transcript,
                category=self._category,
                tags=["youtube", "transcript"],
                metadata={"channel": channel, "video_id": video_id},
                published_at=published,
            )
            items.append(item)

        return items

    def _collect_video(self, video_id: str) -> Item | None:
        meta = self._get_video_meta(video_id)
        title = meta.get("title", f"YouTube Video {video_id}")
        author = meta.get("author_name", "")
        transcript = self._get_transcript(video_id)

        if not transcript:
            print(f"  [youtube] No transcript for {video_id}")

        return Item(
            url=f"https://www.youtube.com/watch?v={video_id}",
            title=title,
            source_id=f"{self._source_id}:{video_id}",
            source_type="youtube",
            body=transcript,
            summary=transcript[:300] + "..." if len(transcript) > 300 else transcript,
            category=self._category,
            tags=["youtube", "transcript"],
            metadata={
                "video_id": video_id,
                "channel": author,
                "thumbnail": meta.get("thumbnail_url", ""),
            },
        )

    def _resolve_handle(self, handle: str) -> str | None:
        """Resolve @handle to UC... channel_id via YouTube page scrape."""
        import re as _re
        try:
            resp = httpx.get(
                f"https://www.youtube.com/@{handle}",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
                follow_redirects=True,
            )
            m = _re.search(r'"channelId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"', resp.text)
            if m:
                return m.group(1)
            m = _re.search(r'"externalId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"', resp.text)
            if m:
                return m.group(1)
        except Exception:
            pass
        return None

    def _get_transcript(self, video_id: str) -> str:
        if YouTubeTranscriptApi is None:
            return ""
        try:
            parts = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join(p["text"] for p in parts)
        except Exception:
            try:
                parts = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
                return " ".join(p["text"] for p in parts)
            except Exception:
                return ""

    def _get_video_meta(self, video_id: str) -> dict:
        try:
            resp = httpx.get(
                OEMBED_URL,
                params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {}

    @staticmethod
    def _extract_video_id(url: str) -> str | None:
        patterns = [
            r"(?:v=|\/v\/|youtu\.be\/)([a-zA-Z0-9_-]{11})",
            r"(?:embed\/)([a-zA-Z0-9_-]{11})",
            r"^([a-zA-Z0-9_-]{11})$",
        ]
        for pattern in patterns:
            m = re.search(pattern, url)
            if m:
                return m.group(1)
        return None
