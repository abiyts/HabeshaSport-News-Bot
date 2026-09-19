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
    [
        Button.url(
            "Man City ሲቲ",
            "https://t.me/mancitynewset"
        ),
        Button.url(
            "Liverpool ሊቨርፑል",
            "https://t.me/liverpoolethiop"
        )
    ],

    [
        Button.url(
            "Arsenal አርሰናል",
            "https://t.me/arsenaletgunners"
        ),
        Button.url(
            "Man United Ethiopia",
            "https://t.me/manunitedethiopia"
        )
    ],

    [
        Button.url(
            "Chelsea ቼልሲ",
            "https://t.me/chelseafcet"
        ),
        Button.url(
            "Ethio Sport",
            "https://t.me/habeshasport"
        )
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
        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except Exception as e:
        print("⚠ Could not read state.json:", e)
        return {}


def save_state(state):
    try:
        with open(
            STATE_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                state,
                f,
                indent=4,
                ensure_ascii=False
            )

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
    text = re.sub(
        r'https?://\S+',
        '',
        text
    )

    # Remove Telegram links
    text = re.sub(
        r'(https?://)?t\.me/\S+',
        '',
        text
    )

    # Remove Telegram/channel usernames
    # Example: @FabrizioRomano
    text = re.sub(
        r'(?<!\w)@[A-Za-z0-9_]{3,}',
        '',
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r'\n\s*\n\s*\n+',
        '\n\n',
        text
    )

    return text.strip()


# =========================================================
# FOOTBALL TRANSLATION
# ENGLISH → AMHARIC
# =========================================================

def translate_to_amharic(text):

    if not text:
        return ""

    # -----------------------------------------------------
    # FOOTBALL WORDS / PHRASES TO KEEP IN ENGLISH
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # PROTECT IMPORTANT ENGLISH WORDS
    # -----------------------------------------------------

    protected = {}

    counter = 0

    # Longest phrases first
    keep_words = sorted(
        keep_words,
        key=len,
        reverse=True
    )

    for word in keep_words:

        pattern = re.compile(
            re.escape(word),
            re.IGNORECASE
        )

        def protect(match):

            nonlocal counter

            counter += 1

            key = (
                f"FOOTBALLKEEP{counter}X"
            )

            protected[key] = match.group(0)

            return key

        text = pattern.sub(
            protect,
            text
        )

    # -----------------------------------------------------
    # SPLIT LONG NEWS INTO SENTENCES
    # -----------------------------------------------------

    sentences = re.split(
        r'(?<=[.!?])\s+',
        text.strip()
    )

    translated_sentences = []

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        # Keep translation requests reasonably short
        chunks = []

        if len(sentence) <= 1000:

            chunks = [sentence]

        else:

            words = sentence.split()

            current = ""

            for word in words:

                if len(current) + len(word) + 1 > 900:

                    if current:
                        chunks.append(
                            current.strip()
                        )

                    current = word

                else:

                    if current:
                        current += " " + word
                    else:
                        current = word

            if current:
                chunks.append(
                    current.strip()
                )

        # -------------------------------------------------
        # TRANSLATE EACH SMALL SECTION
        # -------------------------------------------------

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
                    + urllib.parse.quote(
                        chunk
                    )
                )

                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent":
                        "Mozilla/5.0"
                    }
                )

                with urllib.request.urlopen(
                    request,
                    timeout=20
                ) as response:

                    data = (
                        response
                        .read()
                        .decode("utf-8")
                    )

                result = json.loads(data)

                translated = ""

                for part in result[0]:

                    if part[0]:
                        translated += part[0]

                if translated:

                    translated_sentences.append(
                        translated.strip()
                    )

                else:

                    translated_sentences.append(
                        chunk
                    )

            except Exception as e:

                print(
                    "⚠ Translation error:",
                    e
                )

                # Keep original sentence if
                # translation fails.
                translated_sentences.append(
                    chunk
                )

    translated_text = " ".join(
        translated_sentences
    )

    # -----------------------------------------------------
    # RESTORE ENGLISH FOOTBALL TERMS
    # -----------------------------------------------------

    for key, original in protected.items():

        translated_text = (
            translated_text.replace(
                key,
                original
            )
        )

    # -----------------------------------------------------
    # CLEAN UP
    # -----------------------------------------------------

    translated_text = re.sub(
        r'\s+',
        ' ',
        translated_text
    )

    return translated_text.strip()

# =========================================================
# ETHIOPIAN CALENDAR DATE + ETHIOPIA LOCAL TIME
# =========================================================

def get_ethiopian_date_and_session():

    # Ethiopia is UTC+3.
    # GitHub Actions normally runs in UTC, so we explicitly
    # convert UTC to Ethiopia time here.

    utc_now = datetime.now(timezone.utc)

    ethiopia_now = (
        utc_now + timedelta(hours=3)
    )

    # Remove timezone information for calendar calculations
    now = ethiopia_now.replace(tzinfo=None)

    year = now.year

    # Ethiopian New Year:
    # September 11 normally
    # September 12 when the following Gregorian year is leap

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

    days = (
        now - new_year
    ).days

    eth_month = (
        days // 30
    ) + 1

    eth_day = (
        days % 30
    ) + 1

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
    # ETHIOPIA LOCAL TIME
    # =====================================================

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

    # Ethiopia local clock
    # Example: 02:30 PM

    time_text = now.strftime(
        "%I:%M %p"
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

    translated = translate_to_amharic(
        text
    )

    if not translated:
        translated = text

    translated = html.escape(
        translated
    )

    (
        eth_date,
        session,
        ethiopian_time
    ) = get_ethiopian_date_and_session()

    return (

        f"📅 <b>{eth_date} | "
        f"{session}</b>\n"

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

    text = (
        message.message or ""
    ).lower()

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

        # -------------------------------------------------
        # BLOCK ADVERTISEMENTS
        # -------------------------------------------------

        if is_advertisement(message):

            print(
                "🚫 ADVERTISEMENT BLOCKED"
            )

            print(
                "SOURCE:",
                source_username
            )

            print(
                "TEXT:",
                original_text[:300]
            )

            # Advertisement is considered processed,
            # but it is NOT counted as a successful post.

            return True, False

        print(
            "\n" + "=" * 60
        )

        print("📰 NEW NEWS")

        print(
            "SOURCE:",
            source_username
        )

        print(
            "DESTINATION:",
            destination
        )

        print(
            "MESSAGE ID:",
            message.id
        )

        print("TEXT:")

        print(
            original_text[:500]
        )

        post = create_post(
            original_text
        )

        # Buttons every 10 successful posts

        show_buttons = (
            (post_count + 1)
            % BUTTON_INTERVAL == 0
        )

        buttons = (
            PUSH_BUTTONS
            if show_buttons
            else None
        )

        # -------------------------------------------------
        # MEDIA
        # -------------------------------------------------

        if message.media:

            print(
                "📷 Media detected"
            )

            print(
                "⬇ Downloading media..."
            )

            media = (
                await user_client.download_media(
                    message
                )
            )

            if media:

                await bot_client.send_file(

                    destination,

                    media,

                    caption=post,

                    parse_mode="html",

                    buttons=buttons,

                    force_document=False
                )

                print(
                    "✅ MEDIA POSTED TO",
                    destination
                )

                try:

                    os.remove(media)

                except Exception:
                    pass

                return True, True

            print(
                "⚠ Media download failed"
            )

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

            print(
                "✅ TEXT POSTED TO",
                destination
            )

            return True, True

        print(
            "⚠ Message contained no usable text"
        )

        return True, False

    except Exception as e:

        print(
            "❌ ERROR PROCESSING MESSAGE:",
            e
        )

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

        entity = await user_client.get_entity(
            channel
        )

        username = getattr(
            entity,
            "username",
            channel
        )

        print(
            "\n" + "-" * 60
        )

        print(
            "🔎 Checking:",
            username
        )

        print(
            "📢 Destination:",
            destination
        )

        # =================================================
        # IMPORTANT SAFETY CHECK
        # =================================================
        #
        # If this is a brand-new source and it does not
        # exist in state.json, DO NOT process its old
        # messages.
        #
        # We start from the latest message and wait for
        # NEW messages only.
        #
        # This prevents a new source from flooding the
        # destination channel with old posts.
        # =================================================

        if channel not in state:

            print(
                "🆕 NEW SOURCE DETECTED"
            )

            print(
                "🛡 Initializing safely..."
            )

            latest_messages = (
                await user_client.get_messages(
                    entity,
                    limit=1
                )
            )

            if latest_messages:

                latest_id = (
                    latest_messages[0].id
                )

                state[channel] = latest_id

                save_state(state)

                print(
                    "✅ Starting from latest message ID:",
                    latest_id
                )

            else:

                state[channel] = 0

                save_state(state)

                print(
                    "ℹ Channel has no messages"
                )

            print(
                "⏳ Waiting for NEW messages only."
            )

            return

        # =================================================
        # EXISTING SOURCE
        # =================================================

        last_id = int(
            state.get(
                channel,
                0
            )
        )

        print(
            "Last processed ID:",
            last_id
        )

        messages = []

        async for message in user_client.iter_messages(

            entity,

            min_id=last_id,

            reverse=True

        ):

            messages.append(
                message
            )

        if not messages:

            print(
                "ℹ No new messages"
            )

            return

        print(
            f"📥 Found {len(messages)} "
            f"new message(s)"
        )

        highest_successful_id = (
            last_id
        )

        post_count = int(
            state.get(
                "_successful_posts",
                0
            )
        )

        for message in messages:

            success, posted = (
                await process_message(

                    user_client,

                    bot_client,

                    message,

                    username,

                    destination,

                    post_count
                )
            )

            if success:

                highest_successful_id = max(

                    highest_successful_id,

                    message.id
                )

                # Count only successfully
                # published news posts.

                if posted:

                    post_count += 1

                    state[
                        "_successful_posts"
                    ] = post_count

                    if (
                        post_count
                        % BUTTON_INTERVAL == 0
                    ):

                        print(
                            f"🔘 Push buttons "
                            f"added to post "
                            f"#{post_count}"
                        )

                await asyncio.sleep(2)

            else:

                print(
                    "⚠ Message failed."
                )

                print(
                    "⚠ State will NOT move "
                    "past this message."
                )

                break

        # =================================================
        # SAVE STATE
        # =================================================

        if (
            highest_successful_id
            > last_id
        ):

            state[channel] = (
                highest_successful_id
            )

            save_state(state)

            print(
                "✅ Updated last ID:",
                highest_successful_id
            )

    except Exception as e:

        print(
            "❌ CHANNEL ERROR:",
            channel
        )

        print(e)


# =========================================================
# MAIN
# =========================================================

async def main():

    print(
        "\n" + "=" * 60
    )

    print(
        "🚀 HABESHA SPORT GITHUB BOT"
    )

    print(
        "=" * 60
    )

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

        # =================================================
        # CONNECT USER ACCOUNT
        # =================================================

        print(
            "\n🔐 Connecting Telegram user..."
        )

        await user_client.start()

        print(
            "✅ Telegram user connected"
        )

        # =================================================
        # CONNECT BOT
        # =================================================

        print(
            "\n🤖 Connecting Telegram bot..."
        )

        await bot_client.start(
            bot_token=BOT_TOKEN
        )

        print(
            "✅ Telegram bot connected"
        )

        # =================================================
        # START SOURCES
        # =================================================

        print(
            "\n🔎 Checking source channels..."
        )

        print(
            f"📊 Total sources: "
            f"{len(SOURCE_CHANNELS)}"
        )

        # =================================================
        # CHECK EVERY SOURCE
        # =================================================

        for channel in SOURCE_CHANNELS:

            destination = (
                SOURCE_ROUTES.get(
                    channel,
                    DEFAULT_DESTINATION
                )
            )

            await check_channel(

                user_client,

                bot_client,

                channel,

                destination,

                state
            )

        print(
            "\n" + "=" * 60
        )

        print(
            "✅ CHECK COMPLETE"
        )

        print(
            "=" * 60
        )

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
