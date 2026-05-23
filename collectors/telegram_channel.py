"""Telegram channel collector using Telethon (MTProto)."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone

from collectors.base import BaseCollector
from core.models import Item

try:
    from telethon import TelegramClient
    from telethon.tl.types import Message, MessageMediaWebPage
    _HAS_TELETHON = True
except ImportError:
    _HAS_TELETHON = False
    TelegramClient = None


class TelegramChannelCollector(BaseCollector):
    name = "telegram"

    def __init__(self, api_id: int, api_hash: str, phone: str,
                 channels: list[str | int] | None = None,
                 session_name: str = "kf_telegram",
                 category: str | None = None,
                 source_id: str = "telegram"):
        self._api_id = api_id
        self._api_hash = api_hash
        self._phone = phone
        self._channels = channels or []
        self._session_name = session_name
        self._category = category
        self._source_id = source_id

    def validate_config(self) -> bool:
        if not _HAS_TELETHON:
            print("  [telegram] telethon not installed. Run: pip install telethon")
            return False
        if not self._api_id or not self._api_hash:
            print("  [telegram] api_id and api_hash required (my.telegram.org)")
            return False
        if not self._channels:
            print("  [telegram] No channels configured")
            return False
        return True

    def collect(self, since: datetime | None = None) -> list[Item]:
        if not self.is_authenticated():
            print("  [telegram] No session found. Authenticate first.")
            return []
        return asyncio.run(self._collect_async(since))

    def is_authenticated(self) -> bool:
        import os
        session_file = f"{self._session_name}.session"
        return os.path.exists(session_file) and os.path.getsize(session_file) > 0

    async def _collect_async(self, since: datetime | None) -> list[Item]:
        items: list[Item] = []
        async with TelegramClient(self._session_name, self._api_id, self._api_hash) as client:
            for channel_ref in self._channels:
                try:
                    batch = await self._collect_channel(client, channel_ref, since)
                    items.extend(batch)
                    print(f"  [telegram] {channel_ref}: {len(batch)} posts")
                except Exception as e:
                    print(f"  [telegram] Error {channel_ref}: {e}")
        return items

    async def _collect_channel(self, client, channel_ref: str | int, since: datetime | None) -> list[Item]:
        entity = await client.get_entity(channel_ref)
        channel_title = getattr(entity, "title", str(channel_ref))
        channel_username = getattr(entity, "username", None)

        items = []
        async for message in client.iter_messages(entity, limit=100, offset_date=since,
                                                   reverse=since is not None):
            if not isinstance(message, Message):
                continue
            if not message.text and not message.media:
                continue
            item = self._message_to_item(message, channel_title, channel_username)
            if item:
                items.append(item)
        return items

    def _message_to_item(self, message, channel_title: str, channel_username: str | None) -> Item | None:
        text = message.text or message.message or ""
        if not text and not message.media:
            return None

        msg_id = message.id
        if channel_username:
            url = f"https://t.me/{channel_username}/{msg_id}"
        else:
            url = f"https://t.me/c/{message.chat_id}/{msg_id}"

        lines = text.strip().split("\n")
        title = lines[0][:120] if lines else f"Post from {channel_title}"
        tags = re.findall(r"#(\w+)", text)

        summary = ""
        if message.media and isinstance(message.media, MessageMediaWebPage):
            wp = message.media.webpage
            if hasattr(wp, "title") and wp.title:
                summary = wp.title
            if hasattr(wp, "description") and wp.description:
                summary += f" — {wp.description}"

        return Item(
            url=url,
            title=title,
            source_id=f"{self._source_id}:{message.chat_id}_{msg_id}",
            source_type="telegram",
            body=text,
            summary=summary,
            category=self._category,
            tags=tags,
            score=float(getattr(message, "views", 0) or 0),
            metadata={
                "channel_title": channel_title,
                "channel_username": channel_username,
                "views": getattr(message, "views", None),
                "forwards": getattr(message, "forwards", None),
            },
            published_at=message.date.replace(tzinfo=timezone.utc) if message.date else None,
        )
