import asyncio
import io
import re
import json
import html
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx
import random
import string
import time
import struct
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)

# ==================== LOCAL CONFIGURATION ====================
CONFIG_BOT_TOKEN = "8743808077:AAFKv93Fb0kiBV_0dM71bfn_YTyl5krTEhA"
CONFIG_ZENEX_API_KEY = "ZNX_0L6V54ZNXOBN0I7LYN9IRV8M"
CONFIG_ZENEX_BASE_URL = "https://api.zenexnetwork.com"
CONFIG_ADMIN_ID = 8298133943
CONFIG_OTP_GROUP_ID = -1003784095272

try:
    from telegram import CopyTextButton
    HAS_COPY_BTN = True
except ImportError:
    HAS_COPY_BTN = False

# ==================== CONFIG SECTION ====================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip() or CONFIG_BOT_TOKEN.strip()
USER_DATA_FILE = "users.json"
PAID_SMS_FILE = "paid_sms.json"
STATS_FILE = "user_stats.json"
REFERRAL_DATA_FILE = "referral_data.json"
BANNED_USERS_FILE = "banned_users.json"
WITHDRAW_DATA_FILE = "withdraw_requests.json"
ACTIVITY_LOGS_FILE = "activity_logs.json"
DATA_RANGE_FILE = "datarange.json"
SETTINGS_FILE = "settings.json"

BOT_USERNAME = None

ADMIN_ID = int(os.getenv("ADMIN_ID", str(CONFIG_ADMIN_ID or "6907359862")))
ADMINS = [ADMIN_ID]
OTP_GROUP_ID = int(os.getenv("OTP_GROUP_ID", str(CONFIG_OTP_GROUP_ID or "-1003941189680")))

# ==================== PREMIUM EMOJI MAPPING ====================

EMOJI_ID_MAP = {
    "telegram": "5271801931814165886", "instagram": "5269682734820777950",
    "facebook": "5269427536453984598", "tiktok": "5271527792641595125",
    "x": "5269500885905468781",        "whatsapp": "5271536803482981220",
    "up": "5244837092042750681",        "down": "5246762912428603768",
    "add": "5397916757333654639",       "setting": "5341715473882955310",
    "1st": "5440539497383087970",       "2st": "5447203607294265305",
    "3rd": "5453902265922376865",       "free": "5406756500108501710",
    "msg": "5253742260054409879",       "link": "5271604874419647061",
    "status": "5231200819986047254",    "home": "5416041192905265756",
    "gift_box": "5970074171449808121",  "delete": "5422557736330106570",
    "number_change": "5267295703666824255", "refer_btn": "5420396762189831222",
    "get_number_btn": "5375338737028841420", "cross": "5420130255174145507",
    "stop": "5956074558044770726",      "ban": "5420323339723881652",
    "loading": "5386367538735104399",   "profile": "5352861489541714456",
    "done": "6298670698948724690",      "otp_success": "5190781475468915802",
    "nagad": "5352985330628730418",     "bkash": "5348469219761626211",
    "rocket": "5346042941196507141",    "binance": "5348212415077064131",
    "live": "5355102594886833928",      "developer": "5267294466716244344",
    "channel": "6215074610845585917",   "copy": "5429483843541284898",
    "admin": "5350396951407895212",     "waiting": "6217721388736712699",
    "back": "5267490665117275176",      "leader_board": "5280769763398671636",
    "money": "6233367447789899509",     "discord": "5807892405306791778",
    "custom_range": "5231012545799666522", "paypal": "5107533253946901363",
    "imo": "5337155807752524558",       "hi": "5353027129250453493",
    "off": "5352974971167611327",       "diamond": "5251562950698759162",
    "broadcast": "5251671501702196837", "key": "5296369303661067030",
    "bot_logo": "4943094697238201446",  "tk": "5201873447554145566",
    "roket": "5188481279963715781",     "all_done": "5859265295113261399",
    "yes": "5875017993909440887",       "no": "5875005555684152921",
    "fire_love": "5864093929275658617",
}

FALLBACK_EMOJI_MAP = {
    "telegram": "✈️", "instagram": "📷", "facebook": "🔵",
    "tiktok": "🎵", "x": "❌", "whatsapp": "💬",
    "up": "📈", "down": "📉", "add": "➕", "setting": "⚙️",
    "1st": "🥇", "2st": "🥈", "3rd": "🥉", "free": "🆓",
    "msg": "💬", "link": "🔗", "status": "📊", "home": "🏠",
    "gift_box": "🎁", "delete": "🗑️", "number_change": "🔄",
    "get_number_btn": "📞", "cross": "❌", "stop": "🛑",
    "ban": "🚫", "loading": "⏳", "profile": "👤", "done": "✅",
    "otp_success": "⭐", "nagad": "🟠", "bkash": "💖",
    "rocket": "🚀", "binance": "🟡", "live": "🟢",
    "developer": "👨‍💻", "channel": "📢",
    "copy": "📋", "admin": "👑", "waiting": "⏳", "back": "🔙",
    "leader_board": "🏆", "custom_range": "🎯", "refer_btn": "🔗",
    "paypal": "💳", "imo": "💬", "hi": "👋", "off": "🛑",
    "diamond": "💎", "broadcast": "📢", "key": "🔑", "tk": "৳",
    "roket": "🚀", "all_done": "✅", "yes": "✔️", "no": "❌",
    "fire_love": "❤️",
}

PREMIUM_FLAGS = {
    "🇺🇸": "5913463998522592692", "🇺🇦": "5911406692007941050",
    "🇵🇱": "5913550391789752571", "🇰🇿": "5913724621433082323",
    "🇩🇿": "5911197578640233518", "🇪🇸": "5911106310585193018",
    "🇦🇱": "5913272455866093666", "🇷🇺": "5913274246867456342",
    "🇺🇿": "5911051846104912282", "🇩🇪": "5911096835887337583",
    "🇯🇵": "5913293711659241040", "🇹🇷": "5910995113881901195",
    "🇧🇷": "5911011185649521599", "🇬🇧": "5913443365499703513",
    "🇮🇳": "5913754823643107921", "🇧🇩": "5911148568768418614",
}

def get_tg_emoji(key, default_char=""):
    emoji_id = EMOJI_ID_MAP.get(key)
    fallback = default_char or FALLBACK_EMOJI_MAP.get(key, "⭐")
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
    return fallback

def get_country_tg_flag(flag_emoji):
    emoji_id = PREMIUM_FLAGS.get(flag_emoji)
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{flag_emoji}</tg-emoji>'
    return f'<tg-emoji emoji-id="5911106310585193018">{flag_emoji}</tg-emoji>'

CUSTOM_EMOJI_MAP = {
    "🍂": "6098241269782288407", "🚬": "6097927578255890571", "🥃": "6098326065321613233",
    "✅": "6097949525538772310", "🔥": "6100575060521653786", "😂": "6100194178526880063",
    "🤪": "6098305780191073971", "☠️": "6098000309232081114", "🩷": "6098216990332163722",
    "🤣": "6097986153019873224", "😪": "6100541727280469939", "😊": "6098370329254567380",
    "🙂": "6098318970035640370", "👍": "6098365012085053396", "🌸": "6098243924072077483",
    "❤️": "6097989086482537185", "🌟": "6098375466035452160", "🤍": "6100531780136213332",
    "🤩": "6098245534684812941", "🥹": "6098357714935617432", "😀": "6100253363176217244",
    "😁": "6098196881295283699", "✨": "6100515132842976120", "💝": "6100416443084446928",
    "🌚": "6098344091299354241", "🙄": "6098082446186649920", "🥲": "6098074002280949521",
    "😞": "6098066408778766256", "😯": "6098022247925028490", "🌹": "6100380554337721941",
    "💋": "6097965451277506233", "😘": "6097883868373721404", "⛩️": "6098365660625114734",
    "🇮🇳": "6098012116097177946", "👀": "6098136562774579060", "☄️": "6098059974917756947",
    "⚡️": "6100400465806104855", "🛍": "6100685986642008156", "⛔️": "6098265420383395525",
    "🚫": "6100388225149310843", "❗️": "6098049430773045795", "‼️": "6100387306026309394",
    "⁉️": "6100207381256345481", "❓": "6100520888099149405", "⚠️": "6098337704682984714",
    "🌐": "6098236425059178463", "💬": "6097930030682215910", "💭": "6098072155445007587",
    "📊": "6097979946792130160", "🔼": "6100241633620531535", "🔽": "6097896650196391648",
    "🕯": "6098278966710245155", "📈": "6098163741327629439", "📉": "6098266184887572126",
    "✔️": "6098360833081874496", "❌": "6100304499056844996", "🆒": "6097928956940392722",
    "🔔": "6098419394960955857", "🥸": "6098199638664288273", "🤡": "6098228183016937964",
    "🫦": "6098267606521747665", "📌": "6098387861311068868", "💵": "6100353049367157461",
    "💸": "6098101064869893253", "💱": "6100386769155397563", "▶️": "6098132224857610496",
    "🔴": "6100258190719457801", "🟢": "6100670735213139506", "➡️": "6098240488098240166",
    "💥": "6098409379097229044", "🎙": "6097944964283504492", "🎤": "6097912756323751274",
    "📣": "6100239245618716687", "🤫": "6098175097221158343", "👎": "6098025074013508495",
    "🗣️": "6098018421109168142", "🔍": "6098031288831187632", "🛡": "6100129320225741245",
    "🔗": "6100307857721267700", "🖥": "6097957028846638291", "©": "6098365772294264878",
    "ℹ️": "6100619775426173201", "❄️": "6091423846718510311", "🤴": "6269153634991214569",
    "✉️": "6269255258212404947", "✈️": "6165465711352223465", "😎": "6147552742790405148",
    "🍏": "6271378634208974347", "🎮": "6269171759753203605", "💳": "6129870117619634982",
    "🛒": "6257812301399725616", "🥇": "6269400956387987689", "🎖️": "6269232765468676321",
    "💎": "6271537028307881531", "👮": "6271387924223234127", "👮‍♂️": "6271824284310573725",
    "💼": "6271788773520970269", "⚜️": "6271332888512303608", "👑": "6269556155031228243",
    "⚜": "6293958243651686529", "👨‍🏫": "6271814813907685528", "💙": "6269557847248342937",
    "👩‍💻": "6269458311381258421", "📎": "6269304938099118422", "✈": "6262597302989362227",
    "🔑": "6176966310920983412", "🏷": "6260059243605398502", "🏆": "6194737030165959506",
    "✅️": "6283084125192590161", "📸": "6280525956771745921", "🤔": "6147625684219993899",
    "🇺🇿": "6147770549171918136", "⬇️": "6271712920103555728", "😬": "6269253325477123346",
    "💘": "6269180384047533905", "👉": "6158862632926319619", "⏩": "6269290077512274929",
    "🎚": "6260264603171689263", "❤️‍🔥": "6174589037932712505", "🎥": "6158973722255429425",
    "🔜": "6089104521428997572", "🥳": "6269223265001017592", "😮": "6269194596094317437",
    "😭": "6269316311172518259", "⏬": "6156513311585211842", "🚨": "6257780484281997093",
    "😢": "6269245551586316810", "🆘": "6118474036080021585", "🛑": "6271674836628541366",
    "🔸": "6150014626634405643",
}
_CUSTOM_EMOJI_KEYS = sorted(CUSTOM_EMOJI_MAP.keys(), key=len, reverse=True)
_TAG_SPLIT_RE = re.compile(r'(<[^>]+>)')

def _wrap_plain_segment(segment):
    out, i, n = [], 0, len(segment)
    while i < n:
        for k in _CUSTOM_EMOJI_KEYS:
            if segment.startswith(k, i):
                out.append(f'<tg-emoji emoji-id="{CUSTOM_EMOJI_MAP[k]}">{k}</tg-emoji>')
                i += len(k)
                break
        else:
            out.append(segment[i])
            i += 1
    return ''.join(out)

def pe(text):
    if not text:
        return text
    parts = _TAG_SPLIT_RE.split(text)
    out, in_tg_emoji = [], False
    for part in parts:
        if part.startswith('<tg-emoji'):
            in_tg_emoji = True
            out.append(part)
        elif part == '</tg-emoji>':
            in_tg_emoji = False
            out.append(part)
        elif part.startswith('<') and part.endswith('>'):
            out.append(part)
        elif in_tg_emoji:
            out.append(part)
        else:
            out.append(_wrap_plain_segment(part))
    return ''.join(out)

# ==================== SYSTEM DYNAMIC SETTINGS ====================

_settings_cache = None

def load_settings():
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache
    default = {
        "active_panel": "zenex",
        "zenex_api_key": os.getenv("ZENEX_API_KEY", "").strip() or CONFIG_ZENEX_API_KEY.strip(),
        "zenex_base_url": os.getenv("ZENEX_BASE_URL", CONFIG_ZENEX_BASE_URL),
        "panel_url": f"https://t.me/Zenex_Number_bot?start={ADMIN_ID}",
        "allowed_services": ["Instagram", "Facebook", "WhatsApp", "TikTok", "Telegram", "Discord", "PayPal", "Imo"],
        "otp_group_url": "https://t.me/+31eV11IT7WQzMjI9",
        "channel_url": "https://t.me/MinoXofficial0",
        "support_username": "@support",
        "maintenance_mode": False,
        "cooldown_time": 1.0,
        "min_withdraw": 50.0,
        "otp_bonus": 0.20,
        "referral_bonus": 0.0,
        "admins": [ADMIN_ID],
        "owners": [ADMIN_ID],
        "otp_group_chat_id": None,
        "force_join_channel": None,
        "manual_services": [],
    }
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(default, f, indent=4)
        _settings_cache = default
        return default
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        updated = False
        for k, v in default.items():
            if k not in data:
                data[k] = v
                updated = True
        if updated:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=4)
        _settings_cache = data
        return data
    except Exception:
        _settings_cache = default
        return default

def save_settings(settings):
    global _settings_cache
    _settings_cache = settings
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def clean_base_url(url):
    url = str(url).strip().rstrip('/')
    url = re.sub(r'(/v1|/api|/api/v1)$', '', url)
    return url.rstrip('/')

def get_api_credentials():
    settings = load_settings()
    env_api_key = os.getenv("ZENEX_API_KEY", "").strip() or CONFIG_ZENEX_API_KEY.strip()
    configured_api_key = str(settings.get("zenex_api_key", "")).strip()
    return (
        env_api_key or configured_api_key,
        clean_base_url(settings.get("zenex_base_url", "https://api.zenexnetwork.com")),
    )

def get_api_urls(base_url):
    base = str(base_url).strip().rstrip('/')
    return {
        "getnum": f"{base}/v1/getnum",
        "liveaccess": f"{base}/v1/active-ranges",
        "otp": f"{base}/v1/numsuccess/info",
    }

def get_api_headers(api_key):
    return {"mapikey": api_key}

def get_welcome_message():
    rocket = get_tg_emoji("rocket")
    sparkle = get_tg_emoji("otp_success")
    return (
        f"{sparkle} 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 TEST BOT{rocket} {sparkle} \n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{rocket} Enjoy Premium Quality Service {rocket}"
    )

OTP_RATE = 0.20
REFERRAL_PRICE = 0
MIN_WITHDRAW = 50
MAX_WITHDRAW = 10000
SUPPORT_LINK = "https://t.me/bdgiveaways24"
DEVELOPER_LINK = "http://t.me/rafimhossen"

request_queue = asyncio.Queue()
MAX_WORKERS = max(1, int(os.getenv("MAX_WORKERS", "20")))

client_async = httpx.AsyncClient(
    timeout=httpx.Timeout(8.0, connect=2.0, read=5.0),
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    trust_env=False,
)

active_numbers = {}
last_range = {}
CHECK_INTERVAL = 1.5
number_assignment_lock = asyncio.Lock()
_ranges_cache = {"data": None, "updated_at": 0.0, "fetching": False}

def get_app_emoji_id(app_name):
    n = app_name.lower()
    SERVICE_EMOJI_MAP = [
        ("whatsapp business", "5336814486701514414"),
        ("whatsapp",          "5334759662677957452"),
        ("telegram",          "5337010556253543833"),
        ("facebook",          "5334807341109908955"),
        ("instagram",         "5334868205091459431"),
        ("amazon prime",      "6111801057061374810"),
        ("amazon",            "4995019580536524226"),
        ("imo",               "5337155807752524558"),
        ("apple",             "5334637951894722661"),
        ("google",            "5335010201005231986"),
        ("microsoft",         "5334880948259427772"),
        ("teams",             "5334590977837403844"),
        ("tiktok",            "5339213256001102461"),
        ("bkash",             "5348469219761626211"),
        ("bybit",             "5348372939479751825"),
        ("binance",           "5348212415077064131"),
        ("melbet",            "5337102391244263212"),
        ("snapchat",          "5359441366554255082"),
        ("uber",              "5298715455316303708"),
        ("paypal",            "5776103539872896061"),
        ("discord",           "5116246243646898866"),
        ("viber",             "5463060437572528782"),
        ("linkedin",          "6224222994265279792"),
        ("line",              "5399818044866327279"),
        ("wechat",            "5782757599560602950"),
        ("twitter",           "5215726959056662534"),
        ("reddit",            "4992421103847604984"),
        ("pinterest",         "5346103513120258857"),
        ("twitch",            "5233333563306301418"),
        ("zoom",              "5881799193219043268"),
        ("signal",            "5293998404404272267"),
        ("slack",             "4994972469040251302"),
        ("skype",             "4992613535562334989"),
        ("netflix",           "6255738712664050133"),
        ("spotify",           "5411392711146095115"),
        ("hoichoi",           "6104822598493801746"),
        ("daraz",             "5336879280578138635"),
        ("foodpanda",         "5336879280578138635"),
        ("pathao",            "5336879280578138635"),
        ("aliexpress",        "5336879280578138635"),
        ("shopee",            "5336879280578138635"),
        ("payoneer",          "5336879280578138635"),
        ("wise",              "5336879280578138635"),
        ("chatgpt",           "5296516998996445955"),
        ("notion",            "5336879280578138635"),
        ("github",            "5417836094098007862"),
        ("canva",             "5111661409008092227"),
        ("figma",             "5336879280578138635"),
        ("upwork",            "5336879280578138635"),
        ("fiverr",            "5336879280578138635"),
        ("yahoo",             "5336879280578138635"),
        ("dropbox",           "5336879280578138635"),
        ("coursera",          "5336879280578138635"),
        ("duolingo",          "5336879280578138635"),
        ("rocket",            "5346042941196507141"),
    ]
    for k, v in SERVICE_EMOJI_MAP:
        if k in n:
            return v
    return "5861680977994060034"

def get_platform_icon(platform_name):
    return f'<tg-emoji emoji-id="{get_app_emoji_id(platform_name)}">📞</tg-emoji>'

def get_clean_app_name(raw):
    n = raw.lower().strip()
    for k, v in [
        ("facebook", "Facebook"), ("instagram", "Instagram"), ("whatsapp", "WhatsApp"),
        ("tiktok", "TikTok"), ("paypal", "PayPal"), ("telegram", "Telegram"),
        ("discord", "Discord"), ("imo", "Imo")
    ]:
        if k in n:
            return v
    return raw.strip().capitalize()

def make_bold_text(text):
    out = []
    for ch in str(text):
        o = ord(ch)
        if 65 <= o <= 90:
            out.append(chr(o - 65 + 0x1D5D4))
        elif 97 <= o <= 122:
            out.append(chr(o - 97 + 0x1D5EE))
        elif 48 <= o <= 57:
            out.append(chr(o - 48 + 0x1D7EC))
        else:
            out.append(ch)
    return "".join(out)

def _extract_range_count(obj):
    if isinstance(obj, dict):
        for k in ("count", "active_count", "available", "numbers", "total", "qty", "quantity"):
            val = obj.get(k)
            if isinstance(val, (int, float)) and val >= 0:
                return int(val)
            if isinstance(val, str) and val.strip().isdigit():
                return int(val.strip())
    return None

def extract_active_ranges(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return None
    for key in ("active_ranges", "activeRanges", "available_ranges", "availableRanges", "ranges", "range_list"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    for key in ("data", "result", "response", "payload"):
        value = payload.get(key)
        if isinstance(value, (dict, list)):
            nested = extract_active_ranges(value)
            if nested is not None:
                return nested
    grouped = []
    for service, values in payload.items():
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("service", service)
                grouped.append(item)
            else:
                grouped.append({"service": service, "range": value})
    return grouped if grouped else None

async def fetch_top55_ranges_by_app():
    settings = load_settings()
    api_key, base_url = get_api_credentials()
    allowed = {s.lower() for s in settings.get("allowed_services", ["Instagram", "Facebook", "WhatsApp", "TikTok", "Telegram", "Discord", "PayPal", "Imo"])}
    urls = get_api_urls(base_url)
    headers = get_api_headers(api_key)
    ranges_list = None
    for attempt in range(2):
        try:
            r = await client_async.get(urls["liveaccess"], headers=headers, timeout=httpx.Timeout(5.0, connect=1.5))
            ranges_list = extract_active_ranges(r.json())
            if ranges_list is not None:
                break
        except Exception:
            if attempt == 0:
                await asyncio.sleep(0.2)
    if ranges_list is None:
        return None, "Server unreachable or invalid API key."
    if not ranges_list:
        return {}, None

    top = {}
    for obj in ranges_list:
        explicit_cnt = None
        if isinstance(obj, str):
            rng, service = obj.strip(), "Unknown"
        elif isinstance(obj, dict):
            rng = obj.get("range") or obj.get("prefix") or obj.get("range_text") or obj.get("value") or ""
            service = obj.get("service") or obj.get("app") or obj.get("application") or obj.get("service_name") or "Unknown"
            explicit_cnt = _extract_range_count(obj)
        else:
            continue

        rng = str(rng).strip().upper()
        if not rng or not re.search(r"\d", rng):
            continue
        clean = get_clean_app_name(str(service))
        if clean.lower() not in allowed and clean != "Unknown":
            continue
        top.setdefault(clean, {"icon": get_platform_icon(clean), "ranges": [], "range_counts": {}})
        if rng not in top[clean]["ranges"]:
            top[clean]["ranges"].append(rng)
        prev = top[clean]["range_counts"].get(rng, 0)
        add = explicit_cnt if explicit_cnt is not None else 1
        top[clean]["range_counts"][rng] = max(prev, add) if explicit_cnt is not None else (prev + 1)
    return dict(sorted(top.items(), key=lambda x: len(x[1]["ranges"]), reverse=True)), None

def build_app_buttons_from_cache(top):
    btns, row, ci = [], [], 0
    clrs = ["primary"]
    for app_name, app_info in top.items():
        rc = app_info.get("range_counts", {})
        tot = sum(rc.values()) if rc else len(app_info.get("ranges", []))
        row.append(InlineKeyboardButton(
            f"{make_bold_text(app_name)} ({tot})",
            callback_data=f"sel_app_{app_name}",
            api_kwargs={"icon_custom_emoji_id": get_app_emoji_id(app_name), "style": clrs[ci % len(clrs)]}
        ))
        ci += 1
        if len(row) == 2:
            btns.append(row)
            row = []
    if row:
        btns.append(row)
    return btns

def build_manual_service_buttons():
    s = load_settings()
    manual = s.get("manual_services", [])
    btns = []
    clrs = ["primary"]
    for i, svc in enumerate(manual):
        tot = sum(len(c.get("ranges", [])) for c in svc.get("countries", []))
        btns.append(InlineKeyboardButton(
            f"{make_bold_text(svc['name'])} ({tot})",
            callback_data=f"manual_svc_{i}",
            api_kwargs={"icon_custom_emoji_id": get_app_emoji_id(svc['name']), "style": clrs[i % len(clrs)]}
        ))
    return [btns[j:j+2] for j in range(0, len(btns), 2)]

async def _bg_refresh_ranges():
    global _ranges_cache
    while True:
        try:
            if not _ranges_cache["fetching"]:
                _ranges_cache["fetching"] = True
                try:
                    data, _ = await fetch_top55_ranges_by_app()
                    if data:
                        _ranges_cache["data"] = data
                        _ranges_cache["updated_at"] = time.monotonic()
                finally:
                    _ranges_cache["fetching"] = False
        except Exception:
            pass
        await asyncio.sleep(200)

# ==================== ADMIN & DB HELPERS ====================

def get_admin_ids():
    candidates = [ADMIN_ID, CONFIG_ADMIN_ID]
    try:
        configured = load_settings().get("admins", [])
        if isinstance(configured, list):
            candidates.extend(configured)
    except Exception as exc:
        print(f"Support admin settings could not be loaded: {exc}")
    admin_ids = []
    for candidate in candidates:
        try:
            aid = int(candidate)
            if aid > 0 and aid not in admin_ids:
                admin_ids.append(aid)
        except Exception:
            pass
    return admin_ids

def is_admin(user_id):
    try:
        return int(user_id) in get_admin_ids()
    except Exception:
        return False

def get_min_withdraw():
    try:
        return max(0.0, float(load_settings().get("min_withdraw", MIN_WITHDRAW)))
    except Exception:
        return float(MIN_WITHDRAW)

def load_withdraw_requests():
    if not os.path.exists(WITHDRAW_DATA_FILE):
        with open(WITHDRAW_DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(WITHDRAW_DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_withdraw_requests(data):
    with open(WITHDRAW_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_payment_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def load_banned_users():
    if not os.path.exists(BANNED_USERS_FILE):
        with open(BANNED_USERS_FILE, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(BANNED_USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_banned_users(banned_list):
    with open(BANNED_USERS_FILE, "w") as f:
        json.dump(banned_list, f, indent=4)

def is_user_banned(uid):
    return str(uid) in load_banned_users()

def ban_user(uid):
    bl = load_banned_users()
    if str(uid) not in bl:
        bl.append(str(uid))
        save_banned_users(bl)
        return True
    return False

def unban_user(uid):
    bl = load_banned_users()
    if str(uid) in bl:
        bl.remove(str(uid))
        save_banned_users(bl)
        return True
    return False

def load_referral_data():
    if not os.path.exists(REFERRAL_DATA_FILE):
        with open(REFERRAL_DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(REFERRAL_DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_referral_data(data):
    with open(REFERRAL_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_referral_count(uid, count):
    rd = load_referral_data()
    rd.setdefault(str(uid), {"referral_count": 0})["referral_count"] = count
    save_referral_data(rd)

def get_referral_count(uid):
    return load_referral_data().get(str(uid), {}).get("referral_count", 0)

def load_range_db():
    if not os.path.exists(DATA_RANGE_FILE):
        return {}
    try:
        with open(DATA_RANGE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_range_db(data):
    with open(DATA_RANGE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_number_range_info(uid, number, range_text):
    db = load_range_db()
    flag, name = get_country_info(number)
    db[normalize_number(number)] = {
        "user_id": str(uid),
        "number": f"+{normalize_number(number)}",
        "range": range_text,
        "country": f"{flag} {name}",
    }
    save_range_db(db)

def get_country_info(number):
    number = str(number).strip()
    country_map = {
        "2376": ("🇨🇲", "Cameroon"), "2250": ("🇨🇮", "Ivory Coast"),
        "2613": ("🇲🇬", "Madagascar"), "4077": ("🇷🇴", "Romania"),
        "237": ("🇨🇲", "Cameroon"), "225": ("🇨🇮", "Ivory Coast"),
        "261": ("🇲🇬", "Madagascar"), "20": ("🇪🇬", "Egypt"),
        "27": ("🇿🇦", "South Africa"), "234": ("🇳🇬", "Nigeria"),
        "254": ("🇰🇪", "Kenya"), "233": ("🇬🇭", "Ghana"),
        "212": ("🇲🇦", "Morocco"), "213": ("🇩🇿", "Algeria"),
        "216": ("🇹🇳", "Tunisia"), "218": ("🇱🇾", "Libya"),
        "249": ("🇸🇩", "Sudan"), "251": ("🇪🇹", "Ethiopia"),
        "252": ("🇸🇴", "Somalia"), "253": ("🇩🇯", "Djibouti"),
        "255": ("🇹🇿", "Tanzania"), "256": ("🇺🇬", "Uganda"),
        "257": ("🇧🇮", "Burundi"), "258": ("🇲🇿", "Mozambique"),
        "260": ("🇿🇲", "Zambia"), "263": ("🇿🇼", "Zimbabwe"),
        "264": ("🇳🇦", "Namibia"), "265": ("🇲🇼", "Malawi"),
        "266": ("🇱🇸", "Lesotho"), "267": ("🇧🇼", "Botswana"),
        "268": ("🇸🇿", "Swaziland"), "269": ("🇰🇲", "Comoros"),
        "220": ("🇬🇲", "Gambia"), "221": ("🇸🇳", "Senegal"),
        "222": ("🇲🇷", "Mauritania"), "223": ("🇲🇱", "Mali"),
        "224": ("🇬🇳", "Guinea"), "226": ("🇧🇫", "Burkina Faso"),
        "227": ("🇳🇪", "Niger"), "228": ("🇹🇬", "Togo"),
        "229": ("🇧🇯", "Benin"), "230": ("🇲🇺", "Mauritius"),
        "231": ("🇱🇷", "Liberia"), "232": ("🇸🇱", "Sierra Leone"),
        "235": ("🇹🇩", "Chad"), "236": ("🇨🇫", "Central African Republic"),
        "238": ("🇨🇻", "Cape Verde"), "239": ("🇸🇹", "Sao Tome and Principe"),
        "240": ("🇬🇶", "Equatorial Guinea"), "241": ("🇬🇦", "Gabon"),
        "242": ("🇨🇬", "Congo"), "243": ("🇨🇩", "DR Congo"),
        "244": ("🇦🇴", "Angola"), "245": ("🇬🇼", "Guinea-Bissau"),
        "247": ("🇸🇭", "Saint Helena"), "248": ("🇸🇨", "Seychelles"),
        "250": ("🇷🇼", "Rwanda"), "290": ("🇸🇭", "Saint Helena"),
        "291": ("🇪🇷", "Eritrea"), "40": ("🇷🇴", "Romania"),
        "44": ("🇬🇧", "United Kingdom"), "33": ("🇫🇷", "France"),
        "49": ("🇩🇪", "Germany"), "39": ("🇮🇹", "Italy"),
        "34": ("🇪🇸", "Spain"), "31": ("🇳🇱", "Netherlands"),
        "32": ("🇧🇪", "Belgium"), "41": ("🇨🇭", "Switzerland"),
        "43": ("🇦🇹", "Austria"), "46": ("🇸🇪", "Sweden"),
        "47": ("🇳🇴", "Norway"), "45": ("🇩🇰", "Denmark"),
        "358": ("🇫🇮", "Finland"), "351": ("🇵🇹", "Portugal"),
        "353": ("🇮🇪", "Ireland"), "36": ("🇭🇺", "Hungary"),
        "48": ("🇵🇱", "Poland"), "380": ("🇺🇦", "Ukraine"),
        "370": ("🇱🇹", "Lithuania"), "371": ("🇱🇻", "Latvia"),
        "372": ("🇪🇪", "Estonia"), "373": ("🇲🇩", "Moldova"),
        "374": ("🇦🇲", "Armenia"), "375": ("🇧🇾", "Belarus"),
        "376": ("🇦🇩", "Andorra"), "377": ("🇲🇨", "Monaco"),
        "381": ("🇷🇸", "Serbia"), "382": ("🇲🇪", "Montenegro"),
        "385": ("🇭🇷", "Croatia"), "386": ("🇸🇮", "Slovenia"),
        "387": ("🇧🇦", "Bosnia and Herzegovina"), "389": ("🇲🇰", "North Macedonia"),
        "350": ("🇬🇮", "Gibraltar"), "352": ("🇱🇺", "Luxembourg"),
        "354": ("🇮🇸", "Iceland"), "355": ("🇦🇱", "Albania"),
        "356": ("🇲🇹", "Malta"), "357": ("🇨🇾", "Cyprus"),
        "359": ("🇧🇬", "Bulgaria"), "421": ("🇸🇰", "Slovakia"),
        "420": ("🇨🇿", "Czech Republic"), "298": ("🇫🇴", "Faroe Islands"),
        "299": ("🇬🇱", "Greenland"), "1": ("🇺🇸", "United States"),
        "7": ("🇷🇺", "Russia"), "91": ("🇮🇳", "India"),
        "92": ("🇵🇰", "Pakistan"), "880": ("🇧🇩", "Bangladesh"),
        "86": ("🇨🇳", "China"), "81": ("🇯🇵", "Japan"),
        "82": ("🇰🇷", "South Korea"), "84": ("🇻🇳", "Vietnam"),
        "66": ("🇹🇭", "Thailand"), "62": ("🇮🇩", "Indonesia"),
        "60": ("🇲🇾", "Malaysia"), "65": ("🇸🇬", "Singapore"),
        "63": ("🇵🇭", "Philippines"), "95": ("🇲🇲", "Myanmar"),
        "94": ("🇱🇰", "Sri Lanka"), "977": ("🇳🇵", "Nepal"),
        "93": ("🇦🇫", "Afghanistan"), "98": ("🇮🇷", "Iran"),
        "90": ("🇹🇷", "Turkey"), "964": ("🇮🇶", "Iraq"),
        "963": ("🇸🇾", "Syria"), "961": ("🇱🇧", "Lebanon"),
        "962": ("🇯🇴", "Jordan"), "965": ("🇰🇼", "Kuwait"),
        "966": ("🇸🇦", "Saudi Arabia"), "967": ("🇾🇪", "Yemen"),
        "968": ("🇴🇲", "Oman"), "971": ("🇦🇪", "United Arab Emirates"),
        "972": ("🇮🇱", "Israel"), "973": ("🇧🇭", "Bahrain"),
        "974": ("🇶🇦", "Qatar"), "994": ("🇦🇿", "Azerbaijan"),
        "995": ("🇬🇪", "Georgia"), "996": ("🇰🇬", "Kyrgyzstan"),
        "992": ("🇹🇯", "Tajikistan"), "993": ("🇹🇲", "Turkmenistan"),
        "998": ("🇺🇿", "Uzbekistan"), "855": ("🇰🇭", "Cambodia"),
        "856": ("🇱🇦", "Laos"), "976": ("🇲🇳", "Mongolia"),
        "850": ("🇰🇵", "North Korea"), "55": ("🇧🇷", "Brazil"),
        "52": ("🇲🇽", "Mexico"), "54": ("🇦🇷", "Argentina"),
        "57": ("🇨🇴", "Colombia"), "51": ("🇵🇪", "Peru"),
        "58": ("🇻🇪", "Venezuela"), "56": ("🇨🇱", "Chile"),
        "593": ("🇪🇨", "Ecuador"), "591": ("🇧🇴", "Bolivia"),
        "595": ("🇵🇾", "Paraguay"), "598": ("🇺🇾", "Uruguay"),
        "502": ("🇬🇹", "Guatemala"), "503": ("🇸🇻", "El Salvador"),
        "504": ("🇭🇳", "Honduras"), "506": ("🇨🇷", "Costa Rica"),
        "507": ("🇵🇦", "Panama"), "509": ("🇭🇹", "Haiti"),
        "501": ("🇧🇿", "Belize"), "61": ("🇦🇺", "Australia"),
        "64": ("🇳🇿", "New Zealand"), "675": ("🇵🇬", "Papua New Guinea"),
        "679": ("🇫🇯", "Fiji"), "1246": ("🇧🇧", "Barbados"),
        "1876": ("🇯🇲", "Jamaica"), "53": ("🇨🇺", "Cuba"),
        "592": ("🇬🇾", "Guyana"),
    }
    clean_num = str(number).replace('+', '').replace(' ', '').replace('-', '').strip()
    for prefix in sorted(country_map.keys(), key=len, reverse=True):
        if clean_num.startswith(prefix):
            return country_map[prefix]
    return ("🌍", "Unknown")

def detect_service(full_sms):
    if not full_sms:
        return "SMS SERVICE"
    sms_lower = full_sms.lower()
    service_keywords = {
        "facebook": "FACEBOOK", "fb": "FACEBOOK",
        "instagram": "INSTAGRAM", "insta": "INSTAGRAM",
        "tiktok": "TIKTOK", "twitter": "TWITTER", "x.com": "TWITTER",
        "snapchat": "SNAPCHAT", "snap": "SNAPCHAT",
        "whatsapp": "WHATSAPP", "telegram": "TELEGRAM",
        "discord": "DISCORD", "messenger": "MESSENGER",
        "linkedin": "LINKEDIN", "google": "GOOGLE", "gmail": "GOOGLE",
        "amazon": "AMAZON", "microsoft": "MICROSOFT", "outlook": "MICROSOFT",
        "yahoo": "YAHOO", "paypal": "PAYPAL", "binance": "BINANCE",
        "coinbase": "COINBASE", "spotify": "SPOTIFY", "netflix": "NETFLIX",
        "uber": "UBER", "apple": "APPLE", "icloud": "APPLE",
        "bkash": "BKASH", "nagad": "NAGAD", "stripe": "STRIPE",
        "line": "LINE", "wechat": "WECHAT", "viber": "VIBER",
        "signal": "SIGNAL", "pubg": "PUBG", "free fire": "FREE FIRE",
    }
    for keyword, service_name in sorted(service_keywords.items(), key=lambda x: len(x[0]), reverse=True):
        if keyword in sms_lower:
            return service_name
    return "SMS SERVICE"

# ==================== KEYBOARDS SECTION ====================

def make_reply_btn(text, emoji_id=None, style=None):
    api_kwargs = {}
    if emoji_id:
        api_kwargs['icon_custom_emoji_id'] = str(emoji_id)
    if style:
        api_kwargs['style'] = style
    return KeyboardButton(text=text, api_kwargs=api_kwargs if api_kwargs else None)

def main_keyboard(user_id):
    keyboard = [
        [make_reply_btn("GET NUMBER", emoji_id="5228843986747147814", style="primary"),
         make_reply_btn("GET 2FA",    emoji_id="5296369303661067030", style="primary")],
        [make_reply_btn("PROFILE",    emoji_id="5422444280473998663", style="primary"),
         make_reply_btn("LEADERBOARD",emoji_id="5228875876879318811", style="primary")],
        [make_reply_btn("SUPPORT",    emoji_id="5267294466716244344", style="primary")],
    ]
    if is_admin(user_id):
        keyboard.append([make_reply_btn("ADMIN PANEL", emoji_id="5350396951407895212", style="primary")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def account_keyboard():
    return ReplyKeyboardMarkup([
        [make_reply_btn("BALANCE",        emoji_id="6233367447789899509", style="primary"),
         make_reply_btn("REFER AND EARN", emoji_id="5420396762189831222", style="primary")],
        [make_reply_btn("VIEW PROFILE",   emoji_id="5422444280473998663", style="primary"),
         make_reply_btn("BACK TO MAIN",   emoji_id="5267490665117275176", style="primary")],
    ], resize_keyboard=True)

def cancel_keyboard():
    return ReplyKeyboardMarkup([[make_reply_btn("CANCEL", emoji_id="5420130255174145507", style="primary")]], resize_keyboard=True)

def admin_main_keyboard():
    return ReplyKeyboardMarkup([
        [make_reply_btn("USER MANAGEMENT",      emoji_id="5193063022226086560", style="primary"),
         make_reply_btn("SYSTEM CONFIGURATION", emoji_id="5341715473882955310", style="primary")],
        [make_reply_btn("BOT SETTINGS",         emoji_id="5282843764451195532", style="primary"),
         make_reply_btn("SERVICE MANAGEMENT",   emoji_id="5375338737028841420", style="primary")],
        [make_reply_btn("WITHDRAWAL MANAGEMENT",emoji_id="6233367447789899509", style="primary"),
         make_reply_btn("SUPPORT CHAT",           emoji_id="5267294466716244344", style="primary")],
        [make_reply_btn("⏳ PENDING WITHDRAWALS",emoji_id="6217721388736712699", style="primary")],
        [make_reply_btn("BACK TO MAIN",         emoji_id="5267490665117275176", style="primary")]
    ], resize_keyboard=True)

def user_management_keyboard():
    return ReplyKeyboardMarkup([
        [make_reply_btn("SEND MESSAGE TO ALL USERS", emoji_id="5251671733630431622", style="primary"),
         make_reply_btn("ALL USER ID",               emoji_id="5352861489541714456", style="primary")],
        [make_reply_btn("BAN USER LIST",             emoji_id="5420323339723881652", style="primary"),
         make_reply_btn("ALL USER BALANCE",          emoji_id="6233367447789899509", style="primary")],
        [make_reply_btn("BACK TO ADMIN",             emoji_id="5267490665117275176", style="primary")]
    ], resize_keyboard=True)

def system_config_keyboard():
    return ReplyKeyboardMarkup([
        [make_reply_btn("TODAY ALL STATUS",  emoji_id="5231200819986047254", style="primary"),
         make_reply_btn("USER STATUS CHECK", emoji_id="5352861489541714456", style="primary")],
        [make_reply_btn("BAN USER",          emoji_id="5420323339723881652", style="primary"),
         make_reply_btn("UNBAN USER",        emoji_id="5875017993909440887", style="primary")],
        [make_reply_btn("BAN USER LIST",     emoji_id="5956074558044770726", style="primary"),
         make_reply_btn("REMOVE BALANCE",    emoji_id="5244837092042750681", style="primary")],
        [make_reply_btn("ADD BALANCE",       emoji_id="5397916757333654639", style="primary"),
         make_reply_btn("BACK TO ADMIN",     emoji_id="5267490665117275176", style="primary")]
    ], resize_keyboard=True)

def bot_settings_keyboard():
    return ReplyKeyboardMarkup([
        [make_reply_btn("ADD ADMIN",          emoji_id="5397916757333654639", style="primary"),
         make_reply_btn("REMOVE ADMIN",       emoji_id="5244837092042750681", style="primary")],
        [make_reply_btn("SET OTP GROUP LINK", emoji_id="5253742260054409879", style="primary"),
         make_reply_btn("SET FORCE CHANNEL",  emoji_id="5282843764451195532", style="primary")],
        [make_reply_btn("SET OTP CHAT ID",    emoji_id="5231200819986047254", style="primary"),
         make_reply_btn("ZENEX CONFIG",       emoji_id="5350396951407895212", style="primary")],
        [make_reply_btn("BACK TO ADMIN",      emoji_id="5267490665117275176", style="primary")]
    ], resize_keyboard=True)

def zenex_config_keyboard():
    return ReplyKeyboardMarkup([
        [make_reply_btn("SET API KEY",          emoji_id="5397916757333654639", style="primary"),
         make_reply_btn("SET BASE URL",         emoji_id="5253742260054409879", style="primary")],
        [make_reply_btn("SET ALLOWED SERVICES", emoji_id="5341715473882955310", style="primary"),
         make_reply_btn("VIEW ZENEX CONFIG",    emoji_id="5231200819986047254", style="primary")],
        [make_reply_btn("BACK TO BOT SETTINGS", emoji_id="5267490665117275176", style="primary")]
    ], resize_keyboard=True)

def service_management_keyboard():
    return ReplyKeyboardMarkup([
        [make_reply_btn("ADD SERVICE",    emoji_id="5397916757333654639", style="primary"),
         make_reply_btn("REMOVE SERVICE", emoji_id="5244837092042750681", style="primary")],
        [make_reply_btn("LIST SERVICES",  emoji_id="5352861489541714456", style="primary"),
         make_reply_btn("BACK TO ADMIN",  emoji_id="5267490665117275176", style="primary")]
    ], resize_keyboard=True)

def withdrawal_management_keyboard():
    return ReplyKeyboardMarkup([
        [make_reply_btn("PENDING WITHDRAWALS", emoji_id="6217721388736712699", style="primary"),
         make_reply_btn("SET MINIMUM WITHDRAW",emoji_id="5397916757333654639", style="primary")],
        [make_reply_btn("BACK TO ADMIN",       emoji_id="5267490665117275176", style="primary")],
    ], resize_keyboard=True)

def withdraw_method_keyboard():
    return ReplyKeyboardMarkup([
        [make_reply_btn("BKASH",  emoji_id="5348469219761626211", style="primary"),
         make_reply_btn("NAGAD",  emoji_id="5352985330628730418", style="primary")],
        [make_reply_btn("ROCKET", emoji_id="5346042941196507141", style="primary"),
         make_reply_btn("BINANCE",emoji_id="5348212415077064131", style="primary")],
        [make_reply_btn("CANCEL", emoji_id="5420130255174145507", style="primary")]
    ], resize_keyboard=True)

# ==================== HELPER, DB & STATS ====================

def format_balance(balance):
    return f"{balance:.2f}"

def extract_otp(text):
    if not text or text == "No Content":
        return "N/A"
    spaced_otp = re.search(r'\b(\d{3}\s\d{3})\b', text)
    if spaced_otp:
        return spaced_otp.group(1).replace(" ", "")
    match = re.search(r'\b(\d{4,8})\b', text)
    return match.group(1) if match else "N/A"

def normalize_number(num):
    return re.sub(r'\D', '', str(num))

def mask_number(num):
    return f"{num[:4]}****{num[-6:]}" if len(num) > 6 else num

def get_date_reset_time():
    now = datetime.now()
    return datetime(now.year, now.month, now.day, 0, 0, 0)

def is_valid_bangladesh_number(number):
    number = re.sub(r'\D', '', str(number))
    return len(number) == 11 and number.startswith('01')

def is_range_request(param):
    return 'X' in param.upper()

def is_referral_request(param):
    return param.isdigit()

def load_data(filename=USER_DATA_FILE):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data, filename=USER_DATA_FILE):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def get_user(uid, user_obj=None):
    uid = str(uid)
    data = load_data()
    if uid not in data:
        data[uid] = {
            "user_id": uid,
            "full_name": user_obj.full_name if user_obj else "",
            "username": user_obj.username if user_obj else "",
            "balance": 0.0,
            "total_numbers": 0,
            "referral_count": 0,
            "joined_at": datetime.now().isoformat(),
        }
        save_data(data)
    return data[uid]

async def update_db_balance(uid, amount):
    uid = str(uid)
    data = load_data()
    if uid in data:
        data[uid]["balance"] = round(data[uid].get("balance", 0.0) + amount, 2)
        save_data(data)
        return data[uid]["balance"]
    return 0.0

def get_all_users():
    data = load_data(USER_DATA_FILE)
    return list(data.keys()) if data else []

def user_exists(uid):
    return str(uid) in load_data(USER_DATA_FILE)

def load_stats():
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def log_global_activity(uid, action, details):
    if not os.path.exists(ACTIVITY_LOGS_FILE):
        with open(ACTIVITY_LOGS_FILE, "w") as f:
            json.dump([], f)
    try:
        with open(ACTIVITY_LOGS_FILE, "r") as f:
            logs = json.load(f)
    except Exception:
        logs = []
    now = datetime.now()
    logs.append({
        "uid": str(uid), "action": action, "details": details,
        "timestamp": now.isoformat(), "date": now.strftime("%d/%m/%Y"), "time": now.strftime("%H:%M:%S")
    })
    with open(ACTIVITY_LOGS_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def add_number_taken(uid, count=1):
    uid = str(uid)
    stats = load_stats()
    stats.setdefault(uid, {"numbers_taken": [], "otps_received": []})
    now = datetime.now().isoformat()
    for _ in range(count):
        stats[uid]["numbers_taken"].append(now)
    log_global_activity(uid, "NUMBER_TAKEN", {"count": count})
    save_stats(stats)

def add_otp_received(uid):
    uid = str(uid)
    stats = load_stats()
    stats.setdefault(uid, {"numbers_taken": [], "otps_received": []})
    stats[uid]["otps_received"].append(datetime.now().isoformat())
    save_stats(stats)

def get_user_stats(uid):
    uid = str(uid)
    user_stats = load_stats().get(uid, {"numbers_taken": [], "otps_received": []})
    now = datetime.now()
    today_midnight = get_date_reset_time()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    numbers_taken = user_stats.get("numbers_taken", [])
    otps_received = user_stats.get("otps_received", [])
    return {
        "total_numbers": len(numbers_taken),
        "total_otps": len(otps_received),
        "today_numbers": sum(1 for t in numbers_taken if datetime.fromisoformat(t) >= today_midnight),
        "today_otps": sum(1 for t in otps_received if datetime.fromisoformat(t) >= today_midnight),
        "last24h_numbers": sum(1 for t in numbers_taken if datetime.fromisoformat(t) > last_24h),
        "last24h_otps": sum(1 for t in otps_received if datetime.fromisoformat(t) > last_24h),
        "last7d_numbers": sum(1 for t in numbers_taken if datetime.fromisoformat(t) > last_7d),
        "last7d_otps": sum(1 for t in otps_received if datetime.fromisoformat(t) > last_7d),
    }

def get_global_system_stats():
    stats = load_stats()
    now = datetime.now()
    today_midnight = datetime(now.year, now.month, now.day)
    last_7d = now - timedelta(days=7)
    total_n = total_o = today_n = today_o = seven_n = seven_o = 0
    for u in stats.values():
        n_list = u.get("numbers_taken", [])
        o_list = u.get("otps_received", [])
        total_n += len(n_list)
        total_o += len(o_list)
        for t in n_list:
            dt = datetime.fromisoformat(t)
            if dt >= today_midnight: today_n += 1
            if dt >= last_7d: seven_n += 1
        for t in o_list:
            dt = datetime.fromisoformat(t)
            if dt >= today_midnight: today_o += 1
            if dt >= last_7d: seven_o += 1
    return today_n, today_o, seven_n, seven_o, total_n, total_o

# ==================== LEADERBOARD & 2FA ====================

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    stats_data = load_stats()
    today_midnight = get_date_reset_time()
    user_data_all = load_data(USER_DATA_FILE)
    user_today_counts = []
    for uid_str, user_stats in stats_data.items():
        today_count = sum(1 for ts in user_stats.get("otps_received", []) if datetime.fromisoformat(ts) >= today_midnight)
        if today_count > 0:
            name = user_data_all.get(uid_str, {}).get("full_name") or user_data_all.get(uid_str, {}).get("username") or f"User {uid_str}"
            user_today_counts.append((uid_str, today_count, html.escape(name)))
    user_today_counts.sort(key=lambda x: x[1], reverse=True)
    top10 = user_today_counts[:10]
    if not top10:
        msg = "<b>🏆 TOP 10 OTP LEADERBOARD 🏆</b>\n━━━━━━━━━━━━━━━━━━━━\n\n❌ আজ পর্যন্ত কেউ OTP পায়নি।\n"
    else:
        msg = "<b>🏆 TOP 10 OTP RECEIVERS (TODAY) 🏆</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for idx, (_, count, name) in enumerate(top10, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, f"{idx}️⃣")
            msg += f"{medal} <b>{name}</b>\n   🔑 <code>{count}</code> OTPs\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n📊 <i>প্রতিদিন রাত ১২টায় রিসেট হয়</i>"
    await update.message.reply_text(pe(msg), parse_mode="HTML", reply_markup=main_keyboard(uid))

def generate_2fa_code(secret_key):
    try:
        clean_secret = secret_key.replace(" ", "").upper().strip()
        key = base64.b32decode(clean_secret, casefold=True)
        t_val = int(time.time()) // 30
        h = hmac.new(key, struct.pack(">Q", t_val), hashlib.sha1).digest()
        o = h[-1] & 0xf
        code = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1_000_000
        return f"{code:06d}", clean_secret
    except Exception:
        return None, None

async def get_2fa_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    context.user_data["mode"] = "get_2fa"
    await update.message.reply_text(pe("⚡ <b>GET 2FA CODE</b> ⚡\n\n<blockquote>🔑 ENTER YOUR 2FA SECRET KEY:</blockquote>"), parse_mode="HTML", reply_markup=cancel_keyboard())

async def process_2fa_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    secret_key = update.message.text.strip()
    context.user_data["mode"] = None
    otp_code, clean_key = generate_2fa_code(secret_key)
    if otp_code is None:
        await update.message.reply_text(pe("❌ <b>INVALID 2FA SECRET KEY</b>\n\n⚠️ Please send a valid base32 key."), parse_mode="HTML", reply_markup=main_keyboard(uid))
        return
    now = datetime.now()
    final_msg = (
        "✅ <b>2FA CODE GENERATED!</b>\n\n"
        f"<blockquote>🔑 KEY: <code>{clean_key}</code></blockquote>\n"
        f"<blockquote>🔢 CODE: <code>{otp_code}</code></blockquote>\n"
        f"<blockquote>⏳ EXPIRES IN: 30 SECONDS</blockquote>\n"
        f"📅 {now.strftime('%d %B, %Y')} | {now.strftime('%I:%M %p')}"
    )
    await update.message.reply_text(pe(final_msg), parse_mode="HTML", reply_markup=main_keyboard(uid))

# ==================== RANGES & LIVE NUMBERS ====================

async def fetch_top55_ranges_by_app():
    settings = load_settings()
    api_key, base_url = get_api_credentials()
    allowed = {s.lower() for s in settings.get("allowed_services", ["Instagram", "Facebook", "WhatsApp", "TikTok", "Telegram", "Discord", "PayPal", "Imo"])}
    urls = get_api_urls(base_url)
    ranges_list = None
    for attempt in range(2):
        try:
            r = await client_async.get(urls["liveaccess"], headers=get_api_headers(api_key), timeout=httpx.Timeout(5.0, connect=1.5))
            ranges_list = extract_active_ranges(r.json())
            if ranges_list is not None:
                break
        except Exception:
            if attempt == 0:
                await asyncio.sleep(0.2)
    if ranges_list is None:
        return None, "Server unreachable or invalid API key."
    if not ranges_list:
        return {}, None

    top = {}
    for obj in ranges_list:
        explicit_cnt = None
        if isinstance(obj, str):
            rng, service = obj.strip(), "Unknown"
        elif isinstance(obj, dict):
            rng = obj.get("range") or obj.get("prefix") or obj.get("range_text") or obj.get("value") or ""
            service = obj.get("service") or obj.get("app") or obj.get("application") or obj.get("service_name") or "Unknown"
            explicit_cnt = _extract_range_count(obj)
        else:
            continue
        rng = str(rng).strip().upper()
        if not rng or not re.search(r"\d", rng):
            continue
        clean = get_clean_app_name(str(service))
        if clean.lower() not in allowed and clean != "Unknown":
            continue
        top.setdefault(clean, {"icon": get_platform_icon(clean), "ranges": [], "range_counts": {}})
        if rng not in top[clean]["ranges"]:
            top[clean]["ranges"].append(rng)
        prev = top[clean]["range_counts"].get(rng, 0)
        add = explicit_cnt if explicit_cnt is not None else 1
        top[clean]["range_counts"][rng] = max(prev, add) if explicit_cnt is not None else (prev + 1)
    return dict(sorted(top.items(), key=lambda x: len(x[1]["ranges"]), reverse=True)), None

def build_app_buttons_from_cache(top):
    btns, row, ci = [], [], 0
    for app_name, app_info in top.items():
        rc = app_info.get("range_counts", {})
        tot = sum(rc.values()) if rc else len(app_info.get("ranges", []))
        row.append(InlineKeyboardButton(
            f"{make_bold_text(app_name)} ({tot})",
            callback_data=f"sel_app_{app_name}",
            api_kwargs={"icon_custom_emoji_id": get_app_emoji_id(app_name), "style": "primary"},
        ))
        ci += 1
        if len(row) == 2:
            btns.append(row)
            row = []
    if row:
        btns.append(row)
    return btns

def build_manual_service_buttons():
    manual = load_settings().get("manual_services", [])
    btns = []
    for i, svc in enumerate(manual):
        tot = sum(len(c.get("ranges", [])) for c in svc.get("countries", []))
        btns.append(InlineKeyboardButton(
            f"{make_bold_text(svc['name'])} ({tot})",
            callback_data=f"manual_svc_{i}",
            api_kwargs={"icon_custom_emoji_id": get_app_emoji_id(svc['name']), "style": "primary"},
        ))
    return [btns[j:j+2] for j in range(0, len(btns), 2)]

async def _bg_refresh_ranges():
    global _ranges_cache
    while True:
        try:
            if not _ranges_cache["fetching"]:
                _ranges_cache["fetching"] = True
                try:
                    data, _ = await fetch_top55_ranges_by_app()
                    if data:
                        _ranges_cache["data"] = data
                        _ranges_cache["updated_at"] = time.monotonic()
                finally:
                    _ranges_cache["fetching"] = False
        except Exception:
            pass
        await asyncio.sleep(200)

async def show_app_selection(update, context):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    context.user_data.pop("top_ranges_by_app", None)
    cache_age = time.monotonic() - _ranges_cache["updated_at"]
    if _ranges_cache["data"] and cache_age < 300:
        top = _ranges_cache["data"]
        context.user_data["top_ranges_by_app"] = top
        kb = build_app_buttons_from_cache(top) + build_manual_service_buttons()
        kb.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range", api_kwargs={"style": "primary"})])
        await update.message.reply_text(
            pe(f'{get_tg_emoji("get_number_btn")} <b>SELECT APP TO GET NUMBER</b>\n━━━━━━━━━━━━━━━━━━━━━'),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return

    status = await update.message.reply_text(pe(f'{get_tg_emoji("loading")} <b>Loading ranges...</b>'), parse_mode="HTML")
    top, err = await fetch_top55_ranges_by_app()
    if err or not top:
        top, err = await fetch_top55_ranges_by_app()
    if err or not top:
        manual_rows = build_manual_service_buttons()
        if manual_rows:
            manual_rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range", api_kwargs={"style": "primary"})])
            await status.edit_text(
                pe(f'{get_tg_emoji("get_number_btn")} <b>SELECT APP TO GET NUMBER</b>\n━━━━━━━━━━━━━━━━━━━━━'),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(manual_rows),
            )
        else:
            await status.edit_text(pe(f'{get_tg_emoji("stop")} No active ranges returned by the API.'), parse_mode="HTML")
        return

    _ranges_cache["data"] = top
    _ranges_cache["updated_at"] = time.monotonic()
    context.user_data["top_ranges_by_app"] = top
    kb = build_app_buttons_from_cache(top) + build_manual_service_buttons()
    kb.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range", api_kwargs={"style": "primary"})])
    await status.edit_text(
        pe(f'{get_tg_emoji("get_number_btn")} <b>SELECT APP TO GET NUMBER</b>\n━━━━━━━━━━━━━━━━━━━━━'),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb),
    )

async def register_active_number(uid, number, range_text, app_name=None):
    clean_num = normalize_number(number)
    if len(clean_num) < 7:
        return None
    async with number_assignment_lock:
        if clean_num in active_numbers:
            return None
        active_numbers[clean_num] = {
            "uid": uid,
            "range": str(range_text).strip().upper(),
            "app": app_name or "",
            "timestamp": datetime.now(),
        }
        save_number_range_info(uid, clean_num, range_text)
    return clean_num

async def fetch_number_async(range_str):
    range_str = str(range_str or "").strip().upper()
    if not range_str:
        return None
    try:
        api_key, base_url = get_api_credentials()
        urls = get_api_urls(base_url)
        r = await client_async.post(
            urls["getnum"],
            json={"range": range_str, "is_national": False, "remove_plus": False},
            headers={**get_api_headers(api_key), "Accept": "application/json"},
            timeout=httpx.Timeout(8.0, connect=2.0, read=6.0),
        )
        if 200 <= r.status_code < 300:
            data = r.json()
            num, payload = extract_number_from_payload(data)
            if num:
                return {
                    "number": num,
                    "otp_now": bool(extract_first_value(payload, ("otp", "otp_code", "code", "verification_code"))),
                    "otp": extract_first_value(payload, ("otp", "otp_code", "code", "verification_code")),
                    "sms": extract_first_value(payload, ("sms", "message", "full_sms", "text")),
                }
    except Exception:
        return None
    return None

async def fetch_live_numbers_for_range(range_text, limit=8):
    live_nums, seen = [], set()
    for _ in range(limit):
        res = await fetch_number_async(range_text)
        if res and res.get("number"):
            n = normalize_number(res["number"])
            if n and n not in seen:
                seen.add(n)
                live_nums.append(n)
        else:
            break
        if len(live_nums) >= 6:
            break
    return live_nums

async def show_live_numbers_for_country(query, context, range_text, app_name, country_label):
    uid = query.from_user.id
    await query.message.edit_text(
        pe(
            f"🔍 <b>LOADING LIVE NUMBERS</b>\n"
            f"<blockquote>📱 App: <b>{html.escape(app_name)}</b>\n"
            f"🌍 Country: <b>{html.escape(country_label)}</b>\n"
            f"📶 Range: <code>{html.escape(range_text)}</code></blockquote>"
        ),
        parse_mode="HTML",
    )
    live_nums = await fetch_live_numbers_for_range(range_text, limit=8)
    if not live_nums:
        await query.message.edit_text(
            pe(
                f"❌ <b>NO LIVE NUMBERS RIGHT NOW</b>\n"
                f"<blockquote>🌍 Country: <b>{html.escape(country_label)}</b>\n"
                f"📶 Range: <code>{html.escape(range_text)}</code></blockquote>"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 RETRY", callback_data="same_range", style="primary"),
                InlineKeyboardButton("◀️ BACK", callback_data="back_apps", style="primary"),
            ]]),
        )
        return

    context.user_data["live_numbers_list"] = live_nums
    context.user_data["live_numbers_app"] = app_name
    context.user_data["live_numbers_range"] = range_text
    last_range[uid] = range_text

    rows = [
        [InlineKeyboardButton(f"🟢 +{n}", callback_data=f"pick_live_{i}", api_kwargs={"style": "primary"})]
        for i, n in enumerate(live_nums)
    ]
    rows.append([
        InlineKeyboardButton("🔄 REFRESH", callback_data="same_range", style="primary"),
        InlineKeyboardButton("◀️ BACK", callback_data="back_apps", style="primary"),
    ])

    await query.message.edit_text(
        pe(
            f"🟢 <b>LIVE NUMBERS ({len(live_nums)})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<blockquote>📱 App: <b>{html.escape(app_name)}</b>\n"
            f"🌍 Country: <b>{html.escape(country_label)}</b>\n"
            f"📶 Range: <code>{html.escape(range_text)}</code></blockquote>\n"
            f"👇 <b>নিচের যেকোনো একটি Live Number সিলেক্ট করুন:</b>"
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows),
    )

async def notify_admin_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE, referrer_id=None, is_re_start=False):
    user = update.effective_user
    if not user:
        return
    uid = user.id
    full_name = html.escape(user.full_name or "Unknown")
    username = html.escape(f"@{user.username}" if user.username else "No username")
    total_users = len(load_data(USER_DATA_FILE))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tag = "🆕 NEW USER STARTED BOT" if not is_re_start else "🔄 USER RE-STARTED BOT"
    ref_txt = f"<code>{referrer_id}</code>" if referrer_id else "Direct (None)"
    msg = (
        f"🔔 <b>{tag}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b> {full_name}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>User ID:</b> <code>{uid}</code>\n"
        f"👥 <b>Referral By:</b> {ref_txt}\n"
        f"📊 <b>Total Users:</b> <b>{total_users}</b>\n"
        f"⏰ <b>Time:</b> {now_str}"
    )
    for admin_id in get_admin_ids():
        try:
            await context.bot.send_message(chat_id=admin_id, text=pe(msg), parse_mode="HTML")
        except Exception as e:
            print(f"Admin notify error ({admin_id}): {e}")

# ==================== AUTO OTP MONITOR & WORKER ====================

async def monitor_loop(app):
    while True:
        try:
            settings = load_settings()
            api_key, base_url = get_api_credentials()
            urls = get_api_urls(base_url)
            r = await client_async.get(urls["otp"], headers=get_api_headers(api_key))
            if r.status_code != 200:
                await asyncio.sleep(5)
                continue
            res = r.json()
            otps = []
            if isinstance(res, dict):
                if "data" in res:
                    d = res["data"]
                    otps = d if isinstance(d, list) else (d.get("otps") or d.get("active") or [])
                else:
                    otps = res.get("otps") or []
            elif isinstance(res, list):
                otps = res

            if otps:
                paid_data = load_data(PAID_SMS_FILE)
                paid_keys_set = set(paid_data.keys())
                processed_in_session = set()
                for otp in otps:
                    num = normalize_number(otp.get("number", ""))
                    full_sms = otp.get("otp") or otp.get("sms") or otp.get("message") or "No SMS Content"
                    otp_id = str(otp.get("nid") or otp.get("otp_id", ""))
                    otp_code = extract_otp(full_sms)
                    if not otp_code or otp_code == "N/A":
                        continue
                    sms_key = otp_id if otp_id else f"{num}_{full_sms}"
                    if num in active_numbers and sms_key not in paid_keys_set and sms_key not in processed_in_session:
                        details = active_numbers[num]
                        paid_keys_set.add(sms_key)
                        processed_in_session.add(sms_key)
                        paid_data[sms_key] = {"uid": details["uid"], "otp": otp_code}
                        otp_bonus = settings.get("otp_bonus", OTP_RATE)
                        await update_db_balance(details["uid"], otp_bonus)
                        add_otp_received(details["uid"])
                        log_global_activity(details["uid"], "OTP_RECEIVED", {"number": num, "otp": otp_code, "sms": full_sms})
                        country_flag, _ = get_country_info(num)
                        clean_num = num.replace('+', '').strip()
                        flag_tg = get_country_tg_flag(country_flag)
                        purchased_app = details.get("app") or detect_service(full_sms)
                        app_em = get_platform_icon(purchased_app)
                        btn_copy = InlineKeyboardButton(
                            otp_code,
                            copy_text=CopyTextButton(text=otp_code) if HAS_COPY_BTN else None,
                            callback_data=None if HAS_COPY_BTN else f"copy_text_{otp_code}",
                            api_kwargs={"icon_custom_emoji_id": "5296369303661067030"},
                        )
                        user_msg = f"{flag_tg} {app_em} +{clean_num}"
                        group_msg = f"{flag_tg} {app_em} +{mask_number(clean_num)}"
                        try:
                            await app.bot.send_message(details["uid"], pe(user_msg), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[btn_copy]]))
                        except Exception:
                            pass
                        try:
                            gid = settings.get("otp_group_chat_id") or OTP_GROUP_ID
                            await app.bot.send_message(gid, pe(group_msg), parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[btn_copy]]))
                        except Exception:
                            pass
                        save_data(paid_data, PAID_SMS_FILE)
        except Exception:
            pass
        await asyncio.sleep(CHECK_INTERVAL)

async def worker():
    while True:
        task = await request_queue.get()
        try:
            if task["type"] == "auto_number":
                live_nums = await fetch_live_numbers_for_range(task["range_text"], limit=6)
                uid = task["update"].effective_user.id
                if live_nums:
                    task["context"].user_data["live_numbers_list"] = live_nums
                    task["context"].user_data["live_numbers_app"] = detect_service(task["range_text"])
                    task["context"].user_data["live_numbers_range"] = task["range_text"]
                    rows = [[InlineKeyboardButton(f"🟢 +{n}", callback_data=f"pick_live_{i}", api_kwargs={"style": "primary"})] for i, n in enumerate(live_nums)]
                    await task["update"].message.reply_text(pe("🟢 <b>LIVE NUMBERS</b>"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
                else:
                    await task["update"].message.reply_text("❌ No live numbers found.", reply_markup=main_keyboard(uid))
        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            request_queue.task_done()

# ==================== COMMANDS & HANDLERS ====================

async def check_force_join(update, context):
    channel = load_settings().get("force_join_channel")
    if not channel:
        return True
    uid = update.effective_user.id
    if is_admin(uid):
        return True
    try:
        member = await context.bot.get_chat_member(channel, uid)
        if member.status in ("member", "administrator", "creator", "restricted"):
            return True
    except Exception:
        pass
    ch_clean = str(channel).lstrip("@")
    await update.message.reply_text(
        pe("⚠️ <b>FORCE JOIN REQUIRED!</b>\n\n<blockquote>আগে চ্যানেলে জয়েন করুন।</blockquote>"),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ JOIN CHANNEL", url=f"https://t.me/{ch_clean}", style="primary")]]),
    )
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    uid_str = str(uid)
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return

    existing_data = load_data(USER_DATA_FILE)
    is_new_user = uid_str not in existing_data
    ref_id = None
    if context.args and context.args[0].isdigit():
        cand = int(context.args[0])
        if cand != uid and str(cand) in existing_data:
            ref_id = cand

    if is_new_user:
        get_user(uid, user)
        if ref_id is not None:
            new_count = get_referral_count(ref_id) + 1
            update_referral_count(ref_id, new_count)
            await update_db_balance(ref_id, float(REFERRAL_PRICE))
        await notify_admin_new_user(update, context, referrer_id=ref_id, is_re_start=False)
    else:
        await notify_admin_new_user(update, context, referrer_id=ref_id, is_re_start=True)

    if not await check_force_join(update, context):
        return

    context.user_data.clear()
    await update.message.reply_text(pe(get_welcome_message()), parse_mode="HTML")
    await update.message.reply_text("🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(uid))

async def show_pending_withdrawals(update, context):
    pending = [(pid, r) for pid, r in load_withdraw_requests().items() if r.get("status") == "pending"]
    if not pending:
        await update.message.reply_text(pe("✅ <b>NO PENDING WITHDRAWALS</b>"), parse_mode="HTML", reply_markup=withdrawal_management_keyboard())
        return
    rows, lines = [], ["⏳ <b>PENDING WITHDRAWALS</b>\n"]
    for pid, r in pending:
        lines.append(f"🆔 <code>{pid}</code>\n👤 User: <code>{r.get('user_id')}</code> | 💰 {float(r.get('amount', 0)):.2f} BDT\n📝 {html.escape(str(r.get('method', '')))} | 📞 <code>{html.escape(str(r.get('number', '')))}</code>\n")
        rows.append([
            InlineKeyboardButton("✅ APPROVE", callback_data=f"admin_approve_{pid}", style="primary"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"admin_reject_{pid}", style="primary"),
        ])
    await update.message.reply_text(pe("\n".join(lines)), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    await query.answer()

    if not is_admin(uid) and is_user_banned(uid):
        await query.edit_message_text("🚫 YOU ARE BANNED 🚫")
        return

    if data.startswith("sel_app_"):
        app_name = data[8:]
        top = context.user_data.get("top_ranges_by_app") or (_ranges_cache.get("data") or {})
        ranges = top.get(app_name, {}).get("ranges", [])
        range_counts = top.get(app_name, {}).get("range_counts", {})
        if not ranges:
            await query.answer("No ranges available right now.", show_alert=True)
            return
        context.user_data["sel_app"] = app_name
        context.user_data["sel_ranges"] = ranges

        country_groups = {}
        for i, r in enumerate(ranges):
            pfx_d = re.sub(r"\D", "", re.sub(r"[xX]+$", "", str(r)).strip())
            flag, cname = get_country_info(pfx_d)
            label = f"{flag} {cname}"
            cnt = range_counts.get(r, 1)
            if label not in country_groups:
                country_groups[label] = {"count": 0, "first_idx": i}
            country_groups[label]["count"] += cnt

        btns = [InlineKeyboardButton(f"{lbl} ({grp['count']})", callback_data=f"sel_rng_{grp['first_idx']}", api_kwargs={"style": "primary"}) for lbl, grp in list(country_groups.items())[:24]]
        rows = [btns[j:j+2] for j in range(0, len(btns), 2)]
        rows.append([InlineKeyboardButton("◀️ BACK", callback_data="back_apps", api_kwargs={"style": "primary"})])
        await query.message.edit_text(
            pe(f'{get_tg_emoji("get_number_btn")} <b>SELECT COUNTRY</b>\n━━━━━━━━━━━━━━━━━━━━━\n<blockquote>📱 App: <b>{html.escape(app_name)}</b></blockquote>\n<blockquote>🌍 Select your Country:</blockquote>'),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(rows),
        )
        return

    if data.startswith("sel_rng_"):
        idx = int(data[8:])
        ranges = context.user_data.get("sel_ranges", [])
        app_name = context.user_data.get("sel_app", "Service")
        if idx >= len(ranges):
            await query.answer("Range not found.", show_alert=True)
            return
        rng_val = ranges[idx]
        pfx_d = re.sub(r"\D", "", re.sub(r"[xX]+$", "", str(rng_val)).strip())
        flag, cname = get_country_info(pfx_d)
        await show_live_numbers_for_country(query, context, rng_val, app_name, f"{flag} {cname}")
        return

    if data.startswith("pick_live_"):
        idx = int(data[len("pick_live_"):])
        live_list = context.user_data.get("live_numbers_list", [])
        app_name = context.user_data.get("live_numbers_app", "Service")
        rng_val = context.user_data.get("live_numbers_range", "")
        if idx >= len(live_list):
            await query.answer("Expired, refresh list.", show_alert=True)
            return
        chosen = live_list[idx]
        reserved = await register_active_number(uid, chosen, rng_val, app_name)
        num_final = reserved or normalize_number(chosen)
        add_number_taken(uid, 1)
        flag, cname = get_country_info(num_final)
        await query.message.edit_text(
            pe(
                f"✅ <b>YOUR NUMBER DETAILS</b> ✅\n\n"
                f"<blockquote>🌍 COUNTRY: <code>{flag} {html.escape(cname)}</code>\n"
                f"📱 APP: <code>{html.escape(app_name)}</code>\n"
                f"📶 RANGE: <code>{html.escape(rng_val)}</code>\n"
                f"📞 NUMBER: <code>+{num_final}</code></blockquote>\n\n"
                f"<b>📩 SMS STATUS: ⏳ WAITING...</b>"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 SAME RANGE", callback_data="same_range", style="primary"),
                InlineKeyboardButton("◀️ BACK", callback_data="back_apps", style="primary"),
            ]]),
        )
        return

    if data == "same_range":
        r_text = last_range.get(uid)
        app_name = context.user_data.get("live_numbers_app") or context.user_data.get("sel_app") or "Service"
        if r_text:
            pfx_d = re.sub(r"\D", "", re.sub(r"[xX]+$", "", str(r_text)).strip())
            flag, cname = get_country_info(pfx_d)
            await show_live_numbers_for_country(query, context, r_text, app_name, f"{flag} {cname}")
        return

    if data.startswith("manual_svc_"):
        idx = int(data[len("manual_svc_"):])
        manual = load_settings().get("manual_services", [])
        if idx >= len(manual):
            return
        svc = manual[idx]
        countries = svc.get("countries", [])
        btns = [InlineKeyboardButton(f"{c.get('flag', '🌍')} {c.get('name', '?')} ({len(c.get('ranges', []))})", callback_data=f"manual_cnt_{idx}_{ci}", api_kwargs={"style": "primary"}) for ci, c in enumerate(countries)]
        rows = [btns[j:j+2] for j in range(0, len(btns), 2)]
        rows.append([InlineKeyboardButton("◀️ BACK", callback_data="back_apps", api_kwargs={"style": "primary"})])
        await query.message.edit_text(pe(f"🔧 <b>{html.escape(svc['name'])}</b>\n<blockquote>🌍 Select your Country:</blockquote>"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return

    if data.startswith("manual_cnt_"):
        _, _, svc_i, cnt_i = data.split("_")
        manual = load_settings().get("manual_services", [])
        svc = manual[int(svc_i)]
        c = svc["countries"][int(cnt_i)]
        rng_val = random.choice(c.get("ranges", ["880XXX"])).strip().upper()
        await show_live_numbers_for_country(query, context, rng_val, svc["name"], f"{c.get('flag', '🌍')} {c.get('name', '')}")
        return

    if data in ("back_apps", "back_services"):
        top = context.user_data.get("top_ranges_by_app") or (_ranges_cache.get("data") or {})
        rows = build_app_buttons_from_cache(top) + build_manual_service_buttons()
        rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range", api_kwargs={"style": "primary"})])
        await query.message.edit_text(pe(f'{get_tg_emoji("get_number_btn")} <b>SELECT APP TO GET NUMBER</b>\n━━━━━━━━━━━━━━━━━━━━━'), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return

    if data == "custom_range":
        context.user_data["mode"] = "custom_range"
        await query.message.edit_text(pe("⚙️ <b>CUSTOM RANGE</b>\n\n<blockquote>📱 Type your custom range (e.g. <code>234XXX</code>):</blockquote>"), parse_mode="HTML")
        return

    if data == "withdraw_start":
        bal = get_user(uid)["balance"]
        mw = get_min_withdraw()
        if bal < mw:
            await query.message.reply_text(pe(f"<blockquote>💵 BALANCE: {format_balance(bal)} BDT\n📉 MIN WITHDRAW: {mw:.2f} BDT</blockquote>"), parse_mode="HTML")
            return
        context.user_data["withdraw_mode"] = "select_method"
        await query.message.reply_text("💳 SELECT YOUR PAYMENT METHOD!", reply_markup=withdraw_method_keyboard())
        return

    if data == "withdraw_confirm":
        temp = context.user_data.get("temp_withdraw")
        if temp:
            await update_db_balance(uid, -temp["amount"])
            wr = load_withdraw_requests()
            wr[temp["payment_id"]] = {"user_id": uid, **temp, "status": "pending", "timestamp": datetime.now().isoformat()}
            save_withdraw_requests(wr)
            await query.message.edit_text(pe(f"✅ <b>WITHDRAW REQUEST SUBMITTED</b>\n🆔 <code>{temp['payment_id']}</code>"), parse_mode="HTML")
            for aid in get_admin_ids():
                try:
                    await context.bot.send_message(aid, pe(f"💸 <b>NEW WITHDRAW</b>\n👤 <code>{uid}</code>\n💰 {temp['amount']:.2f} BDT\n📞 <code>{temp['number']}</code>"), parse_mode="HTML")
                except Exception:
                    pass
            context.user_data["temp_withdraw"] = None
            context.user_data["withdraw_mode"] = None
        return

    if data == "withdraw_cancel":
        context.user_data["temp_withdraw"] = None
        context.user_data["withdraw_mode"] = None
        await query.message.edit_text("❌ WITHDRAW CANCELLED")
        return

    if data.startswith("admin_approve_") and is_admin(uid):
        pid = data.replace("admin_approve_", "")
        wr = load_withdraw_requests()
        if pid in wr and wr[pid].get("status") == "pending":
            wr[pid]["status"] = "approved"
            save_withdraw_requests(wr)
            try:
                await context.bot.send_message(wr[pid]["user_id"], pe(f"🎉 <b>WITHDRAW APPROVED!</b>\n💰 {float(wr[pid]['amount']):.2f} BDT"), parse_mode="HTML")
            except Exception:
                pass
            await query.message.edit_text(f"✅ APPROVED: {pid}")
        return

    if data.startswith("admin_reject_") and is_admin(uid):
        pid = data.replace("admin_reject_", "")
        wr = load_withdraw_requests()
        if pid in wr and wr[pid].get("status") == "pending":
            wr[pid]["status"] = "rejected"
            save_withdraw_requests(wr)
            await update_db_balance(wr[pid]["user_id"], float(wr[pid].get("amount", 0)))
            await query.message.edit_text(f"❌ REJECTED: {pid}")
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    uid = update.effective_user.id
    text = (update.message.text or update.message.caption or "").strip()

    if not is_admin(uid) and is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return

    if text == "CANCEL":
        for k in ("mode", "admin_mode", "user_management_mode", "system_config_mode", "bot_settings_mode", "zenex_config_mode", "service_mgmt_mode", "withdrawal_admin_mode", "withdraw_mode", "broadcast_mode", "add_balance_mode", "remove_balance_mode", "admin_ban_mode", "admin_unban_mode", "support_mode"):
            context.user_data.pop(k, None)
        await update.message.reply_text("❌ CANCELLED", reply_markup=main_keyboard(uid))
        return

    if context.user_data.get("support_mode") and not is_admin(uid):
        context.user_data["support_mode"] = False
        for aid in get_admin_ids():
            try:
                await context.bot.send_message(aid, pe(f"📩 <b>SUPPORT MESSAGE</b>\n👤 <code>{uid}</code>\n💬 {html.escape(text)}"), parse_mode="HTML")
            except Exception:
                pass
        await update.message.reply_text("✅ আপনার মেসেজ অ্যাডমিনের কাছে পাঠানো হয়েছে।", reply_markup=main_keyboard(uid))
        return

    if is_admin(uid):
        if text == "ADMIN PANEL":
            context.user_data["admin_mode"] = "main"
            await update.message.reply_text("🎛 <b>WELCOME TO ADMIN PANEL</b>", parse_mode="HTML", reply_markup=admin_main_keyboard())
            return
        if text == "BACK TO MAIN":
            context.user_data.clear()
            await update.message.reply_text("🔙 Back to main menu.", reply_markup=main_keyboard(uid))
            return
        if text == "BACK TO ADMIN":
            for k in ("user_management_mode", "system_config_mode", "bot_settings_mode", "zenex_config_mode", "service_mgmt_mode", "withdrawal_admin_mode"):
                context.user_data.pop(k, None)
            context.user_data["admin_mode"] = "main"
            await update.message.reply_text("🔙 Back to admin panel.", reply_markup=admin_main_keyboard())
            return
        if text == "USER MANAGEMENT":
            context.user_data["user_management_mode"] = "main"
            await update.message.reply_text("👥 <b>USER MANAGEMENT</b>", parse_mode="HTML", reply_markup=user_management_keyboard())
            return
        if text == "SYSTEM CONFIGURATION":
            context.user_data["system_config_mode"] = "main"
            await update.message.reply_text("⚙️ <b>SYSTEM CONFIGURATION</b>", parse_mode="HTML", reply_markup=system_config_keyboard())
            return
        if text == "BOT SETTINGS":
            context.user_data["bot_settings_mode"] = "main"
            await update.message.reply_text("⚙️ <b>BOT SETTINGS</b>", parse_mode="HTML", reply_markup=bot_settings_keyboard())
            return
        if text == "ZENEX CONFIG":
            context.user_data["zenex_config_mode"] = "main"
            await update.message.reply_text("📡 <b>ZENEX CONFIG</b>", parse_mode="HTML", reply_markup=zenex_config_keyboard())
            return
        if text == "SERVICE MANAGEMENT":
            context.user_data["service_mgmt_mode"] = "main"
            await update.message.reply_text("🔧 <b>SERVICE MANAGEMENT</b>", parse_mode="HTML", reply_markup=service_management_keyboard())
            return
        if text == "WITHDRAWAL MANAGEMENT":
            context.user_data["withdrawal_admin_mode"] = "main"
            await update.message.reply_text(f"💸 <b>WITHDRAWAL MANAGEMENT</b>\nMin: <code>{get_min_withdraw():.2f} BDT</code>", parse_mode="HTML", reply_markup=withdrawal_management_keyboard())
            return
        if text in ("⏳ PENDING WITHDRAWALS", "PENDING WITHDRAWALS"):
            await show_pending_withdrawals(update, context)
            return
        if text == "ALL USER ID":
            us = get_all_users()
            buf = io.BytesIO(("\n".join(us) or "None").encode())
            buf.name = "users.txt"
            await update.message.reply_document(buf, caption=f"👥 Total Users: {len(us)}", reply_markup=user_management_keyboard())
            return
        if text == "ALL USER BALANCE":
            udb = load_data(USER_DATA_FILE)
            tot = sum(float(v.get("balance", 0)) for v in udb.values())
            lines = [f"{k}: {float(v.get('balance', 0)):.2f} BDT" for k, v in udb.items()]
            buf = io.BytesIO(("\n".join(lines) or "None").encode())
            buf.name = "balances.txt"
            await update.message.reply_document(buf, caption=f"💰 Total Balance: {tot:.2f} BDT", reply_markup=user_management_keyboard())
            return
        if text == "TODAY ALL STATUS":
            tn, to, sn, so, totn, toto = get_global_system_stats()
            await update.message.reply_text(f"📊 <b>SYSTEM STATUS</b>\nToday: 📱 {tn} | 🔑 {to}\n7D: 📱 {sn} | 🔑 {so}\nAll: 📱 {totn} | 🔑 {toto}", parse_mode="HTML", reply_markup=system_config_keyboard())
            return
        if text == "BAN USER LIST":
            bl = load_banned_users()
            await update.message.reply_text("🚫 <b>BANNED USERS</b>\n" + ("\n".join(bl) if bl else "None"), parse_mode="HTML", reply_markup=system_config_keyboard())
            return
        if text == "BAN USER":
            context.user_data["admin_ban_mode"] = True
            await update.message.reply_text("🚫 Send User ID to ban:", reply_markup=cancel_keyboard())
            return
        if text == "UNBAN USER":
            context.user_data["admin_unban_mode"] = True
            await update.message.reply_text("✅ Send User ID to unban:", reply_markup=cancel_keyboard())
            return
        if text == "ADD BALANCE":
            context.user_data["add_balance_mode"] = True
            await update.message.reply_text("💰 Send: <code>USER_ID AMOUNT</code>", parse_mode="HTML", reply_markup=cancel_keyboard())
            return
        if text == "REMOVE BALANCE":
            context.user_data["remove_balance_mode"] = True
            await update.message.reply_text("💸 Send: <code>USER_ID AMOUNT</code>", parse_mode="HTML", reply_markup=cancel_keyboard())
            return
        if text == "SEND MESSAGE TO ALL USERS":
            context.user_data["broadcast_mode"] = True
            await update.message.reply_text("📣 Send broadcast message:", reply_markup=cancel_keyboard())
            return
        if text == "VIEW ZENEX CONFIG":
            s = load_settings()
            await update.message.reply_text(f"🔑 Key: <code>{html.escape(str(s.get('zenex_api_key', ''))[:16])}...</code>\n🌐 URL: <code>{html.escape(str(s.get('zenex_base_url', '')))}</code>", parse_mode="HTML", reply_markup=zenex_config_keyboard())
            return
        if text == "SET API KEY":
            context.user_data["zenex_config_mode"] = "set_api_key"
            await update.message.reply_text("🔑 Send new API key:", reply_markup=cancel_keyboard())
            return
        if text == "SET BASE URL":
            context.user_data["zenex_config_mode"] = "set_base_url"
            await update.message.reply_text("🌐 Send new Base URL:", reply_markup=cancel_keyboard())
            return
        if text == "SET MINIMUM WITHDRAW":
            context.user_data["withdrawal_admin_mode"] = "set_minimum"
            await update.message.reply_text("📉 Send new minimum withdraw amount:", reply_markup=cancel_keyboard())
            return

        if context.user_data.get("admin_ban_mode"):
            context.user_data["admin_ban_mode"] = False
            if text.isdigit() and ban_user(int(text)):
                await update.message.reply_text(f"✅ Banned <code>{text}</code>", parse_mode="HTML", reply_markup=system_config_keyboard())
            return
        if context.user_data.get("admin_unban_mode"):
            context.user_data["admin_unban_mode"] = False
            if text.isdigit() and unban_user(int(text)):
                await update.message.reply_text(f"✅ Unbanned <code>{text}</code>", parse_mode="HTML", reply_markup=system_config_keyboard())
            return
        if context.user_data.get("add_balance_mode") or context.user_data.get("remove_balance_mode"):
            is_add = bool(context.user_data.get("add_balance_mode"))
            context.user_data["add_balance_mode"] = False
            context.user_data["remove_balance_mode"] = False
            parts = text.split()
            if len(parts) == 2 and parts[0].isdigit():
                try:
                    amt = float(parts[1])
                    nb = await update_db_balance(int(parts[0]), amt if is_add else -amt)
                    await update.message.reply_text(f"✅ Updated balance: <b>{nb:.2f} BDT</b>", parse_mode="HTML", reply_markup=system_config_keyboard())
                except Exception:
                    pass
            return
        if context.user_data.get("broadcast_mode"):
            context.user_data["broadcast_mode"] = False
            ok = fail = 0
            for u_s in get_all_users():
                try:
                    await context.bot.copy_message(int(u_s), update.message.chat_id, update.message.message_id)
                    ok += 1
                except Exception:
                    fail += 1
            await update.message.reply_text(f"✅ Sent: {ok} | Failed: {fail}", reply_markup=user_management_keyboard())
            return
        if context.user_data.get("zenex_config_mode") == "set_api_key":
            context.user_data["zenex_config_mode"] = "main"
            s = load_settings()
            s["zenex_api_key"] = text
            save_settings(s)
            await update.message.reply_text("✅ API Key updated!", reply_markup=zenex_config_keyboard())
            return
        if context.user_data.get("zenex_config_mode") == "set_base_url":
            context.user_data["zenex_config_mode"] = "main"
            s = load_settings()
            s["zenex_base_url"] = clean_base_url(text)
            save_settings(s)
            await update.message.reply_text("✅ Base URL updated!", reply_markup=zenex_config_keyboard())
            return
        if context.user_data.get("withdrawal_admin_mode") == "set_minimum":
            context.user_data["withdrawal_admin_mode"] = "main"
            try:
                s = load_settings()
                s["min_withdraw"] = float(text)
                save_settings(s)
                await update.message.reply_text("✅ Minimum withdraw updated!", reply_markup=withdrawal_management_keyboard())
            except Exception:
                pass
            return

    if context.user_data.get("withdraw_mode") == "select_method" and text in ("BKASH", "NAGAD", "ROCKET", "BINANCE"):
        context.user_data["withdraw_method"] = text
        context.user_data["withdraw_mode"] = "amount"
        await update.message.reply_text(f"💸 Send amount (Min: {get_min_withdraw():.2f} BDT):", reply_markup=cancel_keyboard())
        return
    if context.user_data.get("withdraw_mode") == "amount":
        try:
            amt = float(text)
            if amt < get_min_withdraw() or amt > get_user(uid)["balance"]:
                await update.message.reply_text("🚫 Invalid or insufficient balance!", reply_markup=cancel_keyboard())
                return
            context.user_data["withdraw_amount"] = amt
            context.user_data["withdraw_mode"] = "number"
            await update.message.reply_text("📞 Send payment number (017XXXXXXXX):", reply_markup=cancel_keyboard())
        except Exception:
            await update.message.reply_text("⚠️ Send valid amount!", reply_markup=cancel_keyboard())
        return
    if context.user_data.get("withdraw_mode") == "number":
        if not is_valid_bangladesh_number(text):
            await update.message.reply_text("⚠️ Send valid 11-digit number!", reply_markup=cancel_keyboard())
            return
        pid = generate_payment_id()
        context.user_data["temp_withdraw"] = {"method": context.user_data.get("withdraw_method"), "amount": context.user_data.get("withdraw_amount"), "number": text, "payment_id": pid}
        await update.message.reply_text(
            pe(f"📝 Method: {context.user_data.get('withdraw_method')}\n📞 Number: {text}\n💰 Amount: {context.user_data.get('withdraw_amount'):.2f} BDT"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ CANCEL", callback_data="withdraw_cancel", style="primary"),
                InlineKeyboardButton("✅ CONFIRM", callback_data="withdraw_confirm", style="primary"),
            ]]),
        )
        return

    if context.user_data.get("mode") == "custom_range":
        context.user_data["mode"] = None
        live_nums = await fetch_live_numbers_for_range(text.upper(), limit=8)
        if not live_nums:
            await update.message.reply_text("❌ No live numbers found for this range.", reply_markup=main_keyboard(uid))
            return
        context.user_data["live_numbers_list"] = live_nums
        context.user_data["live_numbers_app"] = "Custom"
        context.user_data["live_numbers_range"] = text.upper()
        rows = [[InlineKeyboardButton(f"🟢 +{n}", callback_data=f"pick_live_{i}", api_kwargs={"style": "primary"})] for i, n in enumerate(live_nums)]
        await update.message.reply_text(pe(f"🟢 <b>LIVE NUMBERS FOR <code>{html.escape(text.upper())}</code></b>"), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return

    if context.user_data.get("mode") == "get_2fa":
        context.user_data["mode"] = None
        try:
            key = base64.b32decode(text.replace(" ", "").upper(), casefold=True)
            t_val = int(time.time()) // 30
            h = hmac.new(key, struct.pack(">Q", t_val), hashlib.sha1).digest()
            o = h[-1] & 0xF
            code = f"{((struct.unpack('>I', h[o:o+4])[0] & 0x7FFFFFFF) % 1_000_000):06d}"
            await update.message.reply_text(pe(f"✅ <b>2FA CODE:</b> <code>{code}</code>"), parse_mode="HTML", reply_markup=main_keyboard(uid))
        except Exception:
            await update.message.reply_text("❌ Invalid 2FA key.", reply_markup=main_keyboard(uid))
        return

    if text == "GET NUMBER":
        await show_app_selection(update, context)
        return
    if text == "GET 2FA":
        await get_2fa_code(update, context)
        return
    if text == "PROFILE":
        u = get_user(uid, update.effective_user)
        st = get_user_stats(uid)
        await update.message.reply_text(
            pe(f"👤 <b>PROFILE</b>\n🆔 <code>{uid}</code>\n💵 Balance: <b>{float(u.get('balance', 0)):.2f} BDT</b>\n📱 Today: {st['today_numbers']} | 🔑 OTPs: {st['today_otps']}"),
            parse_mode="HTML",
            reply_markup=account_keyboard(),
        )
        return
    if text == "LEADERBOARD":
        await leaderboard_command(update, context)
        return
    if text == "SUPPORT":
        context.user_data["support_mode"] = True
        await update.message.reply_text(f"🆘 Support: {SUPPORT_LINK}\n\n💬 অথবা আপনার মেসেজ এখানে লিখুন:", reply_markup=cancel_keyboard())
        return

    await update.message.reply_text("🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(uid))

# ==================== RENDER HEALTH SERVER & MAIN ====================

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args):
        pass

def _start_keepalive_server():
    port = int(os.environ.get("PORT", 10000))
    server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"🌐 Port {port} bound for Render")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"⚠️ Telegram error: {context.error}")

async def post_init(application):
    for _ in range(MAX_WORKERS):
        asyncio.create_task(worker())
    asyncio.create_task(monitor_loop(application))
    asyncio.create_task(_bg_refresh_ranges())

async def post_shutdown(application):
    await client_async.aclose()

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured.")
    _start_keepalive_server()
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .get_updates_write_timeout(30.0)
        .get_updates_pool_timeout(30.0)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get1number", lambda u, c: show_app_selection(u, c)))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))

    print("🚀 BOT RUNNING...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=2.0,
        timeout=30,
    )

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    main()
