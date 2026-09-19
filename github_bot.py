import os
import re
import json
import html
import urllib.parse
import urllib.request
import asyncio

from telethon import TelegramClient
from telethon import Button
from telethon.sessions import StringSession


# =========================================================
# GITHUB / TELEGRAM SETTINGS
# =========================================================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
USER_SESSION = os.environ["USER_SESSION"]


# =========================================================
# CHANNEL ROUTING
# =========================================================

DEFAULT_DESTINATION = "@habeshasport"

SOURCE_ROUTES = {

    # =====================================================
    # ARSENAL
    # =====================================================
    "@arsenal_gunners_london": "@arsenaletgunners",
    "@Arsenalc": "@arsenaletgunners",
    "@gunnersfooty": "@arsenaletgunners",
    "@GUNNERS": "@arsenaletgunners",

    # =====================================================
    # LIVERPOOL
    # =====================================================
    "@LiverpoolFCNews": "@liverpoolethiop",
    "@liverpool": "@liverpoolethiop",
    "@lfconline": "@liverpoolethiop",

    # =====================================================
    # MANCHESTER CITY
    # =====================================================
    "@Manchester_City": "@mancitynewset",
    "@manchester_city_cf": "@mancitynewset",
    "@mancity247": "@mancitynewset",

    # =====================================================
    # CHELSEA
    # =====================================================
    "@Chelsea_fc_worldwide": "@chelseafcet",
    "@chelseafcnews01": "@chelseafcet",
    "@chelseaanalysis": "@chelseafcet",
    "@chelseasunsport": "@chelseafcet",

    # =====================================================
    # MANCHESTER UNITED
    # =====================================================
    "@ManchesterUnited": "@manunitedethiopia",
    "@Empire_MU": "@manunitedethiopia",
    "@manchester_united_uk": "@manunitedethiopia",
    "@manchesterunitedsunsport": "@manunitedethiopia",
}


# =========================================================
# GENERAL FOOTBALL SOURCES → HABESHA SPORT
# =========================================================

GENERAL_SOURCES = [
    "@futbol_fudbol_sport_tv_gollar",
    "@sky_sports_world",
    "@FabrizioRomanoTG",
    "@Sky_sports_football_updates",
    "@Premier_League_News_TG",
    "@goal_sport_football",
]


# =========================================================
# ALL SOURCE CHANNELS
# =========================================================

SOURCE_CHANNELS = GENERAL_SOURCES + list(SOURCE_ROUTES.keys())

# =========================================================
# PUSH BUTTONS
# =========================================================

BUTTON_INTERVAL = 10

PUSH_BUTTONS = [
    [Button.url("Man City ሲቲ", "https://t.me/mancitynewset"),
     Button.url("Liverpool ሊቨርፑል", "https://t.me/liverpoolethiop")],
    [Button.url("Arsenal አርሰናል", "https://t.me/arsenaletgunners"),
     Button.url("Man United Ethiopia", "https://t.me/manunitedethiopia")],
    [Button.url("Chelsea ቼልሲ", "https://t.me/chelseafcet"),
     Button.url("Ethio Sport", "https://t.me/habeshasport")],
]

SOURCE_CHANNELS = [
    "@futbol_fudbol_sport_tv_gollar",
    "@sky_sports_world",
    "@Sky_sports_football_updates",
    "@Premier_League_News_TG",
    "@goal_sport_football",
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

    # Remove normal web links
    text = re.sub(r'https?://\S+', '', text)

    # Remove Telegram links
    text = re.sub(r'(https?://)?t\.me/\S+', '', text)

    # Remove Telegram/channel usernames such as @FabrizioRomano
    text = re.sub(r'(?<!\w)@[A-Za-z0-9_]{3,}', '', text)

    # Remove extra blank lines
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
            "https://translate.googleapis.com/translate_a/single"
            "?client=gtx"
            "&sl=en"
            "&tl=am"
            "&dt=t"
            "&q="
            + urllib.parse.quote(text[:3000])
        )

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read().decode("utf-8")

        result = json.loads(data)

        translated = ""

        for part in result[0]:
            if part[0]:
                translated += part[0]

        if translated:
            return translated.strip()

        print("⚠ Google translation returned empty result")
        return text

    except Exception as e:
        print("⚠ Google translation error:", e)
        return text

# =========================================================
# ETHIOPIAN CALENDAR DATE
# =========================================================

from datetime import datetime, timezone, timedelta

def get_ethiopian_date_and_session():
    now = datetime.now(timezone.utc) + timedelta(hours=3)

    year = now.year
    month = now.month
    day = now.day

    # Ethiopian New Year is September 11, or September 12 in Gregorian
    # years immediately before a Gregorian leap year.
    new_year_day = 12 if (year + 1) % 4 == 0 else 11
    new_year = datetime(year, 9, new_year_day)

    if now.replace(tzinfo=None) < new_year:
        eth_year = year - 9
        previous_gregorian_year = year - 1
        previous_new_year_day = 12 if (year) % 4 == 0 else 11
        new_year = datetime(previous_gregorian_year, 9, previous_new_year_day)
    else:
        eth_year = year - 8

    days = (now.replace(tzinfo=None) - new_year).days
    eth_month = (days // 30) + 1
    eth_day = (days % 30) + 1

    months = {
        1: "መስከረም",
        2: "ጥቅምት",
        3: "ኅዳር",
        4: "ታኅሣሥ",
        5: "ጥር",
        6: "የካቲት",
        7: "መጋቢት",
        8: "ሚያዝያ",
        9: "ግንቦት",
        10: "ሰኔ",
        11: "ሐምሌ",
        12: "ነሐሴ",
        13: "ጳጉሜን"
    }

    # Ethiopia-time posting session
    hour = now.hour
    if 6 <= hour < 12:
        session = "ጠዋት | Morning"
    elif 12 <= hour < 14:
        session = "እኩለ ቀን | Midday"
    elif 14 <= hour < 18:
        session = "ከሰዓት | Afternoon"
    elif 18 <= hour < 21:
        session = "ማታ | Evening"
    else:
        session = "ሌሊት | Night"

    time_text = now.strftime("%I:%M %p")

    return (
        f"{months[eth_month]} {eth_day}, {eth_year}",
        session,
        time_text
    )

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

    eth_date, session, ethiopian_time = get_ethiopian_date_and_session()

    return (
        f"📅 <b>{eth_date} | {session}</b>\n"
        f"🕒 <b>{ethiopian_time}</b>\n"
        "⚽ <b>አጭር የስፖርት ዜና ለቤተሰቦቻችን</b>\n\n"
        + translated
        + "\n\n"
        "━━━━━━━━━━━━━━\n"
        "📢 <b>ሼር ያድርጉ፣ Like አትርሱ —❤️</b>\n"
        "❤️  🔥  👍  😂  😢\n"
        "💖 <b>እንወዳችኋለን!</b> ❤️"
    )
# =========================================================
# ADVERTISEMENT FILTER
# =========================================================

def is_advertisement(message):
    text = (message.message or "").lower()

    # Check message text
    ad_words = [
        ".apk",
        ".exe",
        "download apk",
        "download now",
        "betwinner",
        "linebet",
        "1xbet",
        "betting",
        "casino",
        "bonus",
        "promo code",
        "advertisement",
        "advertising"
    ]

    for word in ad_words:
        if word in text:
            return True

    # Check attached file name
    if message.file:
        filename = getattr(message.file, "name", None)

        if filename:
            filename = filename.lower()

            if filename.endswith((".apk", ".exe", ".msi", ".bat", ".scr")):
                return True

            for word in [
                "betwinner",
                "linebet",
                "1xbet",
                "casino"
            ]:
                if word in filename:
                    return True

    return False
# =========================================================
# PROCESS ONE MESSAGE
# =========================================================

async def process_message(
    user_client,
    bot_client,
    message,
    source_username,
    destination,
    post_count
):
    try:
        original_text = message.message or ""
        # -------------------------------------------------
        # BLOCK ADVERTISEMENTS
        # -------------------------------------------------

        if is_advertisement(message):
            print("🚫 ADVERTISEMENT BLOCKED")
            print("SOURCE:", source_username)
            print("TEXT:", original_text[:300])
            return True, False
        print("\n" + "=" * 60)
        print("📰 NEW NEWS")
        print("SOURCE:", source_username)
        print("MESSAGE ID:", message.id)
        print("TEXT:")
        print(original_text[:500])

        post = create_post(original_text)
        show_buttons = ((post_count + 1) % BUTTON_INTERVAL == 0)
        buttons = PUSH_BUTTONS if show_buttons else None

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
                    buttons=buttons,
                    force_document=False
                )

                print("✅ MEDIA POSTED TO", DESTINATION_CHANNEL)

                try:
                    os.remove(media)
                except Exception:
                    pass

                return True, True

            print("⚠ Media download failed")

        # -------------------------------------------------
        # TEXT ONLY
        # -------------------------------------------------

        if post:
            await bot_client.send_message(
                destination,
                post,
                parse_mode="html",
                buttons=buttons
            )

            print("✅ TEXT POSTED TO", DESTINATION_CHANNEL)
            return True, True

        print("⚠ Message contained no usable text")
        return True, False

    except Exception as e:
        print("❌ ERROR PROCESSING MESSAGE:", e)
        return False, False


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

        last_id = int(state.get(channel, 0))

        print("Last processed ID:", last_id)

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
        post_count = int(state.get("_successful_posts", 0))

        for message in messages:
            success, posted = await process_message(
                user_client,
                bot_client,
                message,
                username,
                post_count
            )

            if success:
                highest_successful_id = max(
                    highest_successful_id,
                    message.id
                )

                # Count only successfully published news posts.
                if posted:
                    post_count += 1
                    state["_successful_posts"] = post_count
                    if post_count % BUTTON_INTERVAL == 0:
                        print(f"🔘 Push buttons added to post #{post_count}")

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
        API_HASH,
        connection_retries=10,
        retry_delay=5,
        request_retries=10,
        auto_reconnect=True
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
