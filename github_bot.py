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
# FACEBOOK DESTINATIONS
# =========================================================
# These are the Facebook Pages that will receive the SAME final post
# that the bot publishes to the matching Telegram destination.
#
# Page URLs are recorded now. Facebook Page IDs and Page access tokens
# will be added securely through GitHub Secrets before live posting.

FACEBOOK_DESTINATIONS = {
    "@habeshasport": "https://web.facebook.com/ethiosportlive",
    "@arsenaletgunners": "https://web.facebook.com/profile.php?id=100070112416970",
    "@manunitedethiopia": "https://web.facebook.com/profile.php?id=100095014544008",
}


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

            minute = (
                int(match.group(2))
                if match.group(2)
                else 0
            )

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

            return (
                f"{eth_hour:02d}:"
                f"{eth_minute:02d} "
                f"Ethiopia time"
            )

        return pattern.sub(replace_time, text)

    text = convert_times_to_ethiopia(text)

    # =====================================================
    # FOOTBALL WORDS / PHRASES TO KEEP IN ENGLISH
    # =====================================================

    keep_words = [
        "Here we go",
        "Fulltime",
        "Full-time",
        "Match Week",
        "Assist",

        "Premier League",
        "Champions League",
        "Europa League",
        "Conference League",

        "Transfer",
        "Transfers",
        "Medical",
        "Agreement",
        "Talks",
        "Bid",
        "Deal",
        "Contract",
        "Loan",

        "Manchester City",
        "Manchester United",
        "Liverpool",
        "Arsenal",
        "Chelsea",
        "Tottenham",
        "Newcastle United",
        "Aston Villa",
        "West Ham United",
        "Crystal Palace",
        "Brighton",
        "Everton",
        "Nottingham Forest",
        "Brentford",
        "Fulham",
        "Bournemouth",
        "Wolverhampton Wanderers",
        "Wolves",
        "Leicester City",

        "Real Madrid",
        "Barcelona",
        "Bayern Munich",
        "Paris Saint-Germain",
        "PSG",
        "Inter Milan",
        "AC Milan",
        "Juventus",
        "Atletico Madrid",
        "Borussia Dortmund",
    ]

    protected = {}
    counter = 0

    keep_words = sorted(keep_words, key=len, reverse=True)

    for word in keep_words:

        pattern = re.compile(re.escape(word), re.IGNORECASE)

        def protect(match):
            nonlocal counter

            counter += 1

            key = f"FOOTBALL_KEEP_{counter}_X"

            protected[key] = match.group(0)

            return key

        text = pattern.sub(protect, text)

    # =====================================================
    # SPLIT NEWS INTO SENTENCES
    # =====================================================

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    translated_sentences = []

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        chunks = []

        if len(sentence) <= 900:
            chunks = [sentence]

        else:

            words = sentence.split()
            current = ""

            for word in words:

                if len(current) + len(word) + 1 > 850:

                    if current:
                        chunks.append(current.strip())

                    current = word

                else:

                    if current:
                        current += " " + word
                    else:
                        current = word

            if current:
                chunks.append(current.strip())

        # =================================================
        # GOOGLE TRANSLATE
        # =================================================

        for chunk in chunks:

            try:

                url = (
                    "https://translate.googleapis.com/"
                    "translate_a/single"
                    "?client=gtx"
                    "&sl=en"
                    "&tl=am"
                    "&dt=t"
                    "&q="
                    + urllib.parse.quote(chunk)
                )

                request = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"}
                )

                with urllib.request.urlopen(
                    request,
                    timeout=20
                ) as response:

                    data = response.read().decode("utf-8")

                result = json.loads(data)

                translated = ""

                for part in result[0]:

                    if part[0]:
                        translated += part[0]

                if translated:
                    translated_sentences.append(translated.strip())
                else:
                    translated_sentences.append(chunk)

            except Exception as e:

                print("⚠ Translation error:", e)
                translated_sentences.append(chunk)

    translated_text = " ".join(translated_sentences)

    # =====================================================
    # RESTORE ENGLISH FOOTBALL TERMS
    # =====================================================

    for key, original in protected.items():

        translated_text = translated_text.replace(
            key,
            original
        )

    translated_text = re.sub(r'\s+', ' ', translated_text)

    return translated_text.strip()


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

        original_text = (
            message.message or ""
        )

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

        buttons = (
            PUSH_BUTTONS
            if show_buttons
            else None
        )

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
