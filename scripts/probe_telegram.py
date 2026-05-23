"""One-shot probe: verify bot auth, chat access, and all topic IDs."""
import asyncio
import json
import os

from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
topic_ids = json.loads(os.getenv("TELEGRAM_TOPIC_IDS", "{}"))


async def main():
    bot = Bot(token=token)

    me = await bot.get_me()
    print(f"Bot: @{me.username}")

    try:
        chat = await bot.get_chat(chat_id)
        print(f"Chat: {chat.title} (id={chat_id})")
    except TelegramError as e:
        print(f"FAIL get_chat: {e}")
        return

    for name, tid in topic_ids.items():
        try:
            msg = await bot.send_message(
                chat_id=chat_id,
                text=f"[KF probe] {name}",
                message_thread_id=tid,
            )
            print(f"  OK   {name} (thread {tid}) -> msg {msg.message_id}")
        except TelegramError as e:
            print(f"  FAIL {name} (thread {tid}): {e}")


asyncio.run(main())
