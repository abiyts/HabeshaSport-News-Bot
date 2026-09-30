```python
import os
import re
import json
import html
import urllib.parse
import urllib.request
import urllib.error
import asyncio
from datetime import datetime, timezone, timedelta

from telethon import TelegramClient
from telethon import Button
from telethon.sessions import StringSession


# =========================================================
# TELEGRAM SETTINGS
# =========================================================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
USER_SESSION = os.environ["USER_SESSION"]

BOT_SCHEDULE = os.environ.get("BOT_SCHEDULE", "").strip()

DEFAULT_DESTINATION = "@habeshasport"


# =========================================================
# SOURCE ROUTES
# =========================================================

SOURCE_ROUTES = {

    # =========================
    # ARSENAL
    # =========================

    "@YEGNA_ARSENAL_ETH": "@arsenaletgunners",
    "@arsenal_london": "@arsenaletgunners",
    "@Arsenalc": "@arsenaletgunners",
    "@gunnersfooty": "@arsenaletgunners",
    "@GUNNERS": "@arsenaletgunners",
    "@ZENA_ARSENAL": "@arsenaletgunners",
    "@ETHIO_ARSENAL": "@arsenaletgunners",

    # =========================
    # LIVERPOOL
    # =========================

    "@LiverpoolFCNews": "@liverpoolethiop",
    "@liverpool": "@liverpoolethiop",
    "@lfconline": "@liverpoolethiop",

    # =========================
    # MAN CITY
    # =========================

    "@Manchester_City": "@mancitynewset",
    "@manchester_city_cf": "@mancitynewset",
    "@mancity247": "@mancitynewset",

    # =========================
    # CHELSEA
    # =========================

    "@Chelsea_fc_worldwide": "@chelseafcet",
    "@chelseafcnews01": "@chelseafcet",
    "@chelseaanalysis": "@chelseafcet",
    "@chelseasunsport": "@chelseafcet",

    "@EthioZena_Chelsea": "@chelseafcet",
    "@ETHIO_CHELSEA": "@chelseafcet",

    # =========================
    # MAN UNITED
    # =========================

    "@ManchesterUnited": "@manunitedethiopia",
    "@Empire_MU": "@manunitedethiopia",
    "@manchester_united_uk": "@manunitedethiopia",
    "@manchesterunitedsunsport": "@manunitedethiopia",
    "@Manchester_Unitedfanns": "@manunitedethiopia",
    "@man_united_ethio_fan": "@manunitedethiopia",

    # =========================
    # PREMIER LEAGUE
    # =========================

    "@Premier_League_News_TG": "@ethplg",
}


# =========================================================
# GENERAL SOURCES
# =========================================================

GENERAL_SOURCES = [
    "@sky_sports_world",
    "@Espnfc_news",
    "@EthioEpl",
]


SOURCE_CHANNELS = (
    GENERAL_SOURCES
    + list(SOURCE_ROUTES.keys())
)


# =========================================================
# SCHEDULE GROUPS
#
# Existing groups remain unchanged.
#
# Premier League gets its own additional run at:
#
# 6,12,18,24,30,36,42,48,54
# =========================================================

SCHEDULE_GROUPS = {

    # GENERAL
    "0,6,12,18,24,30,36,42,48,54 * * * *": [
        "@sky_sports_world",
        "@Espnfc_news",
        "@EthioEpl",
    ],

    # ARSENAL
    "1,7,13,19,25,31,37,43,49,55 * * * *": [
        "@arsenal_london",
        "@Arsenalc",
        "@gunnersfooty",
        "@GUNNERS",
        "@ZENA_ARSENAL",
        "@ETHIO_ARSENAL",
        "@YEGNA_ARSENAL_ETH",
    ],

    # LIVERPOOL
    "2,8,14,20,26,32,38,44,50,56 * * * *": [
        "@LiverpoolFCNews",
        "@liverpool",
        "@lfconline",
    ],

    # MAN CITY
    "3,9,15,21,27,33,39,45,51,57 * * * *": [
        "@Manchester_City",
        "@manchester_city_cf",
        "@mancity247",
    ],

    # CHELSEA
    "4,10,16,22,28,34,40,46,52,58 * * * *": [
        "@Chelsea_fc_worldwide",
        "@chelseafcnews01",
        "@chelseaanalysis",
        "@chelseasunsport",
        "@EthioZena_Chelsea",
        "@ETHIO_CHELSEA",
    ],

    # MAN UNITED
    "5,11,17,23,29,35,41,47,53,59 * * * *": [
        "@ManchesterUnited",
        "@Empire_MU",
        "@manchester_united_uk",
        "@manchesterunitedsunsport",
        "@Manchester_Unitedfanns",
        "@man_united_ethio_fan",
    ],

    # PREMIER LEAGUE
    "6,12,18,24,30,36,42,48,54 * * * *": [
        "@Premier_League_News_TG",
    ],
}


# =========================================================
# FACEBOOK SETTINGS
# =========================================================

FACEBOOK_GRAPH_VERSION = "v26.0"


FACEBOOK_DESTINATIONS = {

    "@habeshasport": (
        "FB_ETHIO_SPORT_PAGE_ID",
        "FB_ETHIO_SPORT_PAGE_TOKEN",
    ),

    "@arsenaletgunners": (
        "FB_ARSENAL_PAGE_ID",
        "FB_ARSENAL_PAGE_TOKEN",
    ),

    # Premier League Facebook can be added later.
}


# =========================================================
# BUTTONS
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
        ),
    ],

    [
        Button.url(
            "Arsenal አርሰናል",
            "https://t.me/arsenaletgunners"
        ),
        Button.url(
            "Man United",
            "https://t.me/manunitedethiopia"
        ),
    ],

    [
        Button.url(
            "Chelsea ቼልሲ",
            "https://t.me/chelseafcet"
        ),
        Button.url(
            "Ethio Sport",
            "https://t.me/habeshasport"
        ),
    ],
]


# =========================================================
# STATE
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

            data = json.load(f)

        if isinstance(data, dict):
            return data

    except Exception as e:

        print(
            f"⚠️ Could not load state.json: {e}"
        )

    return {}


def save_state(state):

    try:

        temp_file = STATE_FILE + ".tmp"

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                state,
                f,
                ensure_ascii=False,
                indent=2
            )

        os.replace(
            temp_file,
            STATE_FILE
        )

    except Exception as e:

        print(
            f"⚠️ Could not save state: {e}"
        )


# =========================================================
# LINK / HANDLE REMOVAL
# =========================================================

def remove_links(text):

    if not text:
        return ""

    text = re.sub(
        r'https?://\S+',
        '',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'(?:https?://)?t\.me/\S+',
        '',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'(?<!\w)@[A-Za-z0-9_]{3,}',
        '',
        text
    )

    text = re.sub(
        r'\n\s*\n\s*\n+',
        '\n\n',
        text
    )

    return text.strip()


# =========================================================
# AD / SPAM FILTER
# =========================================================

AD_WORDS = {

    # promotion
    "promo",
    "#promo",
    "promocode",
    "promo code",
    "promotion",
    "promotional",
    "advertisement",
    "advertising",
    "advertise",
    "sponsored",
    "sponsor",
    "special offer",
    "limited offer",
    "discount",
    "buy now",
    "order now",
    "subscribe now",
    "join now",
    "click here",

    # betting / gambling
    "betting",
    "sportsbook",
    "casino",
    "jackpot",
    "bet now",
    "place your bet",
    "odds",
    "1xbet",
    "bet365",
    "stake.com",
    "parimatch",

    # apps / downloads
    ".apk",
    ".exe",
    "apk",
    "download app",
    "download now",
    "install app",

    # money scams / marketing
    "make money",
    "earn money",
    "free money",
    "investment opportunity",
    "crypto giveaway",
    "giveaway",

    # adult / spam
    "onlyfans",
    "xxx",
}


AD_EXTENSIONS = (
    ".apk",
    ".exe",
    ".msi",
    ".dmg",
)


def is_advertisement(message):

    try:

        text = (
            getattr(
                message,
                "message",
                ""
            )
            or ""
        )

        lower = text.lower().strip()

        if lower in {
            "#promo",
            "promo",
            "advertisement",
            "ad",
        }:

            return True

        for word in AD_WORDS:

            if word in lower:
                return True

        file_name = ""

        if getattr(
            message,
            "file",
            None
        ):

            file_name = (
                getattr(
                    message.file,
                    "name",
                    ""
                )
                or ""
            ).lower()

        for extension in AD_EXTENSIONS:

            if (
                extension in lower
                or extension in file_name
            ):

                return True

        return False

    except Exception as e:

        print(
            f"⚠️ Advertisement filter error: {e}"
        )

        return False


# =========================================================
# ETHIOPIAN DATE / TIME
# =========================================================

def get_ethiopian_date_and_session():

    now_utc = datetime.now(
        timezone.utc
    )

    ethiopia = timezone(
        timedelta(hours=3)
    )

    now = now_utc.astimezone(
        ethiopia
    )

    hour = now.hour

    if 5 <= hour < 11:

        session = "ጠዋት"

    elif 11 <= hour < 14:

        session = "እኩለ ቀን"

    elif 14 <= hour < 18:

        session = "ከሰዓት"

    elif 18 <= hour < 23:

        session = "ማታ"

    else:

        session = "ሌሊት"


    gy = now.year
    gm = now.month
    gd = now.day


    if gm < 9:

        ey = gy - 8

    else:

        ey = gy - 7


    if gm > 9 or (
        gm == 9
        and gd >= 12
    ):

        eth_month = gm - 8

        if eth_month == 1:

            eth_day = gd - 11

        else:

            eth_day = gd - 10

    else:

        eth_month = gm + 4

        if gm == 1:

            eth_day = gd + 21

        else:

            eth_day = gd + 20


    if eth_day <= 0:

        eth_day = 1


    time_string = now.strftime(
        "%I:%M %p"
    )


    return (
        f"{ey}-{eth_month:02d}-{eth_day:02d}",
        time_string,
        session
    )


# =========================================================
# NLLB TRANSLATION
# =========================================================

NLLB_MODEL_NAME = os.environ.get(
    "NLLB_MODEL_NAME",
    "dsfsi/nllb_200_distilled_600m-eng-amh"
).strip()


_nllb_tokenizer = None
_nllb_model = None
_nllb_device = None


def load_nllb_model():

    global _nllb_tokenizer
    global _nllb_model
    global _nllb_device


    if (
        _nllb_tokenizer is not None
        and _nllb_model is not None
    ):

        return (
            _nllb_tokenizer,
            _nllb_model,
            _nllb_device
        )


    print(
        "🔄 Loading NLLB translation model..."
    )


    from transformers import (
        AutoTokenizer,
        AutoModelForSeq2SeqLM
    )

    import torch


    _nllb_device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )


    print(
        f"🌐 NLLB model: "
        f"{NLLB_MODEL_NAME}"
    )


    print(
        f"🖥️ Translation device: "
        f"{_nllb_device}"
    )


    _nllb_tokenizer = (
        AutoTokenizer.from_pretrained(
            NLLB_MODEL_NAME
        )
    )


    _nllb_model = (
        AutoModelForSeq2SeqLM.from_pretrained(
            NLLB_MODEL_NAME
        )
    )


    _nllb_model.to(
        _nllb_device
    )


    _nllb_model.eval()


    _nllb_tokenizer.src_lang = (
        "eng_Latn"
    )


    print(
        "✅ NLLB model loaded"
    )


    return (
        _nllb_tokenizer,
        _nllb_model,
        _nllb_device
    )


# =========================================================
# TIME CONVERSION
# =========================================================

def convert_times_to_ethiopia(text):

    if not text:
        return text


    ethiopia = timezone(
        timedelta(hours=3)
    )


    def replace_utc(match):

        hour = int(
            match.group(1)
        )

        minute = int(
            match.group(2)
        )


        dt = datetime(
            2026,
            1,
            1,
            hour,
            minute,
            tzinfo=timezone.utc
        )


        et = dt.astimezone(
            ethiopia
        )


        return et.strftime(
            "%I:%M %p"
        )


    text = re.sub(
        r'\b(\d{1,2}):(\d{2})\s*(?:UTC|GMT)\b',
        replace_utc,
        text,
        flags=re.IGNORECASE
    )


    return text


# =========================================================
# TEXT SPLITTING
# =========================================================

def split_text_for_nllb(
    text,
    tokenizer,
    max_tokens=220
):

    if not text:
        return []


    paragraphs = re.split(
        r'\n\s*\n',
        text
    )


    output = []


    for paragraph in paragraphs:

        paragraph = paragraph.strip()


        if not paragraph:
            continue


        try:

            token_count = len(
                tokenizer.encode(
                    paragraph,
                    add_special_tokens=True
                )
            )


        except Exception:

            token_count = (
                max_tokens + 1
            )


        if token_count <= max_tokens:

            output.append(
                paragraph
            )

            continue


        sentences = re.split(
            r'(?<=[.!?])\s+',
            paragraph
        )


        current = ""


        for sentence in sentences:

            sentence = sentence.strip()


            if not sentence:
                continue


            candidate = (
                sentence
                if not current
                else current + " " + sentence
            )


            try:

                candidate_tokens = len(
                    tokenizer.encode(
                        candidate,
                        add_special_tokens=True
                    )
                )


            except Exception:

                candidate_tokens = (
                    max_tokens + 1
                )


            if (
                current
                and candidate_tokens > max_tokens
            ):

                output.append(
                    current.strip()
                )

                current = sentence


            else:

                current = candidate


        if current.strip():

            output.append(
                current.strip()
            )


    return output


# =========================================================
# TRANSLATE ONE CHUNK
# =========================================================

def nllb_translate_chunk(
    text,
    tokenizer,
    model,
    device
):

    if not text.strip():
        return ""


    import torch


    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )


    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }


    forced_bos_token_id = (
        tokenizer.convert_tokens_to_ids(
            "amh_Ethi"
        )
    )


    with torch.no_grad():

        generated = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=512,
            num_beams=4,
            length_penalty=1.0,
            no_repeat_ngram_size=3,
            do_sample=False,
        )


    result = tokenizer.batch_decode(
        generated,
        skip_special_tokens=True
    )[0]


    return result.strip()


# =========================================================
# TRANSLATION CLEANUP
# =========================================================

def clean_nllb_translation(text):

    if not text:
        return ""


    text = text.strip()


    text = re.sub(
        r'[ \t]+',
        ' ',
        text
    )


    text = re.sub(
        r'\n{3,}',
        '\n\n',
        text
    )


    return text.strip()


def clean_football_terms(text):

    if not text:
        return ""


    replacements = {

        r'\bFull\s*time\b':
            "Fulltime",

        r'\bFull-time\b':
            "Fulltime",

        r'\bKick\s*off\b':
            "Kick off",

        r'\bKick-off\b':
            "Kick off",

        r'\bHere\s*we\s*go\b':
            "Here we go",

        r'\bMatch\s*week\b':
            "Match Week",

        r'\bAssist\b':
            "Assist",
    }


    for pattern, replacement in replacements.items():

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE
        )


    return text


# =========================================================
# MAIN TRANSLATION FUNCTION
# =========================================================

def translate_to_amharic(text):

    if not text:
        return ""


    original_text = text.strip()


    if not original_text:
        return ""


    try:

        text = convert_times_to_ethiopia(
            original_text
        )


        tokenizer, model, device = (
            load_nllb_model()
        )


        chunks = split_text_for_nllb(
            text,
            tokenizer,
            max_tokens=220
        )


        if not chunks:
            return ""


        translated_chunks = []


        for index, chunk in enumerate(
            chunks,
            start=1
        ):

            print(
                f"🌐 Translating chunk "
                f"{index}/{len(chunks)}..."
            )


            try:

                translated = (
                    nllb_translate_chunk(
                        chunk,
                        tokenizer,
                        model,
                        device
                    )
                )


                if translated:

                    translated_chunks.append(
                        translated
                    )

                else:

                    translated_chunks.append(
                        chunk
                    )


            except Exception as e:

                print(
                    f"⚠️ Translation chunk "
                    f"failed: {e}"
                )


                translated_chunks.append(
                    chunk
                )


        result = "\n\n".join(
            translated_chunks
        )


        result = clean_nllb_translation(
            result
        )


        result = clean_football_terms(
            result
        )


        return result.strip()


    except Exception as e:

        print(
            f"❌ Translation failed: "
            f"{e}"
        )


        return original_text


# =========================================================
# BRANDING
# =========================================================

BRANDING = {

    # =====================================================
    # GENERAL HABESHA SPORT
    # =====================================================

    "@habeshasport": {

        "emoji": "⚽",

        "name": "HABESHA SPORT",

        "footer":
            "❤️ ቤተሰቦቻችን ሆይ ላይክ 👍 "
            "ሼር 🔄 ኮመንት 💬 በማድረግ "
            "ይደግፉን።"
    },


    # =====================================================
    # ARSENAL
    # =====================================================

    "@arsenaletgunners": {

        "emoji": "🔴⚪",

        "name": "ARSENAL",

        "footer":
            "🔴⚪ COYG! የአርሰናል ቤተሰብ ሆይ "
            "ላይክ 👍 ሼር 🔄 ኮመንት 💬 "
            "በማድረግ ይደግፉን።"
    },


    # =====================================================
    # LIVERPOOL
    # =====================================================

    "@liverpoolethiop": {

        "emoji": "🔴",

        "name": "LIVERPOOL",

        "footer":
            "🔴 You'll Never Walk Alone ❤️ "
            "የሊቨርፑል ቤተሰብ ሆይ "
            "ላይክ 👍 ሼር 🔄 ኮመንት 💬 "
            "በማድረግ ይደግፉን።"
    },


    # =====================================================
    # MAN CITY
    # =====================================================

    "@mancitynewset": {

        "emoji": "🔵",

        "name": "MANCHESTER CITY",

        "footer":
            "🔵 Come on City! "
            "የማንችስተር ሲቲ ቤተሰብ ሆይ "
            "ላይክ 👍 ሼር 🔄 ኮመንት 💬 "
            "በማድረግ ይደግፉን።"
    },


    # =====================================================
    # CHELSEA
    # =====================================================

    "@chelseafcet": {

        "emoji": "🔵",

        "name": "CHELSEA",

        "footer":
            "🔵 KTBFFH! የቼልሲ ቤተሰብ ሆይ "
            "ላይክ 👍 ሼር 🔄 ኮመንት 💬 "
            "በማድረግ ይደግፉን።"
    },


    # =====================================================
    # MAN UNITED
    # =====================================================

    "@manunitedethiopia": {

        "emoji": "🔴",

        "name": "MANCHESTER UNITED",

        "footer":
            "🔴 Glory Glory Man United! "
            "የማንችስተር ዩናይትድ ቤተሰብ ሆይ "
            "ላይክ 👍 ሼር 🔄 ኮመንት 💬 "
            "በማድረግ ይደግፉን።"
    },


    # =====================================================
    # PREMIER LEAGUE
    # =====================================================

    "@ethplg": {

        "emoji": "🏆",

        "name": "PREMIER LEAGUE",

        "footer":
            "🏆 Premier League የእንግሊዝ እግር ኳስ "
            "ቤተሰብ ሆይ ላይክ 👍 ሼር 🔄 "
            "ኮመንት 💬 በማድረግ ይደግፉን።"
    },
}


# =========================================================
# CREATE GENERAL HEADER
# =========================================================

def create_general_header():

    eth_date, eth_time, session = (
        get_ethiopian_date_and_session()
    )


    return (
        "⚽ HABESHA SPORT\n"
        "አጭር የስፖርት ዜና "
        "ለቤተሰቦቻችን\n\n"
        f"📅 {eth_date}\n"
        f"🕒 {eth_time} | {session}\n\n"
    )


# =========================================================
# CREATE FINAL POST
#
# GENERAL:
#   Header + date/time + news + footer
#
# CLUBS / PREMIER LEAGUE:
#   News + footer
#
# MEDIA-ONLY GENERAL:
#   Header + date/time + footer
#
# MEDIA-ONLY CLUB:
#   Footer
# =========================================================

def create_post(
    text,
    destination
):

    text = remove_links(
        text or ""
    )


    translated = ""


    if text:

        translated = (
            translate_to_amharic(
                text
            )
        )


        translated = remove_links(
            translated
        )


    branding = BRANDING.get(
        destination,
        BRANDING["@habeshasport"]
    )


    footer = branding["footer"]


    # =====================================================
    # GENERAL
    # =====================================================

    if destination == "@habeshasport":

        header = create_general_header()


        if translated:

            result = (
                header
                + translated
                + "\n\n"
                + footer
            )

        else:

            result = (
                header
                + footer
            )


    # =====================================================
    # CLUB / PREMIER LEAGUE
    # =====================================================

    else:

        if translated:

            result = (
                translated
                + "\n\n"
                + footer
            )

        else:

            result = footer


    return result.strip()


# =========================================================
# FACEBOOK
# =========================================================

def facebook_config(
    destination
):

    config = FACEBOOK_DESTINATIONS.get(
        destination
    )


    if not config:
        return None, None


    page_id_env, token_env = config


    page_id = os.environ.get(
        page_id_env,
        ""
    ).strip()


    page_token = os.environ.get(
        token_env,
        ""
    ).strip()


    if not page_id or not page_token:

        return None, None


    return (
        page_id,
        page_token
    )


def facebook_plain_text(text):

    if not text:
        return ""


    text = re.sub(
        r'<[^>]+>',
        '',
        text
    )


    return html.unescape(
        text
    ).strip()


def facebook_request(
    endpoint,
    params=None,
    data=None,
    files=None
):

    url = (
        f"https://graph.facebook.com/"
        f"{FACEBOOK_GRAPH_VERSION}/"
        f"{endpoint}"
    )


    try:

        if files:

            boundary = (
                "----HabeshaSportBoundary"
                + str(
                    int(
                        datetime.now().timestamp()
                    )
                )
            )


            body = bytearray()


            params = params or {}


            for key, value in params.items():

                body.extend(
                    (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; '
                        f'name="{key}"\r\n\r\n'
                        f"{value}\r\n"
                    ).encode(
                        "utf-8"
                    )
                )


            for key, file_info in files.items():

                filename, content, mime = (
                    file_info
                )


                body.extend(
                    (
                        f"--{boundary}\r\n"
                        f'Content-Disposition: form-data; '
                        f'name="{key}"; '
                        f'filename="{filename}"\r\n'
                        f"Content-Type: {mime}\r\n\r\n"
                    ).encode(
                        "utf-8"
                    )
                )


                body.extend(content)


                body.extend(
                    b"\r\n"
                )


            body.extend(
                f"--{boundary}--\r\n".encode(
                    "utf-8"
                )
            )


            request = urllib.request.Request(
                url,
                data=bytes(body),
                method="POST",
                headers={
                    "Content-Type":
                        f"multipart/form-data; "
                        f"boundary={boundary}"
                }
            )


        else:

            encoded = urllib.parse.urlencode(
                params or {}
            ).encode(
                "utf-8"
            )


            request = urllib.request.Request(
                url,
                data=encoded,
                method="POST"
            )


        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            raw = response.read().decode(
                "utf-8"
            )


            return json.loads(
                raw
            )


    except urllib.error.HTTPError as e:

        try:

            body = e.read().decode(
                "utf-8"
            )

        except Exception:

            body = str(e)


        print(
            f"❌ Facebook HTTP error: "
            f"{e.code} {body}"
        )


        return None


    except Exception as e:

        print(
            f"❌ Facebook request error: "
            f"{e}"
        )


        return None


def facebook_post_text(
    destination,
    text
):

    page_id, page_token = (
        facebook_config(
            destination
        )
    )


    if not page_id or not page_token:
        return False


    message = facebook_plain_text(
        text
    )


    if not message:
        return False


    result = facebook_request(
        f"{page_id}/feed",
        params={
            "message": message,
            "access_token": page_token,
        }
    )


    if result and result.get("id"):

        print(
            f"✅ Facebook text posted: "
            f"{destination}"
        )

        return True


    return False


def facebook_post_media(
    destination,
    file_path,
    caption
):

    page_id, page_token = (
        facebook_config(
            destination
        )
    )


    if not page_id or not page_token:
        return False


    if not os.path.exists(
        file_path
    ):

        return False


    try:

        with open(
            file_path,
            "rb"
        ) as f:

            content = f.read()


        filename = os.path.basename(
            file_path
        )


        extension = os.path.splitext(
            filename
        )[1].lower()


        if extension in (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ):

            endpoint = (
                f"{page_id}/photos"
            )


            mime = (
                "image/jpeg"
                if extension in (
                    ".jpg",
                    ".jpeg"
                )
                else "image/png"
            )


            result = facebook_request(
                endpoint,
                params={
                    "caption":
                        facebook_plain_text(
                            caption
                        ),
                    "access_token":
                        page_token,
                },
                files={
                    "source": (
                        filename,
                        content,
                        mime
                    )
                }
            )


        else:

            endpoint = (
                f"{page_id}/videos"
            )


            result = facebook_request(
                endpoint,
                params={
                    "description":
                        facebook_plain_text(
                            caption
                        ),
                    "access_token":
                        page_token,
                },
                files={
                    "source": (
                        filename,
                        content,
                        "video/mp4"
                    )
                }
            )


        if result and (
            result.get("id")
            or result.get("post_id")
        ):

            print(
                f"✅ Facebook media posted: "
                f"{destination}"
            )

            return True


        return False


    except Exception as e:

        print(
            f"❌ Facebook media error: "
            f"{e}"
        )

        return False


# =========================================================
# TELEGRAM PERMISSION ERROR DETECTION
# =========================================================

def is_permanent_telegram_error(
    error
):

    message = str(
        error
    ).lower()


    permanent_patterns = [

        "you can't write in this chat",

        "chat admin privileges are required",

        "not enough rights",

        "forbidden",

        "user is not a member",

        "chat_write_forbidden",

        "channel_private",

        "peer_id_invalid",

        "chat not found",
    ]


    return any(
        pattern in message
        for pattern in permanent_patterns
    )


# =========================================================
# SEND TELEGRAM MEDIA
# =========================================================

async def send_media_to_destination(
    bot_client,
    user_client,
    destination,
    file_path,
    caption,
    buttons=None
):

    # -----------------------------------------------------
    # BOT
    # -----------------------------------------------------

    try:

        await bot_client.send_file(
            destination,
            file_path,
            caption=caption,
            parse_mode=None,
            buttons=buttons
        )


        print(
            f"✅ Media sent by bot: "
            f"{destination}"
        )


        return True


    except Exception as e:

        print(
            f"⚠️ Bot media send failed: "
            f"{e}"
        )


        # -------------------------------------------------
        # USER ACCOUNT FALLBACK
        # -------------------------------------------------

        try:

            await user_client.send_file(
                destination,
                file_path,
                caption=caption,
                parse_mode=None,
                buttons=buttons
            )


            print(
                f"✅ Media sent by user account: "
                f"{destination}"
            )


            return True


        except Exception as user_error:

            print(
                f"❌ User media send failed: "
                f"{user_error}"
            )


            return False


# =========================================================
# BUILD BUTTONS
# =========================================================

def get_post_buttons(
    destination,
    post_number
):

    if (
        post_number <= 0
        or post_number % BUTTON_INTERVAL != 0
    ):

        return None


    # =====================================================
    # GENERAL
    # =====================================================

    if destination == "@habeshasport":

        return PUSH_BUTTONS


    # =====================================================
    # ARSENAL
    # =====================================================

    if destination == "@arsenaletgunners":

        return [

            [
                Button.url(
                    "🔴 Arsenal",
                    "https://t.me/arsenaletgunners"
                )
            ],

            [
                Button.url(
                    "Facebook",
                    "https://www.facebook.com/"
                )
            ]

        ]


    # =====================================================
    # LIVERPOOL
    # =====================================================

    if destination == "@liverpoolethiop":

        return [

            [
                Button.url(
                    "🔴 Liverpool",
                    "https://t.me/liverpoolethiop"
                )
            ],

            [
                Button.url(
                    "Facebook",
                    "https://www.facebook.com/"
                )
            ]

        ]


    # =====================================================
    # MAN CITY
    # =====================================================

    if destination == "@mancitynewset":

        return [

            [
                Button.url(
                    "🔵 Man City",
                    "https://t.me/mancitynewset"
                )
            ],

            [
                Button.url(
                    "Facebook",
                    "https://www.facebook.com/"
                )
            ]

        ]


    # =====================================================
    # CHELSEA
    # =====================================================

    if destination == "@chelseafcet":

        return [

            [
                Button.url(
                    "🔵 Chelsea",
                    "https://t.me/chelseafcet"
                )
            ],

            [
                Button.url(
                    "Facebook",
                    "https://www.facebook.com/"
                )
            ]

        ]


    # =====================================================
    # MAN UNITED
    # =====================================================

    if destination == "@manunitedethiopia":

        return [

            [
                Button.url(
                    "🔴 Man United",
                    "https://t.me/manunitedethiopia"
                )
            ],

            [
                Button.url(
                    "Facebook",
                    "https://www.facebook.com/"
                )
            ]

        ]


    # =====================================================
    # PREMIER LEAGUE
    # =====================================================

    if destination == "@ethplg":

        return [

            [
                Button.url(
                    "🏆 Premier League",
                    "https://t.me/ethplg"
                )
            ],

            [
                Button.url(
                    "Facebook",
                    "https://www.facebook.com/"
                )
            ]

        ]


    return None


# =========================================================
# PROCESS ONE MESSAGE
# =========================================================

async def process_message(
    message,
    destination,
    bot_client,
    user_client,
    post_number
):

    source_text = (
        getattr(
            message,
            "message",
            ""
        )
        or ""
    ).strip()


    # =====================================================
    # AD FILTER
    # =====================================================

    if is_advertisement(
        message
    ):

        print(
            f"🚫 Advertisement/spam "
            f"skipped: ID={message.id}"
        )


        return True, False


    # =====================================================
    # CLEAN SOURCE
    # =====================================================

    clean_source_text = remove_links(
        source_text
    )


    # =====================================================
    # MEDIA
    # =====================================================

    has_media = bool(
        getattr(
            message,
            "media",
            None
        )
    )


    # =====================================================
    # EMPTY
    # =====================================================

    if (
        not clean_source_text
        and not has_media
    ):

        print(
            f"⚠️ Empty message skipped: "
            f"ID={message.id}"
        )


        return True, False


    # =====================================================
    # CREATE FINAL POST
    #
    # IMPORTANT:
    # This is called for BOTH:
    #
    # 1. text/caption messages
    # 2. media-only messages
    #
    # Therefore general header/footer will never
    # be bypassed for media-only messages.
    # =====================================================

    post_text = create_post(
        clean_source_text,
        destination
    )


    # =====================================================
    # BUTTONS
    # =====================================================

    buttons = get_post_buttons(
        destination,
        post_number
    )


    # =====================================================
    # MEDIA
    # =====================================================

    if has_media:

        file_path = None


        try:

            print(
                f"⬇️ Downloading media: "
                f"ID={message.id}"
            )


            file_path = (
                await user_client.download_media(
                    message,
                    file="downloads/"
                )
            )


            if not file_path:

                print(
                    "⚠️ Media download "
                    "returned nothing."
                )


                return True, False


            sent = (
                await send_media_to_destination(
                    bot_client,
                    user_client,
                    destination,
                    file_path,
                    post_text,
                    buttons
                )
            )


            if not sent:

                print(
                    f"⚠️ Could not post media "
                    f"ID={message.id}"
                )


                return True, False


            # Facebook only after Telegram succeeds

            facebook_post_media(
                destination,
                file_path,
                post_text
            )


            return True, True


        except Exception as e:

            print(
                f"❌ Media processing error: "
                f"{e}"
            )


            return True, False


        finally:

            if (
                file_path
                and os.path.exists(
                    file_path
                )
            ):

                try:

                    os.remove(
                        file_path
                    )

                except Exception:

                    pass


    # =====================================================
    # TEXT
    # =====================================================

    if not post_text:

        return True, False


    try:

        await bot_client.send_message(
            destination,
            post_text,
            parse_mode=None,
            buttons=buttons
        )


        print(
            f"✅ Telegram text posted: "
            f"{destination}"
        )


    except Exception as e:

        print(
            f"❌ Telegram text posting "
            f"failed: {e}"
        )


        if is_permanent_telegram_error(
            e
        ):

            print(
                "⚠️ Permanent Telegram error. "
                "Skipping message so source "
                "does not freeze."
            )


            return True, False


        return False, False


    # =====================================================
    # FACEBOOK
    # =====================================================

    facebook_post_text(
        destination,
        post_text
    )


    return True, True


# =========================================================
# CHECK ONE CHANNEL
# =========================================================

async def check_channel(
    user_client,
    bot_client,
    source,
    destination,
    state
):

    print(
        f"\n📡 SOURCE: {source}"
    )


    print(
        f"🎯 DESTINATION: {destination}"
    )


    # =====================================================
    # GET ENTITY
    # =====================================================

    try:

        entity = (
            await user_client.get_entity(
                source
            )
        )


    except Exception as e:

        print(
            f"❌ Could not access source "
            f"{source}: {e}"
        )


        return


    # =====================================================
    # STATE KEY
    # =====================================================

    state_key = str(
        getattr(
            entity,
            "id",
            source
        )
    )


    last_id = int(
        state.get(
            state_key,
            0
        )
    )


    # =====================================================
    # FIRST RUN
    #
    # IMPORTANT:
    # New source starts from the CURRENT latest message.
    # It does NOT repost old history.
    # =====================================================

    if last_id == 0:

        try:

            latest_messages = []


            async for msg in (
                user_client.iter_messages(
                    entity,
                    limit=1
                )
            ):

                latest_messages.append(
                    msg
                )


            if latest_messages:

                latest_id = (
                    latest_messages[0].id
                )


                state[state_key] = (
                    latest_id
                )


                save_state(
                    state
                )


                print(
                    f"🆕 First run for "
                    f"{source}. "
                    f"Starting from message "
                    f"{latest_id}."
                )


            else:

                print(
                    f"ℹ️ No messages found "
                    f"in {source}."
                )


        except Exception as e:

            print(
                f"❌ First-run state error: "
                f"{e}"
            )


        return


    # =====================================================
    # FETCH NEW MESSAGES
    # =====================================================

    messages = []


    try:

        async for msg in (
            user_client.iter_messages(
                entity,
                min_id=last_id,
                reverse=True
            )
        ):

            messages.append(
                msg
            )


    except Exception as e:

        print(
            f"❌ Reading source failed: "
            f"{e}"
        )


        return


    if not messages:

        print(
            f"ℹ️ No new messages: "
            f"{source}"
        )


        return


    print(
        f"📨 {len(messages)} "
        f"new message(s)"
    )


    # =====================================================
    # PROCESS
    # =====================================================

    post_number = 0

    highest_processed_id = last_id


    for message in messages:

        print(
            f"\n➡️ Processing "
            f"{source} ID={message.id}"
        )


        success, posted = (
            await process_message(
                message,
                destination,
                bot_client,
                user_client,
                post_number
            )
        )


        if success:

            highest_processed_id = max(
                highest_processed_id,
                message.id
            )


            state[state_key] = (
                highest_processed_id
            )


            save_state(
                state
            )


            if posted:

                post_number += 1


        else:

            print(
                f"⏸️ Temporary failure at "
                f"{source} ID={message.id}. "
                f"Stopping this source "
                f"for now."
            )


            break


# =========================================================
# SCHEDULE MATCHING
# =========================================================

def get_schedule_sources():

    if not BOT_SCHEDULE:

        return None


    for cron_expression, sources in (
        SCHEDULE_GROUPS.items()
    ):

        if cron_expression == BOT_SCHEDULE:

            return sources


    return None


# =========================================================
# MAIN
# =========================================================

async def main():

    print(
        "\n========================================"
    )


    print(
        "⚽ HABESHA SPORT NEWS BOT"
    )


    print(
        "========================================"
    )


    print(
        "🌐 Translation: "
        "NLLB English → Amharic"
    )


    print(
        f"📅 Schedule: "
        f"{BOT_SCHEDULE or 'manual/all sources'}"
    )


    # =====================================================
    # CLIENTS
    # =====================================================

    user_client = TelegramClient(
        StringSession(USER_SESSION),
        API_ID,
        API_HASH
    )


    bot_client = TelegramClient(
        "bot_session",
        API_ID,
        API_HASH
    )


    await user_client.start()


    await bot_client.start(
        bot_token=BOT_TOKEN
    )


    print(
        "✅ Telegram clients connected."
    )


    # =====================================================
    # STATE
    # =====================================================

    state = load_state()


    # =====================================================
    # DETERMINE SOURCES
    # =====================================================

    scheduled_sources = (
        get_schedule_sources()
    )


    if scheduled_sources is not None:

        sources_to_process = (
            scheduled_sources
        )


        print(
            f"⏰ Scheduled run: "
            f"{len(sources_to_process)} "
            f"source(s)"
        )


    else:

        sources_to_process = (
            SOURCE_CHANNELS
        )


        print(
            f"🔎 Processing all sources: "
            f"{len(sources_to_process)}"
        )


    # =====================================================
    # PROCESS SOURCES
    # =====================================================

    for source in sources_to_process:

        if source in GENERAL_SOURCES:

            destination = (
                DEFAULT_DESTINATION
            )

        else:

            destination = (
                SOURCE_ROUTES.get(
                    source
                )
            )


        if not destination:

            print(
                f"⚠️ No destination "
                f"for {source}"
            )


            continue


        try:

            await check_channel(
                user_client,
                bot_client,
                source,
                destination,
                state
            )


        except Exception as e:

            print(
                f"❌ Error processing "
                f"{source}: {e}"
            )


        await asyncio.sleep(
            1
        )


    # =====================================================
    # DISCONNECT
    # =====================================================

    await bot_client.disconnect()

    await user_client.disconnect()


    print(
        "\n✅ HABESHA SPORT BOT "
        "RUN COMPLETE."
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )


    except KeyboardInterrupt:

        print(
            "\n🛑 Bot stopped."
        )


    except Exception as e:

        print(
            f"\n❌ Fatal error: {e}"
        )
```
