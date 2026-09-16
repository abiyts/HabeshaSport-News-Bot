import os
import asyncio
from telethon import TelegramClient

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

client = TelegramClient("bot", API_ID, API_HASH)

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("✅ HabeshaSport bot connected successfully!")
    print("🤖 Bot is running...")
    
    await client.run_until_disconnected()

asyncio.run(main())
