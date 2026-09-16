import os
import asyncio
from telethon import TelegramClient

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

client = TelegramClient("bot", API_ID, API_HASH)

async def main():
    await client.start(bot_token=BOT_TOKEN)

    print("✅ Bot connected!")

    await client.send_message(
        "@habeshasport",
        "🤖 HabeshaSport News Bot is connected successfully!"
    )

    print("✅ Test message sent to @habeshasport!")

    await client.disconnect()

asyncio.run(main())
