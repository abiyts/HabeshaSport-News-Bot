from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Put the SAME API_ID and API_HASH from your working bot.py here.
API_ID = 12345678
API_HASH = "PASTE_YOUR_API_HASH_HERE"

# This must match the existing session file in your sports_news_bot folder:
SESSION_NAME = "sports_user_secondary"

with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
    string_session = StringSession.save(client.session)

    print("\n" + "=" * 60)
    print("YOUR USER_SESSION")
    print("=" * 60)
    print(string_session)
    print("=" * 60)
    print("\nCopy the ENTIRE line above.")
    print("Keep it secret. Do NOT send it to anyone.")
    input("\nPress Enter to close...")
