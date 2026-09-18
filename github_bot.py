import os
import re
import json
import html
import urllib.parse
import urllib.request
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession


# =========================================================
# GITHUB / TELEGRAM SETTINGS
# =========================================================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
USER_SESSION = os.environ["USER_SESSION"]


# =========================================================
# CHANNEL SETTINGS
# =========================================================

DESTINATION_CHANNEL = "@habeshasport"

SOURCE_CHANNELS = [
    "@futbol_fudbol_sport_tv_gollar",
    "@sky_sports_world",
    "@FabrizioRomanoTG",
    "@Sky_sports_football_updates",
    "@Premier_League_News_TG",
    "@goal_sport_football",
    "@espndc_news",
]


# =========================================================
# STATE FILE
# =========================================================

STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("⚠ Could not read state.json:", e)
        return {}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)

        print("💾 State saved")

    except Exception as e:
        print("❌ Could not save state:", e)


# =========================================================
# REMOVE LINKS
# =========================================================

def remove_links(text):
    if not text:
        return ""

    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'(https?://)?t\.me/\S+', '', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    return text.strip()


# =========================================================
# TRANSLATE ENGLISH → AMHARIC
# =========================================================

def translate_to_amharic(text):
    if not text:
        return ""

    try:
        url = (
            "https://api.mymemory.translated.net/get"
            "?q="
            + urllib.parse.quote(text[:450])
            + "&langpair=en|am"
        )

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read().decode("utf-8")

        result = json.loads(data)

        translated = result.get(
            "responseData", {}
        ).get(
            "translatedText", ""
        )

        if translated:
            return translated.strip()

        print("⚠ Translation returned empty result")
        return text

    except Exception as e:
        print("⚠ Translation error:", e)
        return text


# =========================================================
# CREATE FINAL POST
# =========================================================

def create_post(text):
    text = remove_links(text)

    if not text:
        return ""

    translated = translate_to_amharic(text)

    if not translated:
        translated = text

    translated = html.escape(translated)

    return (
        "⚽ <b>የእግር ኳስ ዜና</b>\n\n"
        + translated
        + "\n\n"
        "📢 <b>Habesha Sport</b>"
    )


# =========================================================
# PROCESS ONE MESSAGE
# =========================================================

async def process_message(
    user_client,
    bot_client,
    message,
    source_username
):
    try:
        original_text = message.message or ""

        print("\n" + "=" * 60)
        print("📰 NEW NEWS")
        print("SOURCE:", source_username)
        print("MESSAGE ID:", message.id)
        print("TEXT:")
        print(original_text[:500])

        post = create_post(original_text)

        # -------------------------------------------------
        # MEDIA
        # -------------------------------------------------

        if message.media:
            print("📷 Media detected")
            print("⬇ Downloading media...")

            media = await user_client.download_media(message)

            if media:
                await bot_client.send_file(
                    DESTINATION_CHANNEL,
                    media,
                    caption=post,
                    parse_mode="html",
                    force_document=False
                )

                print("✅ MEDIA POSTED TO", DESTINATION_CHANNEL)

                try:
                    os.remove(media)
                except Exception:
                    pass

                return True

            print("⚠ Media download failed")

        # -------------------------------------------------
        # TEXT ONLY
        # -------------------------------------------------

        if post:
            await bot_client.send_message(
                DESTINATION_CHANNEL,
                post,
                parse_mode="html"
            )

            print("✅ TEXT POSTED TO", DESTINATION_CHANNEL)
            return True

        print("⚠ Message contained no usable text")
        return True

    except Exception as e:
        print("❌ ERROR PROCESSING MESSAGE:", e)
        return False


# =========================================================
# CHECK CHANNEL
# =========================================================

async def check_channel(
    user_client,
    bot_client,
    channel,
    state
):
    try:
        entity = await user_client.get_entity(channel)

        username = getattr(
            entity,
            "username",
            channel
        )

        print("\n" + "-" * 60)
        print("🔎 Checking:", username)

        # -------------------------------------------------
# SAFE INITIALIZATION
# -------------------------------------------------
# If this is a newly added channel or its state is
# suspiciously low, establish the current latest
# message as the starting point.
# This prevents old messages from being reposted.
# -------------------------------------------------

last_id = int(state.get(channel, 0))

if last_id <= 13:
    latest_messages = await user_client.get_messages(
        entity,
        limit=1
    )

    if latest_messages:
        latest_id = latest_messages[0].id

        print("⚠ Safe initialization for:", channel)
        print("Old state:", last_id)
        print("Current latest message ID:", latest_id)
        print("➡ Starting from current message. Old messages will NOT be posted.")

        state[channel] = latest_id
        save_state(state)

        return

print("Last processed ID:", last_id)

messages = []

        async for message in user_client.iter_messages(
            entity,
            min_id=last_id,
            reverse=True
        ):
            messages.append(message)

        if not messages:
            print("ℹ No new messages")
            return

        print(f"📥 Found {len(messages)} new message(s)")

        highest_successful_id = last_id

        for message in messages:
            success = await process_message(
                user_client,
                bot_client,
                message,
                username
            )

            if success:
                highest_successful_id = max(
                    highest_successful_id,
                    message.id
                )
                await asyncio.sleep(2)
            else:
                print("⚠ Message failed.")
                print("⚠ State will NOT move past this message.")
                break

        if highest_successful_id > last_id:
            state[channel] = highest_successful_id
            save_state(state)

            print(
                "✅ Updated last ID:",
                highest_successful_id
            )

    except Exception as e:
        print("❌ CHANNEL ERROR:", channel)
        print(e)


# =========================================================
# MAIN
# =========================================================

async def main():
    print("\n" + "=" * 60)
    print("🚀 HABESHA SPORT GITHUB BOT")
    print("=" * 60)

    state = load_state()

    user_client = TelegramClient(
    StringSession(USER_SESSION),
    API_ID,
    API_HASH,
    connection_retries=10,
    retry_delay=5,
    request_retries=10,
    auto_reconnect=True
)

    bot_client = TelegramClient(
        StringSession(),
        API_ID,
        API_HASH
    )

    try:
        print("\n🔐 Connecting Telegram user...")
        await user_client.start()
        print("✅ Telegram user connected")

        print("\n🤖 Connecting Telegram bot...")
        await bot_client.start(bot_token=BOT_TOKEN)
        print("✅ Telegram bot connected")

        print("\n📢 Destination:", DESTINATION_CHANNEL)
        print("\n🔎 Checking source channels...")

        for channel in SOURCE_CHANNELS:
            await check_channel(
                user_client,
                bot_client,
                channel,
                state
            )

        print("\n" + "=" * 60)
        print("✅ CHECK COMPLETE")
        print("=" * 60)

    finally:
        await bot_client.disconnect()
        await user_client.disconnect()
        print("\n🔌 Telegram connections closed")


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
