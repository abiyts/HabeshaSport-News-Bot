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
# GITHUB / TELEGRAM SETTINGS
# =========================================================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
USER_SESSION = os.environ["USER_SESSION"]


# =========================================================
# GITHUB ACTIONS SCHEDULE GROUP
# =========================================================

BOT_SCHEDULE = os.environ.get(
    "BOT_SCHEDULE",
    ""
).strip()


# =========================================================
# DEFAULT DESTINATION
# =========================================================

DEFAULT_DESTINATION = "@habeshasport"


# =========================================================
# CLUB SOURCE → CLUB DESTINATION
# =========================================================

SOURCE_ROUTES = {

    # ARSENAL
    "@arsenal_london": "@arsenaletgunners",
    "@Arsenalc": "@arsenaletgunners",
    "@gunnersfooty": "@arsenaletgunners",
    "@GUNNERS": "@arsenaletgunners",
    "@ZENA_ARSENAL": "@arsenaletgunners",
    "@ETHIO_ARSENAL": "@arsenaletgunners",

    # LIVERPOOL
    "@LiverpoolFCNews": "@liverpoolethiop",
    "@liverpool": "@liverpoolethiop",
    "@lfconline": "@liverpoolethiop",

    # MAN CITY
    "@Manchester_City": "@mancitynewset",
    "@manchester_city_cf": "@mancitynewset",
    "@mancity247": "@mancitynewset",

    # CHELSEA
    "@Chelsea_fc_worldwide": "@chelseafcet",
    "@chelseafcnews01": "@chelseafcet",
    "@chelseaanalysis": "@chelseafcet",
    "@chelseasunsport": "@chelseafcet",

    # MAN UNITED
    "@ManchesterUnited": "@manunitedethiopia",
    "@Empire_MU": "@manunitedethiopia",
    "@manchester_united_uk": "@manunitedethiopia",
    "@manchesterunitedsunsport": "@manunitedethiopia",
    "@Manchester_Unitedfanns": "@manunitedethiopia",
    "@man_united_ethio_fan": "@manunitedethiopia",
}


# =========================================================
# GENERAL FOOTBALL SOURCES
# =========================================================

GENERAL_SOURCES = [
    "@sky_sports_world",
    "@Espnfc_news",
]


# =========================================================
# ALL SOURCE CHANNELS
# =========================================================

SOURCE_CHANNELS = GENERAL_SOURCES + list(
    SOURCE_ROUTES.keys()
)


# =========================================================
# SEPARATE 5-MINUTE SCHEDULE GROUPS
# =========================================================

SCHEDULE_GROUPS = {

    # GENERAL
    "0,5,10,15,20,25,30,35,40,45,50,55 * * * *": [
        "@sky_sports_world",
        "@Espnfc_news",
    ],

    # ARSENAL
    "1,6,11,16,21,26,31,36,41,46,51,56 * * * *": [
        "@arsenal_london",
        "@Arsenalc",
        "@gunnersfooty",
        "@GUNNERS",
        "@ZENA_ARSENAL",
        "@ETHIO_ARSENAL",
    ],

    # LIVERPOOL
    "2,7,12,17,22,27,32,37,42,47,52,57 * * * *": [
        "@LiverpoolFCNews",
        "@liverpool",
        "@lfconline",
    ],

    # MAN CITY
    "3,8,13,18,23,28,33,38,43,48,53,58 * * * *": [
        "@Manchester_City",
        "@manchester_city_cf",
        "@mancity247",
    ],

    # CHELSEA
    "4,9,14,19,24,29,34,39,44,49,54,59 * * * *": [
        "@Chelsea_fc_worldwide",
        "@chelseafcnews01",
        "@chelseaanalysis",
        "@chelseasunsport",
    ],

    # MAN UNITED
    "5,10,15,20,25,30,35,40,45,50,55,0 * * * *": [
        "@ManchesterUnited",
        "@Empire_MU",
        "@manchester_united_uk",
        "@manchesterunitedsunsport",
        "@Manchester_Unitedfanns",
        "@man_united_ethio_fan",
    ],
}


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


# =========================================================
# FACEBOOK CONFIG
# =========================================================

def facebook_config(destination):

    config = FACEBOOK_DESTINATIONS.get(destination)

    if not config:
        return None

    page_id = os.environ.get(
        config["page_id_env"],
        ""
    ).strip()

    token = os.environ.get(
        config["token_env"],
        ""
    ).strip()

    if not page_id or not token:

        print(
            "ℹ Facebook is not configured for",
            destination,
            "- Telegram will continue normally."
        )

        return None

    return config, page_id, token


# =========================================================
# FACEBOOK TEXT CLEANING
# =========================================================

def facebook_plain_text(post):

    if not post:
        return ""

    text = re.sub(
        r"<[^>]+>",
        "",
        post
    )

    text = html.unescape(text)

    return text.strip()


# =========================================================
# FACEBOOK GRAPH REQUEST
# =========================================================

def facebook_request(
    endpoint,
    fields,
    files=None
):

    boundary = (
        "----HabeshaSportBoundary"
        + str(abs(hash(endpoint)))
    )

    body = bytearray()

    for key, value in fields.items():

        body.extend(
            f"--{boundary}\r\n".encode()
        )

        body.extend(
            (
                f'Content-Disposition: form-data; '
                f'name="{key}"\r\n\r\n'
            ).encode()
        )

        body.extend(
            str(value).encode("utf-8")
        )

        body.extend(b"\r\n")

    if files:

        for key, file_info in files.items():

            filename, content_type, data = file_info

            body.extend(
                f"--{boundary}\r\n".encode()
            )

            body.extend(
                (
                    f'Content-Disposition: form-data; '
                    f'name="{key}"; '
                    f'filename="{filename}"\r\n'
                ).encode()
            )

            body.extend(
                (
                    f"Content-Type: "
                    f"{content_type}\r\n\r\n"
                ).encode()
            )

            body.extend(data)
            body.extend(b"\r\n")

    body.extend(
        f"--{boundary}--\r\n".encode()
    )

    request = urllib.request.Request(
        endpoint,
        data=bytes(body),
        method="POST",
        headers={
            "Content-Type":
                f"multipart/form-data; boundary={boundary}",
            "User-Agent":
                "Mozilla/5.0",
        },
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=90
        ) as response:

            response_data = (
                response.read()
                .decode("utf-8")
            )

            return json.loads(response_data)

    except urllib.error.HTTPError as e:

        print("")
        print("❌ FACEBOOK GRAPH API ERROR")
        print("HTTP STATUS:", e.code)

        try:

            error_body = (
                e.read()
                .decode("utf-8")
            )

            print("RESPONSE:")
            print(error_body)

        except Exception as read_error:

            print(
                "Could not read Facebook error:",
                read_error
            )

        print("END FACEBOOK ERROR")

        return {
            "error": {
                "http_status": e.code
            }
        }

    except urllib.error.URLError as e:

        print("")
        print(
            "❌ FACEBOOK CONNECTION ERROR:",
            e
        )

        return {
            "error": {
                "connection": str(e)
            }
        }

    except Exception as e:

        print("")
        print(
            "❌ FACEBOOK REQUEST ERROR:",
            e
        )

        return {
            "error": {
                "request": str(e)
            }
        }


# =========================================================
# FACEBOOK TEXT POST
# =========================================================

def facebook_post_text(
    destination,
    post
):

    config = facebook_config(destination)

    if not config:
        return False

    page_config, page_id, token = config

    message = facebook_plain_text(post)

    if not message:
        return False

    endpoint = (
        f"https://graph.facebook.com/"
        f"{FACEBOOK_GRAPH_VERSION}/"
        f"{page_id}/feed"
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

        print(
            "⚠ Facebook text returned:",
            result
        )

        return False

    except Exception as e:

        print(
            "⚠ FACEBOOK TEXT ERROR:",
            e
        )

        return False


# =========================================================
# FACEBOOK MEDIA POST
# =========================================================

def facebook_post_media(
    destination,
    media_path,
    post
):

    config = facebook_config(destination)

    if not config:
        return False

    page_config, page_id, token = config

    try:

        with open(media_path, "rb") as f:
            data = f.read()

        filename = os.path.basename(media_path)
        lower_name = filename.lower()

        if lower_name.endswith(".mp4"):

            endpoint = (
                f"https://graph.facebook.com/"
                f"{FACEBOOK_GRAPH_VERSION}/"
                f"{page_id}/videos"
            )

            content_type = "video/mp4"
            file_field = "source"
            text_field = "description"

        elif lower_name.endswith(".mov"):

            endpoint = (
                f"https://graph.facebook.com/"
                f"{FACEBOOK_GRAPH_VERSION}/"
                f"{page_id}/videos"
            )

            content_type = "video/quicktime"
            file_field = "source"
            text_field = "description"

        elif lower_name.endswith(".m4v"):

            endpoint = (
                f"https://graph.facebook.com/"
                f"{FACEBOOK_GRAPH_VERSION}/"
                f"{page_id}/videos"
            )

            content_type = "video/x-m4v"
            file_field = "source"
            text_field = "description"

        elif lower_name.endswith(".webm"):

            endpoint = (
                f"https://graph.facebook.com/"
                f"{FACEBOOK_GRAPH_VERSION}/"
                f"{page_id}/videos"
            )

            content_type = "video/webm"
            file_field = "source"
            text_field = "description"

        elif lower_name.endswith(
            (".jpg", ".jpeg")
        ):

            endpoint = (
                f"https://graph.facebook.com/"
                f"{FACEBOOK_GRAPH_VERSION}/"
                f"{page_id}/photos"
            )

            content_type = "image/jpeg"
            file_field = "source"
            text_field = "caption"

        elif lower_name.endswith(".png"):

            endpoint = (
                f"https://graph.facebook.com/"
                f"{FACEBOOK_GRAPH_VERSION}/"
                f"{page_id}/photos"
            )

            content_type = "image/png"
            file_field = "source"
            text_field = "caption"

        elif lower_name.endswith(".gif"):

            endpoint = (
                f"https://graph.facebook.com/"
                f"{FACEBOOK_GRAPH_VERSION}/"
                f"{page_id}/photos"
            )

            content_type = "image/gif"
            file_field = "source"
            text_field = "caption"

        elif lower_name.endswith(".webp"):

            endpoint = (
                f"https://graph.facebook.com/"
                f"{FACEBOOK_GRAPH_VERSION}/"
                f"{page_id}/photos"
            )

            content_type = "image/webp"
            file_field = "source"
            text_field = "caption"

        else:

            print(
                "ℹ Facebook media type not supported:",
                filename
            )

            return False

        caption = facebook_plain_text(post)

        fields = {
            "access_token": token,
            "published": "true",
            text_field: caption,
        }

        print("📘 Sending media to Facebook...")
        print(
            "Facebook destination:",
            page_config["name"]
        )
        print("File:", filename)
        print("Content-Type:", content_type)

        result = facebook_request(
            endpoint,
            fields,
            {
                file_field: (
                    filename,
                    content_type,
                    data,
                )
            }
        )

        if (
            result.get("id")
            or result.get("post_id")
        ):

            print(
                "✅ FACEBOOK MEDIA POSTED TO",
                page_config["name"]
            )

            return True

        print(
            "⚠ Facebook media returned:",
            result
        )

        return False

    except Exception as e:

        print(
            "⚠ FACEBOOK MEDIA ERROR:",
            e
        )

        return False


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
        ),
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

        print(
            "⚠ Could not read state.json:",
            e
        )

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

        print(
            "❌ Could not save state:",
            e
        )


# =========================================================
# REMOVE LINKS
# =========================================================

def remove_links(text):

    if not text:
        return ""

    text = re.sub(
        r'https?://\S+',
        '',
        text
    )

    text = re.sub(
        r'(https?://)?t\.me/\S+',
        '',
        text
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
# FOOTBALL TRANSLATION
# FREE LOCAL NLLB 600M
#
# IMPORTANT:
# We DO NOT use fake placeholders such as:
# NLLBKEEPX0X
#
# Football terms are kept OUTSIDE NLLB and restored
# naturally after the translated parts are generated.
# =========================================================

NLLB_MODEL_NAME = os.environ.get(
    "NLLB_MODEL_NAME",
    "dsfsi/nllb_200_distilled_600m-eng-amh"
).strip()

_nllb_tokenizer = None
_nllb_model = None
_nllb_device = None


# =========================================================
# LOAD NLLB
# =========================================================

def load_nllb_model():

    global _nllb_tokenizer
    global _nllb_model
    global _nllb_device

    if (
        _nllb_model is not None
        and _nllb_tokenizer is not None
    ):
        return (
            _nllb_tokenizer,
            _nllb_model,
            _nllb_device
        )

    try:

        import torch

        from transformers import (
            AutoTokenizer,
            AutoModelForSeq2SeqLM
        )

        _nllb_device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        print("")
        print(
            "📦 Loading free NLLB 600M "
            "English → Amharic translator..."
        )

        print(
            "🤖 Model:",
            NLLB_MODEL_NAME
        )

        print(
            "💻 Device:",
            _nllb_device
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

        print(
            "✅ NLLB 600M translator loaded"
        )

        return (
            _nllb_tokenizer,
            _nllb_model,
            _nllb_device
        )

    except Exception as e:

        print(
            "❌ Could not load NLLB translator:",
            e
        )

        _nllb_tokenizer = None
        _nllb_model = None
        _nllb_device = None

        return None, None, None


# =========================================================
# CONVERT SOURCE TIMES TO ETHIOPIA TIME
# =========================================================

def convert_times_to_ethiopia(value):

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

            if (
                ampm == "PM"
                and hour != 12
            ):
                hour += 12

            elif (
                ampm == "AM"
                and hour == 12
            ):
                hour = 0

        source_offset = timezone_offsets.get(
            zone,
            0
        )

        total_minutes = (
            hour * 60
            + minute
            + (3 - source_offset) * 60
        )

        total_minutes %= (
            24 * 60
        )

        eth_hour = (
            total_minutes // 60
        )

        eth_minute = (
            total_minutes % 60
        )

        return (
            f"{eth_hour:02d}:"
            f"{eth_minute:02d} "
            f"Ethiopia time"
        )

    return pattern.sub(
        replace_time,
        value
    )


# =========================================================
# FOOTBALL TERMS
#
# These terms are NOT sent through NLLB.
# This prevents NLLB from producing broken words such as
# NLLBKEEPX0X.
# =========================================================

PROTECTED_FOOTBALL_TERMS = [

    # -------------------------
    # MAJOR CLUBS
    # -------------------------

    "Manchester United",
    "Manchester City",
    "Liverpool",
    "Arsenal",
    "Chelsea",
    "Tottenham Hotspur",
    "Newcastle United",
    "Aston Villa",
    "West Ham United",
    "Crystal Palace",
    "Nottingham Forest",
    "Real Madrid",
    "Barcelona",
    "Atletico Madrid",
    "Bayern Munich",
    "Borussia Dortmund",
    "Paris Saint-Germain",
    "Inter Milan",
    "AC Milan",
    "Juventus",
    "Napoli",
    "Roma",
    "Ajax",
    "Benfica",
    "Porto",
    "Sporting CP",

    # -------------------------
    # SHORT CLUB NAMES
    # -------------------------

    "PSG",
    "LFC",
    "AFC",
    "MUFC",
    "MCFC",
    "FCB",

    # -------------------------
    # COMPETITIONS
    # -------------------------

    "Premier League",
    "Champions League",
    "Europa League",
    "Conference League",
    "FA Cup",
    "Carabao Cup",
    "Community Shield",
    "Club World Cup",
    "World Cup",
    "AFCON",
    "UEFA",
    "FIFA",

    # -------------------------
    # FOOTBALL TERMS
    # -------------------------

    "VAR",
    "Assist",
    "Fulltime",
    "Full-time",
    "Half-time",
    "Kick-off",
    "Kickoff",
    "Match Week",
    "Man of the Match",
    "Player of the Match",

    "transfer",
    "transfers",
    "contract",
    "contracts",
    "deal",
    "medical",
    "loan",
    "loanee",
    "free agent",
    "release clause",
    "buy-back clause",

    "Here we go",
    "Here we Go",

    "starting XI",
    "starting 11",
    "Starting XI",

    "clean sheet",
    "hat-trick",
    "penalty",
    "red card",
    "yellow card",

    # -------------------------
    # FOOTBALL POSITIONS
    # -------------------------

    "goalkeeper",
    "centre-back",
    "center-back",
    "left-back",
    "right-back",
    "midfielder",
    "defender",
    "forward",
    "striker",
    "winger",

    # -------------------------
    # COMMON FOOTBALL ABBREVIATIONS
    # -------------------------

    "EPL",
    "UCL",
    "UEL",
    "PL",
    "FT",
    "HT",
]


# =========================================================
# SORT TERMS LONGEST FIRST
# =========================================================

PROTECTED_FOOTBALL_TERMS_SORTED = sorted(
    set(PROTECTED_FOOTBALL_TERMS),
    key=len,
    reverse=True
)


# =========================================================
# PROPER NAME DETECTION
#
# Protect common multi-word English football names without
# creating artificial placeholder tokens.
# =========================================================

PROPER_NAME_PATTERN = re.compile(
    r"\b"
    r"[A-Z][a-zA-ZÀ-ÖØ-öø-ÿ'-]+"
    r"(?:\s+"
    r"[A-Z][a-zA-ZÀ-ÖØ-öø-ÿ'-]+"
    r"){1,3}"
    r"\b"
)


def find_protected_terms(text):

    matches = []

    # -----------------------------------------------------
    # Explicit football terms
    # -----------------------------------------------------

    explicit_pattern = re.compile(
        "|".join(
            re.escape(term)
            for term in PROTECTED_FOOTBALL_TERMS_SORTED
        ),
        re.IGNORECASE
    )

    for match in explicit_pattern.finditer(text):

        matches.append(
            (
                match.start(),
                match.end(),
                match.group(0)
            )
        )

    # -----------------------------------------------------
    # Multi-word proper names
    # -----------------------------------------------------

    for match in PROPER_NAME_PATTERN.finditer(text):

        matches.append(
            (
                match.start(),
                match.end(),
                match.group(0)
            )
        )

    # -----------------------------------------------------
    # Remove overlaps.
    # Explicit football terms get priority.
    # -----------------------------------------------------

    matches.sort(
        key=lambda item: (
            item[0],
            -(item[1] - item[0])
        )
    )

    accepted = []

    for start, end, value in matches:

        overlaps = False

        for accepted_start, accepted_end, _ in accepted:

            if (
                start < accepted_end
                and end > accepted_start
            ):

                overlaps = True
                break

        if not overlaps:

            accepted.append(
                (
                    start,
                    end,
                    value
                )
            )

    accepted.sort(
        key=lambda item: item[0]
    )

    return accepted


# =========================================================
# SPLIT NORMAL TEXT INTO NLLB-SAFE PIECES
# =========================================================

def split_plain_text_for_nllb(
    text,
    tokenizer,
    max_tokens=190
):

    if not text:
        return []

    pieces = []

    paragraphs = text.split("\n")

    for paragraph in paragraphs:

        if not paragraph.strip():

            pieces.append(
                ("\n", False)
            )

            continue

        paragraph = paragraph.strip()

        # -------------------------------------------------
        # First try the whole paragraph.
        # -------------------------------------------------

        token_count = len(
            tokenizer(
                paragraph,
                add_special_tokens=True,
                truncation=False
            )["input_ids"]
        )

        if token_count <= max_tokens:

            pieces.append(
                (
                    paragraph,
                    True
                )
            )

            continue

        # -------------------------------------------------
        # Split long paragraph into sentences.
        # -------------------------------------------------

        sentences = re.split(
            r"(?<=[.!?])\s+",
            paragraph
        )

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            token_count = len(
                tokenizer(
                    sentence,
                    add_special_tokens=True,
                    truncation=False
                )["input_ids"]
            )

            if token_count <= max_tokens:

                pieces.append(
                    (
                        sentence,
                        True
                    )
                )

                continue

            # -------------------------------------------------
            # Extremely long sentence → words.
            # -------------------------------------------------

            words = sentence.split()

            word_buffer = ""

            for word in words:

                candidate = (
                    word
                    if not word_buffer
                    else word_buffer + " " + word
                )

                candidate_tokens = len(
                    tokenizer(
                        candidate,
                        add_special_tokens=True,
                        truncation=False
                    )["input_ids"]
                )

                if candidate_tokens <= max_tokens:

                    word_buffer = candidate

                else:

                    if word_buffer:

                        pieces.append(
                            (
                                word_buffer,
                                True
                            )
                        )

                    word_buffer = word

            if word_buffer:

                pieces.append(
                    (
                        word_buffer,
                        True
                    )
                )

    return pieces


# =========================================================
# TRANSLATE ONE NLLB CHUNK
# =========================================================

def nllb_translate_chunk(
    text,
    tokenizer,
    model,
    device
):

    import torch

    if not text.strip():
        return ""

    tokenizer.src_lang = "eng_Latn"

    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=256
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

        outputs = model.generate(

            **inputs,

            forced_bos_token_id=(
                forced_bos_token_id
            ),

            # Stay safely within the model's limit.
            max_length=256,

            # Slightly stronger beam search.
            num_beams=5,

            # Helps avoid excessively short translations.
            length_penalty=1.0,

            # Reduces repeated phrases.
            no_repeat_ngram_size=3,

            # Avoid unnecessary sampling.
            do_sample=False,

            early_stopping=True,
        )

    result = tokenizer.batch_decode(
        outputs,
        skip_special_tokens=True
    )[0].strip()

    return result


# =========================================================
# TRANSLATE ONLY THE NON-PROTECTED TEXT
#
# This is the KEY improvement.
#
# Example:
#
# "Liverpool have reached a deal with Arsenal"
#
# NLLB receives:
#
# "have reached a deal with"
#
# while:
#
# Liverpool
# Arsenal
#
# remain untouched.
#
# NO fake NLLBKEEPX placeholders are ever created.
# =========================================================

def translate_with_protected_terms(
    text,
    tokenizer,
    model,
    device
):

    if not text:
        return ""

    matches = find_protected_terms(text)

    if not matches:

        pieces = split_plain_text_for_nllb(
            text,
            tokenizer,
            max_tokens=190
        )

        output = []

        for piece, should_translate in pieces:

            if not should_translate:

                output.append(piece)
                continue

            translated = nllb_translate_chunk(
                piece,
                tokenizer,
                model,
                device
            )

            output.append(
                translated
                if translated
                else piece
            )

        return "\n".join(output).strip()

    result_parts = []

    cursor = 0

    for start, end, original_term in matches:

        # -------------------------------------------------
        # Translate text before protected term.
        # -------------------------------------------------

        before = text[
            cursor:start
        ]

        if before:

            pieces = split_plain_text_for_nllb(
                before,
                tokenizer,
                max_tokens=190
            )

            for piece, should_translate in pieces:

                if not should_translate:

                    result_parts.append(piece)
                    continue

                translated = nllb_translate_chunk(
                    piece,
                    tokenizer,
                    model,
                    device
                )

                result_parts.append(
                    translated
                    if translated
                    else piece
                )

        # -------------------------------------------------
        # Keep football term EXACTLY as source.
        # -------------------------------------------------

        result_parts.append(
            original_term
        )

        cursor = end

    # -----------------------------------------------------
    # Translate remaining text.
    # -----------------------------------------------------

    remaining = text[cursor:]

    if remaining:

        pieces = split_plain_text_for_nllb(
            remaining,
            tokenizer,
            max_tokens=190
        )

        for piece, should_translate in pieces:

            if not should_translate:

                result_parts.append(piece)
                continue

            translated = nllb_translate_chunk(
                piece,
                tokenizer,
                model,
                device
            )

            result_parts.append(
                translated
                if translated
                else piece
            )

    return "".join(result_parts).strip()


# =========================================================
# FINAL NLLB TRANSLATION
# =========================================================

def translate_to_amharic(text):

    if not text:
        return ""

    # -----------------------------------------------------
    # Convert explicit source times first.
    # -----------------------------------------------------

    text = convert_times_to_ethiopia(
        text
    )

    tokenizer, model, device = (
        load_nllb_model()
    )

    if (
        tokenizer is None
        or model is None
    ):

        print(
            "⚠ NLLB unavailable - "
            "using original English text"
        )

        return text.strip()

    try:

        print(
            "🇪🇹 Translating with "
            "NLLB 600M..."
        )

        translated = (
            translate_with_protected_terms(
                text,
                tokenizer,
                model,
                device
            )
        )

        if not translated:

            print(
                "⚠ NLLB returned empty text"
            )

            return text.strip()

        # -------------------------------------------------
        # SAFETY CHECK
        #
        # Old broken placeholders must NEVER reach Telegram.
        # -------------------------------------------------

        broken_placeholder_pattern = re.compile(
            r"NLLB\s*KEEP\s*X?\d+\s*X?",
            re.IGNORECASE
        )

        if broken_placeholder_pattern.search(
            translated
        ):

            print(
                "⚠ Broken NLLB placeholder "
                "detected - removing corrupted token"
            )

            translated = (
                broken_placeholder_pattern.sub(
                    "",
                    translated
                )
            )

        translated = re.sub(
            r"\n{3,}",
            "\n\n",
            translated
        ).strip()

        print(
            "✅ NLLB 600M AMHARIC "
            "TRANSLATION SUCCESS"
        )

        return translated

    except Exception as e:

        print(
            "❌ NLLB translation error:",
            e
        )

        print(
            "⚠ Using original English text "
            "for this post"
        )

        return text.strip()


# =========================================================
# ETHIOPIAN CALENDAR DATE + CLOCK
# =========================================================

def get_ethiopian_date_and_session():

    utc_now = datetime.now(
        timezone.utc
    )

    ethiopia_now = (
        utc_now
        + timedelta(hours=3)
    )

    now = ethiopia_now.replace(
        tzinfo=None
    )

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

        previous_gregorian_year = (
            year - 1
        )

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

    if 6 <= now.hour < 12:

        session = (
            "ጠዋት | Morning"
        )

    elif 12 <= now.hour < 14:

        session = (
            "እኩለ ቀን | Midday"
        )

    elif 14 <= now.hour < 18:

        session = (
            "ከሰዓት | Afternoon"
        )

    elif 18 <= now.hour < 21:

        session = (
            "ማታ | Evening"
        )

    else:

        session = (
            "ሌሊት | Night"
        )

    ethiopian_hour = (
        now.hour - 6
    ) % 12

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

def create_post(
    text,
    destination
):

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

    channel_branding = {

        "@habeshasport": {

            "header": (
                "⚽ <b>HABESHA SPORT | "
                "አጭር የእግር ኳስ ዜና</b>"
            ),

            "footer": (
                "📢 <b>Habesha Sport</b> | "
                "ኢትዮ ስፖርት"
            )
        },

        "@arsenaletgunners": {

            "header": (
                "🔴⚪ <b>ARSENAL NEWS | "
                "የአርሰናል ዜና</b>"
            ),

            "footer": (
                "🔴⚪ <b>Arsenal Ethiopia</b> | "
                "አርሰናል ኢትዮጵያ"
            )
        },

        "@liverpoolethiop": {

            "header": (
                "🔴 <b>LIVERPOOL NEWS | "
                "የሊቨርፑል ዜና</b>"
            ),

            "footer": (
                "🔴 <b>Liverpool Ethiopia</b> | "
                "ሊቨርፑል ኢትዮጵያ"
            )
        },

        "@mancitynewset": {

            "header": (
                "🔵 <b>MAN CITY NEWS | "
                "የማን ሲቲ ዜና</b>"
            ),

            "footer": (
                "🔵 <b>Man City Ethiopia</b> | "
                "ማን ሲቲ ኢትዮጵያ"
            )
        },

        "@chelseafcet": {

            "header": (
                "🔵 <b>CHELSEA NEWS | "
                "የቼልሲ ዜና</b>"
            ),

            "footer": (
                "🔵 <b>Chelsea Ethiopia</b> | "
                "ቼልሲ ኢትዮጵያ"
            )
        },

        "@manunitedethiopia": {

            "header": (
                "🔴 <b>MAN UNITED NEWS | "
                "የማን ዩናይትድ ዜና</b>"
            ),

            "footer": (
                "🔴 <b>Man United Ethiopia</b> | "
                "ማን ዩናይትድ ኢትዮጵያ"
            )
        }
    }

    branding = channel_branding.get(
        destination,
        channel_branding["@habeshasport"]
    )

    if destination == "@habeshasport":

        date_time_header = (
            f"📅 <b>{eth_date} | "
            f"{session}</b>\n"
            f"🕒 <b>{ethiopian_time}</b>\n"
        )

    else:

        date_time_header = ""

    return (
        date_time_header
        + f"{branding['header']}\n\n"
        + translated
        + "\n\n"
        + "━━━━━━━━━━━━━━\n"
        + f"{branding['footer']}\n"
        + "📲 <b>ሼር ያድርጉ፣ "
        + "Like አትርሱ —❤️</b>\n"
        + "❤️  🔥  👍  😂  😢\n"
        + "💖 <b>እንወዳችኋለን!</b> ❤️"
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
        ".msi",
        ".bat",
        ".scr",
        "download apk",
        "download now",
        "install now",

        "betwinner",
        "linebet",
        "1xbet",
        "1x bet",
        "melbet",
        "monybet",
        "betway",
        "bet365",
        "22bet",
        "22 bet",
        "bet9ja",
        "sportybet",
        "mostbet",
        "parimatch",
        "stake.com",

        "betting",
        "sportsbook",
        "sports book",
        "place your bet",
        "place a bet",
        "bet now",
        "win big",
        "odds",
        "free bet",
        "freebets",
        "prediction coupon",

        "casino",
        "roulette",
        "slot games",
        "slots",
        "jackpot",

        "bonus",
        "promo code",
        "promocode",
        "promotion",
        "advertisement",
        "advertising",
        "sponsored",
        "sponsor",
        "special offer",
        "limited offer",

        "gambling",
        "gaming bonus",
        "deposit now",
        "withdraw now",
        "register now",
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

            filename_ad_words = [

                "betwinner",
                "linebet",
                "1xbet",
                "melbet",
                "monybet",
                "casino",
                "betting",
                "gambling",
            ]

            for word in filename_ad_words:

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

            return True, False

        print(
            "\n" + "=" * 60
        )

        print("📰 NEW NEWS")
        print("SOURCE:", source_username)
        print("DESTINATION:", destination)
        print("MESSAGE ID:", message.id)

        print("TEXT:")
        print(original_text[:500])

        post = create_post(
            original_text,
            destination
        )

        show_buttons = (
            (post_count + 1)
            % BUTTON_INTERVAL
            == 0
        )

        buttons = (
            PUSH_BUTTONS
            if show_buttons
            else None
        )

        media = None

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

                telegram_posted = False

                try:

                    print(
                        "🤖 Trying bot account "
                        "to post media..."
                    )

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

                    telegram_posted = True

                except Exception as bot_media_error:

                    print(
                        "⚠ BOT MEDIA POST FAILED:"
                    )

                    print(
                        bot_media_error
                    )

                    print(
                        "🔄 Trying Telegram "
                        "user account..."
                    )

                    try:

                        await user_client.send_file(
                            destination,
                            media,
                            caption=post,
                            parse_mode="html",
                            buttons=buttons,
                            force_document=False
                        )

                        print(
                            "✅ MEDIA POSTED TO",
                            destination,
                            "USING USER ACCOUNT"
                        )

                        telegram_posted = True

                    except Exception as user_media_error:

                        print(
                            "❌ USER MEDIA POST FAILED:"
                        )

                        print(
                            user_media_error
                        )

                if telegram_posted:

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

                try:
                    os.remove(media)
                except Exception:
                    pass

                print(
                    "❌ Telegram media "
                    "could not be posted."
                )

                return False, False

            print(
                "⚠ Media download failed"
            )

        # =================================================
        # TEXT ONLY
        # =================================================

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

            facebook_post_text(
                destination,
                post
            )

            return True, True

        print(
            "⚠ Message contained "
            "no usable text"
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
        # FIRST TIME INITIALIZATION
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
                    "✅ Starting from "
                    "latest message ID:",
                    latest_id
                )

            else:

                state[channel] = 0

                save_state(state)

                print(
                    "ℹ Channel has no messages"
                )

            print(
                "⏳ Waiting for NEW "
                "messages only."
            )

            return

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

        async for message in (
            user_client.iter_messages(
                entity,
                min_id=last_id,
                reverse=True
            )
        ):

            messages.append(message)

        if not messages:

            print(
                "ℹ No new messages"
            )

            return

        print(
            f"📥 Found "
            f"{len(messages)} "
            f"new message(s)"
        )

        highest_successful_id = last_id

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

                if posted:

                    post_count += 1

                    state[
                        "_successful_posts"
                    ] = post_count

                    if (
                        post_count
                        % BUTTON_INTERVAL
                        == 0
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
                    "⚠ State will NOT "
                    "move past this message."
                )

                break

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
        "🚀 HABESHA SPORT "
        "GITHUB BOT"
    )

    print(
        "=" * 60
    )

    state = load_state()

    # =====================================================
    # TELEGRAM USER CLIENT
    # =====================================================

    user_client = TelegramClient(

        StringSession(
            USER_SESSION
        ),

        API_ID,
        API_HASH,

        connection_retries=10,
        retry_delay=5,
        request_retries=10,
        auto_reconnect=True
    )

    # =====================================================
    # TELEGRAM BOT CLIENT
    # =====================================================

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

        print(
            "\n🔐 Connecting "
            "Telegram user..."
        )

        await user_client.start()

        print(
            "✅ Telegram user connected"
        )

        print(
            "\n🤖 Connecting "
            "Telegram bot..."
        )

        await bot_client.start(
            bot_token=BOT_TOKEN
        )

        print(
            "✅ Telegram bot connected"
        )

        print(
            "\n🔎 Checking "
            "source channels..."
        )

        if BOT_SCHEDULE in SCHEDULE_GROUPS:

            channels_to_check = (
                SCHEDULE_GROUPS[
                    BOT_SCHEDULE
                ]
            )

            print(
                "\n⏰ Triggered schedule:",
                BOT_SCHEDULE
            )

            print(
                "📊 Group sources:",
                len(channels_to_check)
            )

        else:

            channels_to_check = (
                SOURCE_CHANNELS
            )

            print(
                "\n🖐 Manual workflow run"
            )

            print(
                "📊 Checking all sources:",
                len(channels_to_check)
            )

        for channel in channels_to_check:

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
            "\n🔌 Telegram "
            "connections closed"
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )
