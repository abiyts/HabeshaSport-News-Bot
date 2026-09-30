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
        r
```
