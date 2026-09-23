import os
import re
import json
import html
import urllib.parse
import urllib.request
import asyncio
from datetime import datetime, timezone, timedelta

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
# DEFAULT DESTINATION
# =========================================================

DEFAULT_DESTINATION = "@habeshasport"


# =========================================================
# CLUB SOURCE → CLUB DESTINATION
# =========================================================

SOURCE_ROUTES = {
    "@arsenal_gunners_london": "@arsenaletgunners",
    "@Arsenalc": "@arsenaletgunners",
    "@gunnersfooty": "@arsenaletgunners",
    "@GUNNERS": "@arsenaletgunners",

    "@LiverpoolFCNews": "@liverpoolethiop",
    "@liverpool": "@liverpoolethiop",
    "@lfconline": "@liverpoolethiop",

    "@Manchester_City": "@mancitynewset",
    "@manchester_city_cf": "@mancitynewset",
    "@mancity247": "@mancitynewset",

    "@Chelsea_fc_worldwide": "@chelseafcet",
    "@chelseafcnews01": "@chelseafcet",
    "@chelseaanalysis": "@chelseafcet",
    "@chelseasunsport": "@chelseafcet",

    "@ManchesterUnited": "@manunitedethiopia",
    "@Empire_MU": "@manunitedethiopia",
    "@manchester_united_uk": "@manunitedethiopia",
    "@manchesterunitedsunsport": "@manunitedethiopia",
    "@ZENA_ARSENAL": "@arsenaletgunners",
    "@ETHIO_ARSENAL": "@arsenaletgunners",
    "@Manchester_Unitedfanns": "@manunitedethiopia",
    "@man_united_ethio_fan": "@manunitedethiopia",

}


# =========================================================
# GENERAL FOOTBALL SOURCES → HABESHA SPORT
# =========================================================

GENERAL_SOURCES = [
    "@br_football_news",
    "@Football433_uk",
    "@Espnfc_news",
    "@Premier_League_Update",
    "@Espn_Football_News_UK",
    "@squawka_football_news",
    "@mainfootball",
    "@transfermarkt_off",
    "@mtransfers",
    "@sport_hub_football",
    "@transfer_news_football",
]


# =========================================================
# ALL SOURCE CHANNELS
# =========================================================

SOURCE_CHANNELS = GENERAL_SOURCES + list(SOURCE_ROUTES.keys())


# =========================================================
# FACEBOOK DESTINATIONS
# =========================================================

FACEBOOK_GRAPH_VERSION = "v26.0"

FACEBOOK_DESTINATIONS = {
    DEFAULT_DESTINATION: {
        "name": "Ethio Sport ኢትዮ ስፖርት",
        "page_id_env": "FB_ETHIO_SPORT_PAGE_ID",
        "token_env": "FB_ETHIO_SPORT_PAGE_TOKEN",
    },
    "@arsenaletgunners": {
        "name": "Arsenal",
        "page_id_env": "FB_ARSENAL_PAGE_ID",
        "token_env": "FB_ARSENAL_PAGE_TOKEN",
    },
}


def facebook_config(destination):
    config = FACEBOOK_DESTINATIONS.get(destination)

    if not config:
        return None

    page_id = os.environ.get(config["page_id_env"], "").strip()
    token = os.environ.get(config["token_env"], "").strip()

    if not page_id or not token:
        print(
            "ℹ Facebook is not configured for",
            destination,
            "- Telegram will continue normally."
        )
        return None

    return config, page_id, token


def facebook_plain_text(post):
    if not post:
        return ""

    text = re.sub(r"<[^>]+>", "", post)
    text = html.unescape(text)
    return text.strip()


def facebook_request(endpoint, fields, files=None):
    boundary = "----HabeshaSportBoundary"
    body = bytearray()

    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
        )
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    if files:
        for key, file_info in files.items():
            filename, content_type, data = file_info
            body.extend(f"--{boundary}\r\n".encode())
            body.extend(
                (
                    f'Content-Disposition: form-data; '
                    f'name="{key}"; filename="{filename}"\r\n'
                ).encode()
            )
            body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
            body.extend(data)
            body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode())

    request = urllib.request.Request(
        endpoint,
        data=bytes(body),
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Mozilla/5.0",
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def facebook_post_text(destination, post):
    config = facebook_config(destination)

    if not config:
        return False

    page_config, page_id, token = config
    message = facebook_plain_text(post)

    if not message:
        return False

    endpoint = (
        f"https://graph.facebook.com/"
        f"{FACEBOOK_GRAPH_VERSION}/{page_id}/feed"
    )

    try:
        result = facebook_request(
            endpoint,
            {
                "message": message,
                "access_token": token,
            },
        )

        if result.get("id"):
            print(
                "✅ FACEBOOK TEXT POSTED TO",
                page_config["name"]
            )
            return True

        print("⚠ Facebook returned no post ID:", result)
        return False

    except Exception as e:
        print("⚠ FACEBOOK ERROR:", e)
        return False


def facebook_post_media(destination, media_path, post):
    config = facebook_config(destination)

    if not config:
        return False

    page_config, page_id, token = config

    try:
        with open(media_path, "rb") as f:
            data = f.read()

        filename = os.path.basename(media_path)
        lower_name = filename.lower()

        if lower_name.endswith((".mp4", ".mov", ".m4v", ".webm")):
            endpoint = (
                f"https://graph.facebook.com/"
                f"{FACEBOOK_GRAPH_VERSION}/{page_id}/videos"
            )
            content_type = "video/mp4"
            file_field = "source"
            text_field = "description"
        elif lower_name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
            endpoint = (
                f"https://graph.facebook.com/"
                f"{FACEBOOK_GRAPH_VERSION}/{page_id}/photos"
            )
            content_type = "image/jpeg"
            file_field = "source"
            text_field = "caption"
        else:
            print("ℹ Facebook media type not supported:", filename)
            return False

        fields = {
            "access_token": token,
            "published": "true",
            text_field: facebook_plain_text(post),
        }

        result = facebook_request(
            endpoint,
            fields,
            {
                file_field: (
                    filename,
                    content_type,
                    data,
                )
            },
        )

        if result.get("id") or result.get("post_id"):
            print(
                "✅ FACEBOOK MEDIA POSTED TO",
                page_config["name"]
            )
            return True

        print("⚠ Facebook media returned:", result)
        return False

    except Exception as e:
        print("⚠ FACEBOOK MEDIA ERROR:", e)
        return False


# =========================================================
# PUSH BUTTONS
# =========================================================

BUTTON_INTERVAL = 10

PUSH_BUTTONS = [
    [
        Button.url("Man City ሲቲ", "https://t.me/mancitynewset"),
        Button.url("Liverpool ሊቨርፑል", "https://t.me/liverpoolethiop")
    ],
    [
        Button.url("Arsenal አርሰናል", "https://t.me/arsenaletgunners"),
        Button.url("Man United Ethiopia", "https://t.me/manunitedethiopia")
    ],
    [
        Button.url("Chelsea ቼልሲ", "https://t.me/chelseafcet"),
        Button.url("Ethio Sport", "https://t.me/habeshasport")
    ],
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
    text = re.sub(r'(?<!\w)@[A-Za-z0-9_]{3,}', '', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    return text.strip()


# =========================================================
# FOOTBALL TRANSLATION
# ENGLISH → AMHARIC
# + TIME ZONE CONVERSION → ETHIOPIA
# =========================================================

def translate_to_amharic(text):

    if not text:
        return ""

    # =====================================================
    # CONVERT TIMES TO ETHIOPIA TIME
    # =====================================================

    def convert_times_to_ethiopia(text):

        timezone_offsets = {
            "UTC": 0,
            "GMT": 0,
            "EAT": 3,
            "WAT": 1,
            "CAT": 2,
            "CET": 1,
            "CEST": 2,
            "BST": 1,
            "IST": 5.5,
        }

        pattern = re.compile(
            r'\b'
            r'(\d{1,2})'
            r'(?::(\d{2}))?'
            r'\s*'
            r'(AM|PM|am|pm)?'
            r'\s*'
            r'(UTC|GMT|EAT|WAT|CAT|CET|CEST|BST|IST)'
            r'\b',
            re.IGNORECASE
        )

        def replace_time(match):

            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3)
            zone = match.group(4).upper()

            if ampm:
                ampm = ampm.upper()

                if ampm == "PM" and hour != 12:
                    hour += 12

                elif ampm == "AM" and hour == 12:
                    hour = 0

            source_offset = timezone_offsets.get(zone, 0)
            ethiopia_offset = 3

            total_minutes = (
                hour * 60
                + minute
                + (ethiopia_offset - source_offset) * 60
            )

            total_minutes %= (24 * 60)

            eth_hour = total_minutes // 60
            eth_minute = total_minutes % 60

            return f"{eth_hour:02d}:{eth_minute:02d} Ethiopia time"

        return pattern.sub(replace_time, text)

    text = convert_times_to_ethiopia(text)

    # =====================================================
    # AI FOOTBALL TRANSLATION
    # =====================================================

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()

    if not api_key:
        print("⚠ OPENAI_API_KEY is not configured")
        return text

    system_prompt = """
You are the professional Amharic football-news translator for an Ethiopian
football news channel.

Translate the supplied English football news into NATURAL, CLEAR,
PROFESSIONAL Ethiopian Amharic.

IMPORTANT:
1. Translate the MEANING and football context, not each English word literally.
2. Never produce strange literal translations.
3. Make the result sound like a real Ethiopian sports-news post.
4. Keep player names, club names, competition names, abbreviations and
   well-known football names exactly as written when appropriate.
5. Never translate football abbreviations such as LFC, AFC, UEFA, FIFA, EPL.
6. Never interpret club abbreviations as ordinary English words.
   Example: "LFC" means Liverpool Football Club, NOT food.
7. "according to LFC" should naturally become:
   "እንደ LFC ገለጻ"
8. "backroom staff" / "back staff" in a football technical context should
   normally become:
   "የቴክኒክ ቡድን አባላት"
9. General "staff" may become:
   "የሰራተኛ ቡድን"
   when that is the natural meaning.
10. "agreement has been reached" should naturally become:
    "ስምምነቱ ተደርሷል"
11. "set to be officially announced" should naturally become:
    "በይፋ እንዲገለጽ በዝግጅት ላይ ይገኛል"
12. Preserve football terms such as contract, agreement, transfer, deal,
    medical, bid, loan, Here we go, Assist, Fulltime when keeping the
    English term makes the Ethiopian football-news style clearer.
13. Do not invent facts, names, dates, quotes or information that is not
    present in the original.
14. Keep the original meaning and level of certainty.
15. Keep emojis when they are part of the original news.
16. Do not add explanations, notes, headings or comments.
17. Return ONLY the final Amharic translation.
18. Keep the translation concise and suitable for Telegram.
19. If a source is mentioned, preserve it naturally. For example:
    "according to sources" -> "እንደ ምንጮች ገለጻ"
    "according to LFC sources" -> "እንደ LFC ምንጮች ገለጻ"
"""

    payload = {
        "model": "gpt-5",
        "input": [
            {
                "role": "system",
                "content": system_prompt.strip()
            },
            {
                "role": "user",
                "content": text.strip()
            }
        ],
        "max_output_tokens": 1200
    }

    try:

        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "HabeshaSport-News-Bot/1.0"
            },
            method="POST"
        )

        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        translated_parts = []

        for item in data.get("output", []):

            for content in item.get("content", []):

                if content.get("type") == "output_text":

                    value = content.get("text", "")

                    if value:
                        translated_parts.append(value)

        translated = "\n".join(
            translated_parts
        ).strip()

        if not translated:
            print("⚠ OpenAI returned no translation")
            return text

        return translated

    except urllib.error.HTTPError as e:

        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            error_body = ""

        print(
            "⚠ OpenAI translation HTTP error:",
            e.code,
            error_body[:500]
        )

        return text

    except Exception as e:

        print(
            "⚠ OpenAI translation error:",
            e
        )

        return text

# =========================================================
# ETHIOPIAN CALENDAR DATE + ETHIOPIAN CLOCK
# =========================================================

def get_ethiopian_date_and_session():

    utc_now = datetime.now(timezone.utc)

    ethiopia_now = (
        utc_now + timedelta(hours=3)
    )

    now = ethiopia_now.replace(tzinfo=None)

    year = now.year

    new_year_day = (
        12
        if (year + 1) % 4 == 0
        else 11
    )

    new_year = datetime(
        year,
        9,
        new_year_day
    )

    if now < new_year:

        eth_year = year - 9

        previous_gregorian_year = year - 1

        previous_new_year_day = (
            12
            if year % 4 == 0
            else 11
        )

        new_year = datetime(
            previous_gregorian_year,
            9,
            previous_new_year_day
        )

    else:

        eth_year = year - 8

    days = (now - new_year).days

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

    # =====================================================
    # ETHIOPIAN CLOCK
    # =====================================================

    if 6 <= now.hour < 12:
        session = "ጠዋት | Morning"

    elif 12 <= now.hour < 14:
        session = "እኩለ ቀን | Midday"

    elif 14 <= now.hour < 18:
        session = "ከሰዓት | Afternoon"

    elif 18 <= now.hour < 21:
        session = "ማታ | Evening"

    else:
        session = "ሌሊት | Night"

    ethiopian_hour = (
        (now.hour - 6) % 12
    )

    if ethiopian_hour == 0:
        ethiopian_hour = 12

    time_text = (
        f"{ethiopian_hour:02d}:"
        f"{now.minute:02d}"
    )

    return (
        f"{months[eth_month]} "
        f"{eth_day}, "
        f"{eth_year}",
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

    (
        eth_date,
        session,
        ethiopian_time
    ) = get_ethiopian_date_and_session()

    return (
        f"📅 <b>{eth_date} | {session}</b>\n"
        f"🕒 <b>{ethiopian_time}</b>\n"
        "⚽ <b>አጭር የስፖርት ዜና "
        "ለቤተሰቦቻችን</b>\n\n"
        + translated
        + "\n\n"
        "━━━━━━━━━━━━━━\n"
        "📢 <b>ሼር ያድርጉ፣ "
        "Like አትርሱ —❤️</b>\n"
        "❤️  🔥  👍  😂  😢\n"
        "💖 <b>እንወዳችኋለን!</b> ❤️"
    )


# =========================================================
# ADVERTISEMENT FILTER
# =========================================================

def is_advertisement(message):

    text = (message.message or "").lower()

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

    if message.file:

        filename = getattr(
            message.file,
            "name",
            None
        )

        if filename:

            filename = filename.lower()

            if filename.endswith(
                (
                    ".apk",
                    ".exe",
                    ".msi",
                    ".bat",
                    ".scr"
                )
            ):
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

        if is_advertisement(message):
            print("🚫 ADVERTISEMENT BLOCKED")
            print("SOURCE:", source_username)
            print("TEXT:", original_text[:300])
            return True, False

        print("\n" + "=" * 60)
        print("📰 NEW NEWS")
        print("SOURCE:", source_username)
        print("DESTINATION:", destination)
        print("MESSAGE ID:", message.id)
        print("TEXT:")
        print(original_text[:500])

        post = create_post(original_text)

        show_buttons = (
            (post_count + 1) % BUTTON_INTERVAL == 0
        )

        buttons = PUSH_BUTTONS if show_buttons else None

        media = None

        # -------------------------------------------------
        # TELEGRAM POST
        # -------------------------------------------------

        if message.media:
            print("📷 Media detected")
            print("⬇ Downloading media...")

            media = await user_client.download_media(message)

            if media:
                await bot_client.send_file(
                    destination,
                    media,
                    caption=post,
                    parse_mode="html",
                    buttons=buttons,
                    force_document=False
                )

                print("✅ MEDIA POSTED TO", destination)

                # Facebook is attempted only after Telegram succeeds.
                # Facebook failure does NOT fail the Telegram message.
                facebook_post_media(
                    destination,
                    media,
                    post
                )

                try:
                    os.remove(media)
                except Exception:
                    pass

                return True, True

            print("⚠ Media download failed")

        if post:
            await bot_client.send_message(
                destination,
                post,
                parse_mode="html",
                buttons=buttons
            )

            print("✅ TEXT POSTED TO", destination)

            # Facebook is attempted only after Telegram succeeds.
            facebook_post_text(
                destination,
                post
            )

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
    destination,
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
        print("📢 Destination:", destination)

        if channel not in state:

            print("🆕 NEW SOURCE DETECTED")
            print("🛡 Initializing safely...")

            latest_messages = await user_client.get_messages(
                entity,
                limit=1
            )

            if latest_messages:

                latest_id = latest_messages[0].id

                state[channel] = latest_id

                save_state(state)

                print(
                    "✅ Starting from latest message ID:",
                    latest_id
                )

            else:

                state[channel] = 0
                save_state(state)

                print("ℹ Channel has no messages")

            print("⏳ Waiting for NEW messages only.")

            return

        last_id = int(
            state.get(
                channel,
                0
            )
        )

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

        print(
            f"📥 Found {len(messages)} new message(s)"
        )

        highest_successful_id = last_id

        post_count = int(
            state.get(
                "_successful_posts",
                0
            )
        )

        for message in messages:

            success, posted = await process_message(
                user_client,
                bot_client,
                message,
                username,
                destination,
                post_count
            )

            if success:

                highest_successful_id = max(
                    highest_successful_id,
                    message.id
                )

                if posted:

                    post_count += 1

                    state["_successful_posts"] = post_count

                    if (
                        post_count
                        % BUTTON_INTERVAL
                        == 0
                    ):

                        print(
                            f"🔘 Push buttons added "
                            f"to post #{post_count}"
                        )

                await asyncio.sleep(2)

            else:

                print("⚠ Message failed.")
                print(
                    "⚠ State will NOT move past this message."
                )

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

        await bot_client.start(
            bot_token=BOT_TOKEN
        )

        print("✅ Telegram bot connected")

        print("\n🔎 Checking source channels...")

        print(
            f"📊 Total sources: "
            f"{len(SOURCE_CHANNELS)}"
        )

        for channel in SOURCE_CHANNELS:

            destination = SOURCE_ROUTES.get(
                channel,
                DEFAULT_DESTINATION
            )

            await check_channel(
                user_client,
                bot_client,
                channel,
                destination,
                state
            )

        print("\n" + "=" * 60)
        print("✅ CHECK COMPLETE")
        print("=" * 60)

    finally:

        await bot_client.disconnect()
        await user_client.disconnect()

        print(
            "\n🔌 Telegram connections closed"
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
