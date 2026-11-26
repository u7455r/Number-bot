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
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

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

# ==================== ADMIN CONFIGURATION ====================

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
    "telegram": "\u2708\ufe0f", "instagram": "\U0001f4f7", "facebook": "\U0001f535",
    "tiktok": "\U0001f3b5", "x": "\u274c", "whatsapp": "\U0001f4ac",
    "up": "\U0001f4c8", "down": "\U0001f4c9", "add": "\u2795", "setting": "\u2699\ufe0f",
    "1st": "\U0001f947", "2st": "\U0001f948", "3rd": "\U0001f949", "free": "\U0001f193",
    "msg": "\U0001f4ac", "link": "\U0001f517", "status": "\U0001f4ca", "home": "\U0001f3e0",
    "gift_box": "\U0001f381", "delete": "\U0001f5d1\ufe0f", "number_change": "\U0001f504",
    "get_number_btn": "\U0001f4de", "cross": "\u274c", "stop": "\U0001f6d1",
    "ban": "\U0001f6ab", "loading": "\u23f3", "profile": "\U0001f464", "done": "\u2705",
    "otp_success": "\u2b50", "nagad": "\U0001f7e0", "bkash": "\U0001f496",
    "rocket": "\U0001f680", "binance": "\U0001f7e1", "live": "\U0001f7e2",
    "developer": "\U0001f468\u200d\U0001f4bb", "channel": "\U0001f4e2",
    "copy": "\U0001f4cb", "admin": "\U0001f451", "waiting": "\u23f3", "back": "\U0001f519",
    "leader_board": "\U0001f3c6", "custom_range": "\U0001f3af", "refer_btn": "\U0001f517",
    "paypal": "\U0001f4b3", "imo": "\U0001f4ac", "hi": "\U0001f44b", "off": "\U0001f6d1",
    "diamond": "\U0001f48e", "broadcast": "\U0001f4e2", "key": "\U0001f511", "tk": "\u09f3",
    "roket": "\U0001f680", "all_done": "\u2705", "yes": "\u2714\ufe0f", "no": "\u274c",
    "fire_love": "\u2764\ufe0f",
}

PREMIUM_FLAGS = {
    "\U0001f1fa\U0001f1f8": "5913463998522592692",
    "\U0001f1fa\U0001f1e6": "5911406692007941050",
    "\U0001f1f5\U0001f1f1": "5913550391789752571",
    "\U0001f1f0\U0001f1ff": "5913724621433082323",
    "\U0001f1e6\U0001f1ff": "5911197578640233518",
    "\U0001f1ea\U0001f1fa": "5911106310585193018",
    "\U0001f1e6\U0001f1f2": "5913272455866093666",
    "\U0001f1f7\U0001f1fa": "5913274246867456342",
    "\U0001f1fa\U0001f1ff": "5911051846104912282",
    "\U0001f1e9\U0001f1ea": "5911096835887337583",
    "\U0001f1ef\U0001f1f5": "5913293711659241040",
    "\U0001f1f9\U0001f1f7": "5910995113881901195",
    "\U0001f1e7\U0001f1fe": "5911011185649521599",
    "\U0001f1ec\U0001f1e7": "5913443365499703513",
    "\U0001f1ee\U0001f1f3": "5913754823643107921",
    "\U0001f1e7\U0001f1f7": "5911148568768418614",
    "\U0001f1fe\U0001f1ea": "5913346492512341993",
    "\U0001f1fb\U0001f1f3": "5913428887164949581",
    "\U0001f1e6\U0001f1ea": "5913726554168365343",
    "\U0001f1fa\U0001f1ec": "5913488939397681980",
    "\U0001f1f9\U0001f1f2": "5913315521503170180",
    "\U0001f1f9\U0001f1f3": "5911332947419468671",
    "\U0001f1f9\U0001f1ed": "5913617968805187987",
    "\U0001f1f9\U0001f1ff": "5911418949844603556",
    "\U0001f1f8\U0001f1ea": "5911156510162949403",
    "\U0001f1f8\U0001f1e9": "5911387497799094470",
    "\U0001f1ea\U0001f1f8": "5911193287967904547",
    "\U0001f1f1\U0001f1f0": "5911293163137406640",
    "\U0001f1ff\U0001f1e6": "5911203119148044594",
    "\U0001f1f8\U0001f1ec": "5911531460808051849",
    "\U0001f1f7\U0001f1f8": "5913592598433369871",
    "\U0001f1f8\U0001f1f3": "5910995302860461643",
    "\U0001f1f6\U0001f1e6": "5911260864983339619",
    "\U0001f1f5\U0001f1f9": "5911023653939581472",
    "\U0001f1f5\U0001f1ed": "5911268638874145162",
    "\U0001f1f5\U0001f1ea": "5911207993935925780",
    "\U0001f1f5\U0001f1f0": "5913705895375672082",
    "\U0001f1f4\U0001f1f2": "5913570801474343473",
    "\U0001f1f3\U0001f1f4": "5913617397574537046",
    "\U0001f1f3\U0001f1ec": "5911143844304393105",
    "\U0001f1f3\U0001f1ff": "5913640044937089340",
    "\U0001f1f3\U0001f1f1": "5913367645226275100",
    "\U0001f1f3\U0001f1f5": "5913496520014958723",
    "\U0001f1f2\U0001f1e6": "5911482111633658301",
    "\U0001f1f2\U0001f1f3": "5911041383564580038",
    "\U0001f1f2\U0001f1e9": "5913456847402045950",
    "\U0001f1f2\U0001f1fd": "5913687302462246518",
    "\U0001f1f2\U0001f1fe": "5913654360063087453",
    "\U0001f1f0\U0001f1ea": "5911154710571651231",
    "\U0001f1f1\U0001f1f9": "5911172315642597775",
    "\U0001f1f1\U0001f1fb": "5913738489882480243",
    "\U0001f1f1\U0001f1e7": "5911504273664905447",
    "\U0001f1ee\U0001f1e9": "5913479361620611038",
    "\U0001f1ee\U0001f1f7": "5911308891307643032",
    "\U0001f1ee\U0001f1f6": "5911382442622587735",
    "\U0001f1ee\U0001f1f1": "5911471936856134692",
    "\U0001f1ee\U0001f1f9": "5913688444923547525",
    "\U0001f1ed\U0001f1fa": "5913767635530551104",
    "\U0001f1ec\U0001f1f7": "5911210399117611448",
    "\U0001f1ec\U0001f1ed": "5913391155877252952",
    "\U0001f1ec\U0001f1ea": "5913434771270144023",
    "\U0001f1eb\U0001f1f7": "5913605586414473124",
    "\U0001f1eb\U0001f1ee": "5911041344909873378",
    "\U0001f1ea\U0001f1f9": "5911078333168227043",
    "\U0001f1ea\U0001f1ec": "5913694831539916769",
    "\U0001f1e9\U0001f1f0": "5911206009661034712",
    "\U0001f1e8\U0001f1fe": "5911023550860366409",
    "\U0001f1ed\U0001f1f7": "5913692684056269311",
    "\U0001f1e8\U0001f1f3": "5913779335021466780",
    "\U0001f1e7\U0001f1e9": "5911365056594973179",
    "\U0001f1e7\U0001f1ea": "5913529642802745141",
    "\U0001f1e6\U0001f1fa": "5913632326880858455",
    "\U0001f1e6\U0001f1f9": "5911338831524664592",
    "\U0001f1e6\U0001f1f7": "5913573356979884082",
    "\U0001f1f0\U0001f1f7": "5913371673905598425",
    "\U0001f1f8\U0001f1e6": "4985897134424328239",
    "\U0001f1e8\U0001f1f4": "5913773060074246009",
    "\U0001f1e8\U0001f1f1": "5911470957603592832",
    "\U0001f1ff\U0001f1f2": "5913564754160389778",
}

def get_tg_emoji(key, default_char=""):
    emoji_id = EMOJI_ID_MAP.get(key)
    fallback = default_char or FALLBACK_EMOJI_MAP.get(key, "\u2b50")
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
        "allowed_services": ["Instagram","Facebook","WhatsApp","TikTok","Telegram","Discord","PayPal","Imo"],
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
                data[k] = v; updated = True
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
    return (env_api_key or configured_api_key,
            clean_base_url(settings.get("zenex_base_url","https://api.zenexnetwork.com")))

def get_api_urls(base_url):
    base = str(base_url).strip().rstrip('/')
    return {"getnum": f"{base}/v1/getnum",
            "liveaccess": f"{base}/v1/active-ranges",
            "otp": f"{base}/v1/numsuccess/info"}

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
    for k, v in [("facebook","Facebook"),("instagram","Instagram"),("whatsapp","WhatsApp"),
                  ("tiktok","TikTok"),("paypal","PayPal"),("telegram","Telegram"),
                  ("discord","Discord"),("imo","Imo")]:
        if k in n: return v
    return raw.strip().capitalize()

def make_bold_text(text):
    out = []
    for ch in str(text):
        o = ord(ch)
        if 65 <= o <= 90:    out.append(chr(o - 65 + 0x1D5D4))
        elif 97 <= o <= 122: out.append(chr(o - 97 + 0x1D5EE))
        elif 48 <= o <= 57:  out.append(chr(o - 48 + 0x1D7EC))
        else: out.append(ch)
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

async def fetch_top55_ranges_by_app():
    settings = load_settings()
    api_key, base_url = get_api_credentials()
    allowed = {s.lower() for s in settings.get("allowed_services",
        ["Instagram","Facebook","WhatsApp","TikTok","Telegram","Discord","PayPal","Imo"])}
    urls = get_api_urls(base_url)
    headers = get_api_headers(api_key)
    ranges_list = None
    for attempt in range(2):
        try:
            r = await client_async.get(urls["liveaccess"], headers=headers,
                                        timeout=httpx.Timeout(5.0, connect=1.5))
            data = r.json()
            ranges_list = extract_active_ranges(data)
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
            rng = obj.strip()
            service = "Unknown"
        elif isinstance(obj, dict):
            rng = (
                obj.get("range") or obj.get("prefix") or
                obj.get("range_text") or obj.get("value") or ""
            )
            service = (
                obj.get("service") or obj.get("app") or
                obj.get("application") or obj.get("service_name") or "Unknown"
            )
            explicit_cnt = _extract_range_count(obj)
        else:
            continue

        rng = str(rng).strip().upper()
        if not rng or not re.search(r"\d", rng):
            continue
        clean = get_clean_app_name(str(service))
        if clean.lower() not in allowed and clean != "Unknown":
            continue
        if clean not in top:
            top[clean] = {"icon": get_platform_icon(clean), "ranges": [], "range_counts": {}}
        if rng not in top[clean]["ranges"]:
            top[clean]["ranges"].append(rng)
        prev_c = top[clean]["range_counts"].get(rng, 0)
        add_c = explicit_cnt if explicit_cnt is not None else 1
        top[clean]["range_counts"][rng] = max(prev_c, add_c) if explicit_cnt is not None else (prev_c + 1)

    return dict(sorted(top.items(), key=lambda x: len(x[1]["ranges"]), reverse=True)), None

def extract_active_ranges(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return None

    for key in (
        "active_ranges", "activeRanges", "available_ranges",
        "availableRanges", "ranges", "range_list",
    ):
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
            else:
                item = {"service": service, "range": value}
            grouped.append(item)
    return grouped if grouped else None

def build_app_buttons_from_cache(top):
    btns, row, ci = [], [], 0
    clrs = ["primary"]
    for app_name, app_info in top.items():
        r_counts = app_info.get("range_counts", {})
        total_active = sum(r_counts.values()) if r_counts else len(app_info.get("ranges", []))
        btn_label = f"{make_bold_text(app_name)} ({total_active})"
        row.append(InlineKeyboardButton(
            btn_label,
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
                except Exception:
                    pass
                finally:
                    _ranges_cache["fetching"] = False
        except Exception:
            pass
        await asyncio.sleep(200)

# ==================== CHECK IF USER IS ADMIN ====================

def is_admin(user_id):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return False
    return user_id in get_admin_ids()

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
            admin_id = int(candidate)
        except (TypeError, ValueError):
            continue
        if admin_id > 0 and admin_id not in admin_ids:
            admin_ids.append(admin_id)
    return admin_ids

async def notify_admin_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE, referrer_id=None, is_re_start=False):
    user = update.effective_user
    if not user:
        return
    uid = user.id
    full_name = html.escape(user.full_name or "Unknown")
    username = html.escape(f"@{user.username}" if user.username else "No username")
    total_users = len(load_data(USER_DATA_FILE))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_lbl = "🆕 NEW USER STARTED BOT" if not is_re_start else "🔄 USER RE-STARTED BOT"
    ref_line = f"<code>{referrer_id}</code>" if referrer_id else "Direct (None)"

    msg = (
        f"🔔 <b>{status_lbl}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b> {full_name}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>User ID:</b> <code>{uid}</code>\n"
        f"👥 <b>Referral By:</b> {ref_line}\n"
        f"📊 <b>Total Users:</b> <b>{total_users}</b>\n"
        f"⏰ <b>Time:</b> {now_str}"
    )

    for admin_id in get_admin_ids():
        try:
            await context.bot.send_message(chat_id=admin_id, text=pe(msg), parse_mode="HTML")
        except Exception as e:
            print(f"Admin new user notify fail ({admin_id}): {e}")

def get_min_withdraw():
    try:
        return max(0.0, float(load_settings().get("min_withdraw", MIN_WITHDRAW)))
    except (TypeError, ValueError):
        return float(MIN_WITHDRAW)

# ==================== WITHDRAW DATA FUNCTIONS ====================

def load_withdraw_requests():
    if not os.path.exists(WITHDRAW_DATA_FILE):
        with open(WITHDRAW_DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(WITHDRAW_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_withdraw_requests(data):
    with open(WITHDRAW_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_payment_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

# ==================== BANNED USERS FUNCTIONS ====================

def load_banned_users():
    if not os.path.exists(BANNED_USERS_FILE):
        with open(BANNED_USERS_FILE, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(BANNED_USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_banned_users(banned_list):
    with open(BANNED_USERS_FILE, "w") as f:
        json.dump(banned_list, f, indent=4)

def is_user_banned(uid):
    banned_list = load_banned_users()
    return str(uid) in banned_list

def ban_user(uid):
    banned_list = load_banned_users()
    uid_str = str(uid)
    if uid_str not in banned_list:
        banned_list.append(uid_str)
        save_banned_users(banned_list)
        return True
    return False

def unban_user(uid):
    banned_list = load_banned_users()
    uid_str = str(uid)
    if uid_str in banned_list:
        banned_list.remove(uid_str)
        save_banned_users(banned_list)
        return True
    return False

# ==================== REFERRAL DATA FUNCTIONS ====================

def load_referral_data():
    if not os.path.exists(REFERRAL_DATA_FILE):
        with open(REFERRAL_DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(REFERRAL_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_referral_data(data):
    with open(REFERRAL_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_referral_count(uid, count):
    referral_data = load_referral_data()
    uid_str = str(uid)
    if uid_str not in referral_data:
        referral_data[uid_str] = {"referral_count": 0}
    referral_data[uid_str]["referral_count"] = count
    save_referral_data(referral_data)

def get_referral_count(uid):
    referral_data = load_referral_data()
    uid_str = str(uid)
    return referral_data.get(uid_str, {}).get("referral_count", 0)

# ==================== DATA RANGE FILE ====================

def load_range_db():
    if not os.path.exists(DATA_RANGE_FILE):
        return {}
    try:
        with open(DATA_RANGE_FILE, "r") as f:
            return json.load(f)
    except:
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
        "country": f"{flag} {name}"
    }
    save_range_db(db)

# ==================== COUNTRY MAPPING SECTION ====================

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

# ==================== SERVICE DETECTION SECTION ====================

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
    keyboard = [
        [make_reply_btn("BALANCE",        emoji_id="6233367447789899509", style="primary"),
         make_reply_btn("REFER AND EARN", emoji_id="5420396762189831222", style="primary")],
        [make_reply_btn("VIEW PROFILE",   emoji_id="5422444280473998663", style="primary"),
         make_reply_btn("BACK TO MAIN",   emoji_id="5267490665117275176", style="primary")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def cancel_keyboard():
    return ReplyKeyboardMarkup([[make_reply_btn("CANCEL", emoji_id="5420130255174145507", style="primary")]], resize_keyboard=True)

def admin_main_keyboard():
    keyboard = [
        [make_reply_btn("USER MANAGEMENT",      emoji_id="5193063022226086560", style="primary"),
         make_reply_btn("SYSTEM CONFIGURATION", emoji_id="5341715473882955310", style="primary")],
        [make_reply_btn("BOT SETTINGS",         emoji_id="5282843764451195532", style="primary"),
         make_reply_btn("SERVICE MANAGEMENT",   emoji_id="5375338737028841420", style="primary")],
        [make_reply_btn("WITHDRAWAL MANAGEMENT",emoji_id="6233367447789899509", style="primary"),
         make_reply_btn("SUPPORT CHAT",           emoji_id="5267294466716244344", style="primary")],
        [make_reply_btn("⏳ PENDING WITHDRAWALS",emoji_id="6217721388736712699", style="primary")],
        [make_reply_btn("BACK TO MAIN",         emoji_id="5267490665117275176", style="primary")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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

# ==================== HELPER & DB FUNCTIONS ====================

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
    if len(num) > 6:
        return f"{num[:4]}****{num[-6:]}"
    return num

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
    except:
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
    data = load_data(USER_DATA_FILE)
    return str(uid) in data

def load_stats():
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def add_number_taken(uid, count=1):
    uid = str(uid)
    stats = load_stats()
    if uid not in stats:
        stats[uid] = {"numbers_taken": [], "otps_received": []}
    now = datetime.now().isoformat()
    for _ in range(count):
        stats[uid]["numbers_taken"].append(now)
    log_global_activity(uid, "NUMBER_TAKEN", {"count": count})
    save_stats(stats)

def add_otp_received(uid):
    uid = str(uid)
    stats = load_stats()
    if uid not in stats:
        stats[uid] = {"numbers_taken": [], "otps_received": []}
    stats[uid]["otps_received"].append(datetime.now().isoformat())
    save_stats(stats)

def get_user_stats(uid):
    uid = str(uid)
    stats = load_stats()
    user_stats = stats.get(uid, {"numbers_taken": [], "otps_received": []})
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

def log_global_activity(uid, action, details):
    if not os.path.exists(ACTIVITY_LOGS_FILE):
        with open(ACTIVITY_LOGS_FILE, "w") as f:
            json.dump([], f)
    try:
        with open(ACTIVITY_LOGS_FILE, "r") as f:
            logs = json.load(f)
    except:
        logs = []
    now = datetime.now()
    logs.append({
        "uid": str(uid), "action": action, "details": details,
        "timestamp": now.isoformat(), "date": now.strftime("%d/%m/%Y"), "time": now.strftime("%H:%M:%S")
    })
    with open(ACTIVITY_LOGS_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def get_global_system_stats():
    stats = load_stats()
    now = datetime.now()
    today_midnight = datetime(now.year, now.month, now.day)
    last_7d = now - timedelta(days=7)
    total_n = total_o = today_n = today_o = seven_n = seven_o = 0
    for uid in stats:
        u = stats[uid]
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
        for idx, (uid_str, count, name) in enumerate(top10, 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, f"{idx}️⃣")
            msg += f"{medal} <b>{name}</b>\n   🔑 <code>{count}</code> OTPs\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n📊 <i>প্রতিদিন রাত ১২টায় রিসেট হয়</i>"
    await update.message.reply_text(pe(msg), parse_mode="HTML", reply_markup=main_keyboard(uid))

def generate_2fa_code(secret_key):
    try:
        clean_secret = secret_key.replace(" ", "").upper().strip()
        key = base64.b32decode(clean_secret, casefold=True)
        t = int(time.time()) // 30
        h = hmac.new(key, struct.pack(">Q", t), hashlib.sha1).digest()
        o = h[-1] & 0xf
        code = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1_000_000
        return f"{code:06d}", clean_secret
    except:
        return None, None

async def get_2fa_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    context.user_data["mode"] = "get_2fa"
    await update.message.reply_text(pe("⚡ <b>GET 2FA CODE</b> ⚡\n\n<blockquote>🔑 ENTER YOUR 2FA SECRET KEY:</blockquote>"), parse_mode="HTML")

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
    await update.message.reply_text(pe(final_msg), parse_mode="HTML")

def build_manual_service_buttons():
    s = load_settings()
    manual = s.get("manual_services", [])
    btns = []
    for i, svc in enumerate(manual):
        total_cnt = sum(len(c.get("ranges", [])) for c in svc.get("countries", []))
        btns.append(InlineKeyboardButton(
            f"{make_bold_text(svc['name'])} ({total_cnt})",
            callback_data=f"manual_svc_{i}",
            api_kwargs={"icon_custom_emoji_id": get_app_emoji_id(svc['name']), "style": "primary"}
        ))
    return [btns[j:j+2] for j in range(0, len(btns), 2)]

async def show_app_selection(update, context):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    context.user_data.pop("top_ranges_by_app", None)

    async def _build_full_keyboard(top):
        zenex_rows = build_app_buttons_from_cache(top)
        manual_rows = build_manual_service_buttons()
        all_rows = zenex_rows + manual_rows
        all_rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range", api_kwargs={"style": "primary"})])
        return all_rows

    cache_age = time.monotonic() - _ranges_cache["updated_at"]
    if _ranges_cache["data"] and cache_age < 300:
        top = _ranges_cache["data"]
        context.user_data["top_ranges_by_app"] = top
        msg = f'{get_tg_emoji("get_number_btn")} <b>SELECT APP TO GET NUMBER</b>\n━━━━━━━━━━━━━━━━━━━━━'
        kb = await _build_full_keyboard(top)
        await update.message.reply_text(pe(msg), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        return

    status = await update.message.reply_text(pe(f'{get_tg_emoji("loading")} <b>Loading ranges...</b>'), parse_mode="HTML")
    top, err = await fetch_top55_ranges_by_app()
    if err or not top:
        top, err = await fetch_top55_ranges_by_app()
    if err or not top:
        manual_rows = build_manual_service_buttons()
        if manual_rows:
            manual_rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range", api_kwargs={"style": "primary"})])
            await status.edit_text(pe(f'{get_tg_emoji("get_number_btn")} <b>SELECT APP TO GET NUMBER</b>\n━━━━━━━━━━━━━━━━━━━━━'), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(manual_rows))
        else:
            await status.edit_text(pe(f'{get_tg_emoji("stop")} No active ranges available right now.'), parse_mode="HTML")
        return

    _ranges_cache["data"] = top
    _ranges_cache["updated_at"] = time.monotonic()
    context.user_data["top_ranges_by_app"] = top
    msg = f'{get_tg_emoji("get_number_btn")} <b>SELECT APP TO GET NUMBER</b>\n━━━━━━━━━━━━━━━━━━━━━'
    kb = await _build_full_keyboard(top)
    await status.edit_text(pe(msg), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

# ==================== AUTO OTP MONITOR & WORKER ====================

async def monitor_loop(app):
    while True:
        try:
            settings = load_settings()
            api_key, base_url = get_api_credentials()
            urls = get_api_urls(base_url)
            headers = get_api_headers(api_key)
            r = await client_async.get(urls["otp"], headers=headers)
            if r.status_code != 200:
                await asyncio.sleep(5)
                continue
            try:
                res = r.json()
            except Exception:
                await asyncio.sleep(5)
                continue

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
                        if HAS_COPY_BTN:
                            try:
                                btn_copy = InlineKeyboardButton(text=otp_code, copy_text=CopyTextButton(text=otp_code), api_kwargs={"icon_custom_emoji_id": "5296369303661067030"})
                            except Exception:
                                btn_copy = InlineKeyboardButton(otp_code, callback_data=f"copy_text_{otp_code}", api_kwargs={"icon_custom_emoji_id": "5296369303661067030"})
                        else:
                            btn_copy = InlineKeyboardButton(otp_code, callback_data=f"copy_text_{otp_code}", api_kwargs={"icon_custom_emoji_id": "5296369303661067030"})
                        panel_url = settings.get("panel_url", f"https://t.me/Zenex_Number_bot?start={ADMIN_ID}")
                        channel_url = settings.get("channel_url", "https://t.me/MinoXofficial0")
                        masked = mask_number(clean_num)
                        user_msg = f"{flag_tg} {app_em} +{clean_num}"
                        group_msg = f"{flag_tg} {app_em} +{masked}"
                        user_kb = InlineKeyboardMarkup([[btn_copy]])
                        group_kb = InlineKeyboardMarkup([
                            [btn_copy],
                            [InlineKeyboardButton(" NUMBER", url=panel_url, api_kwargs={"icon_custom_emoji_id": "4943094697238201446", "style": "primary"}),
                             InlineKeyboardButton(" CHANNEL", url=channel_url, api_kwargs={"icon_custom_emoji_id": "6215074610845585917", "style": "primary"})]
                        ])
                        try:
                            await app.bot.send_message(details["uid"], pe(user_msg), parse_mode="HTML", reply_markup=user_kb)
                        except Exception:
                            pass
                        try:
                            gid = settings.get("otp_group_chat_id") or OTP_GROUP_ID
                            await app.bot.send_message(gid, pe(group_msg), parse_mode="HTML", reply_markup=group_kb)
                        except Exception:
                            pass
                        save_data(paid_data, PAID_SMS_FILE)

            now = datetime.now()
            for nk in [k for k, v in list(active_numbers.items()) if isinstance(v, dict) and "timestamp" in v and (now - v["timestamp"]).total_seconds() > 3600]:
                del active_numbers[nk]
        except Exception:
            pass
        await asyncio.sleep(CHECK_INTERVAL)

def extract_first_value(payload, keys):
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if value not in (None, "") and isinstance(value, (str, int, float)):
                return value
        for value in payload.values():
            found = extract_first_value(value, keys)
            if found not in (None, ""):
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = extract_first_value(value, keys)
            if found not in (None, ""):
                return found
    return None

def extract_number_from_payload(payload):
    number_keys = ("full_number", "no_plus_number", "phone_number", "phone", "mobile", "msisdn", "number", "copy")
    if isinstance(payload, dict):
        for key in number_keys:
            value = payload.get(key)
            if isinstance(value, (str, int, float)) and len(normalize_number(value)) >= 7:
                return value, payload
        for value in payload.values():
            number, owner = extract_number_from_payload(value)
            if number:
                return number, owner
    elif isinstance(payload, list):
        for value in payload:
            number, owner = extract_number_from_payload(value)
            if number:
                return number, owner
    return None, {}

async def fetch_number_async(range_str):
    range_str = str(range_str or "").strip().upper()
    if not range_str:
        return None
    try:
        api_key, base_url = get_api_credentials()
        urls = get_api_urls(base_url)
        headers = {**get_api_headers(api_key), "Accept": "application/json"}
        r = await client_async.post(
            urls["getnum"],
            json={"range": range_str, "is_national": False, "remove_plus": False},
            headers=headers,
            timeout=httpx.Timeout(8.0, connect=2.0, read=6.0),
        )
        if not 200 <= r.status_code < 300:
            return None
        data = r.json()
        num, number_payload = extract_number_from_payload(data)
        if num:
            otp = extract_first_value(number_payload, ("otp", "otp_code", "code", "verification_code"))
            sms = extract_first_value(number_payload, ("sms", "message", "full_sms", "text"))
            return {"number": num, "otp_now": bool(otp), "otp": otp, "sms": sms}
    except Exception:
        return None
    return None

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

async def fast_allocate_number(query, context, range_text, sid):
    uid = query.from_user.id
    if is_user_banned(uid):
        await query.message.edit_text("🚫 YOU ARE BANNED 🚫")
        return

    res = None
    clean_num = None
    for _ in range(3):
        res = await fetch_number_async(range_text)
        if not res or not res.get("number"):
            break
        clean_num = await register_active_number(uid, res["number"], range_text, sid)
        if clean_num:
            break

    if not res or not clean_num:
        await query.message.edit_text(
            pe("❌ <b>Number পাওয়া যায়নি।</b>\n\n<blockquote>⚠️ এই range-এ এখন number নেই বা server busy।\nআরেকটি range চেষ্টা করুন।</blockquote>"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="back_services", style="primary")]])
        )
        return

    add_number_taken(uid, 1)
    last_range[uid] = range_text
    country_flag, country_name = get_country_info(clean_num)

    if res.get("otp_now") and res.get("otp"):
        otp_safe = html.escape(str(res["otp"]))
        sms_safe = html.escape(str(res.get("sms") or ""))
        otp_bonus = load_settings().get("otp_bonus", OTP_RATE)
        await update_db_balance(uid, otp_bonus)
        add_otp_received(uid)
        log_global_activity(uid, "OTP_RECEIVED", {"number": clean_num, "otp": res["otp"]})
        text = (
            f"✅ <b>YOUR NUMBER</b> ✅\n\n"
            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {html.escape(country_name)}</code></blockquote>\n"
            f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n"
            f"<blockquote>📞 NUMBER: <code>+{clean_num}</code></blockquote>\n"
            f"<blockquote>🔑 OTP: <code>{otp_safe}</code></blockquote>"
            + (f"\n<blockquote>📩 SMS: <code>{sms_safe}</code></blockquote>" if sms_safe else "")
            + f"\n\n<b>✅ OTP RECEIVED! +{otp_bonus:.2f} BDT ADDED</b>"
        )
    else:
        text = (
            f"✅ <b>YOUR NUMBER</b> ✅\n\n"
            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {html.escape(country_name)}</code></blockquote>\n"
            f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n"
            f"<blockquote>📞 NUMBER: <code>+{clean_num}</code></blockquote>\n\n"
            f"<b>📩 SMS STATUS: ⏳ WAITING...</b>"
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 SAME RANGE", callback_data="same_range", style="primary")],
        [InlineKeyboardButton("📢 OTP GROUP", url="https://t.me/volt_x_lite_otp", style="primary")]
    ])
    try:
        await query.message.edit_text(pe(text), parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        print(f"fast_allocate edit error: {e}")

async def process_auto_number(update, context, range_text):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    if is_user_banned(uid):
        await context.bot.send_message(chat_id=chat_id, text="🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    status_msg = await context.bot.send_message(chat_id=chat_id, text="🔍 SEARCHING...")
    try:
        res = await fetch_number_async(range_text)
        generated_num = await register_active_number(uid, res["number"], range_text, detect_service(range_text)) if res and res.get("number") else None
        if not generated_num:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return
        last_range[uid] = range_text
        add_number_taken(uid, 1)
        country_flag, country_name = get_country_info(generated_num)
        final_text = (
            f"✅ <b>YOUR NUMBER DETAILS</b> ✅\n\n"
            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
            f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n\n"
            f"<blockquote>📞 NUMBER: <code>+{generated_num}</code></blockquote>\n\n"
            f"<b>📩 SMS STATUS: ⏳ WAITING...</b>"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 SAME RANGE", callback_data="same_range", style="primary")],
            [InlineKeyboardButton("📢 OTP GROUP", url="https://t.me/volt_x_lite_otp", style="primary")]
        ])
        await status_msg.edit_text(pe(final_text), parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

async def process_numbers(update_or_query, context, range_text, count):
    if isinstance(update_or_query, Update) and update_or_query.callback_query:
        uid = update_or_query.callback_query.from_user.id
        chat_id = update_or_query.callback_query.message.chat_id
    else:
        uid = update_or_query.effective_user.id
        chat_id = update_or_query.effective_chat.id
    if is_user_banned(uid):
        await context.bot.send_message(chat_id=chat_id, text="🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    status_msg = await context.bot.send_message(chat_id=chat_id, text="🔍 SEARCHING . . .")
    try:
        last_range[uid] = range_text
        results = await asyncio.gather(*[fetch_number_async(range_text) for _ in range(count)])
        valid_results = [r for r in results if r and r.get("number")]
        if not valid_results:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return
        num_entries = []
        for r in valid_results:
            clean_num = await register_active_number(uid, r["number"], range_text, r.get("app") or "")
            if clean_num:
                add_number_taken(uid, 1)
                num_entries.append({"num": clean_num, "otp_now": r.get("otp_now", False), "otp": r.get("otp"), "sms": r.get("sms")})
        if not num_entries:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return
        country_flag, country_name = get_country_info(num_entries[0]["num"])
        num_list_text = "\n".join(f"<blockquote>📞 NUMBER: <code>+{e['num']}</code></blockquote>" for e in num_entries)
        final_text = (
            f"✅ <b>YOUR NUMBER DETAILS</b> ✅\n\n"
            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
            f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n\n"
            f"{num_list_text}\n\n"
            f"<b>📩 SMS STATUS: ⏳ WAITING...</b>"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 SAME RANGE", callback_data="same_range", style="primary")],
            [InlineKeyboardButton("📢 OTP GROUP", url="https://t.me/volt_x_lite_otp", style="primary")]
        ])
        await status_msg.edit_text(pe(final_text), parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        await status_msg.edit_text(f"❌ System Error: {str(e)}")

async def perform_otp_search(update, context, target_num):
    uid = str(update.effective_user.id)
    if is_user_banned(int(uid)):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(int(uid)))
        return
    status_msg = await update.message.reply_text("🔍 SEARCHING IN SERVER...")
    try:
        api_key, base_url = get_api_credentials()
        urls = get_api_urls(base_url)
        r = await client_async.get(urls["otp"], headers=get_api_headers(api_key))
        res = r.json()
        raw_otps = res.get("data", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
        if isinstance(raw_otps, dict):
            raw_otps = raw_otps.get("otps") or raw_otps.get("active") or []
        found_otps = [o for o in raw_otps if normalize_number(o.get("number", "")) == target_num]
        if not found_otps:
            await status_msg.edit_text(f"❌ NO OTP FOUND for `+{target_num}`", parse_mode="Markdown")
            return
        await status_msg.delete()
        for o in found_otps:
            full_sms = o.get("message") or o.get("otp") or o.get("sms") or "No Content"
            otp_code = extract_otp(full_sms)
            await update.message.reply_text(pe(f"✅ <b>OTP FOUND</b>\n📞 <code>+{target_num}</code>\n🔑 <code>{html.escape(otp_code)}</code>"), parse_mode="HTML", reply_markup=main_keyboard(int(uid)))
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {e}")

async def worker():
    while True:
        task = await request_queue.get()
        try:
            if task["type"] == "process_numbers":
                await process_numbers(task["update"], task["context"], task["range_text"], task["count"])
            elif task["type"] == "search_otp":
                await perform_otp_search(task["update"], task["context"], task["target_num"])
            elif task["type"] == "auto_number":
                await process_auto_number(task["update"], task["context"], task["range_text"])
        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            request_queue.task_done()

# ==================== START, COMMANDS & CALLBACKS ====================

async def check_force_join(update, context):
    s = load_settings()
    channel = s.get("force_join_channel")
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
    channel_clean = str(channel).lstrip("@")
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ JOIN CHANNEL", url=f"https://t.me/{channel_clean}", style="primary")]])
    await update.message.reply_text(pe("⚠️ <b>FORCE JOIN REQUIRED!</b>\n\n<blockquote>বট ব্যবহার করতে আগে চ্যানেলে জয়েন করুন।</blockquote>"), parse_mode="HTML", reply_markup=btn)
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    uid_str = str(uid)

    existing_data = load_data(USER_DATA_FILE)
    is_new_user = uid_str not in existing_data

    ref_id = None
    args = context.args
    if args:
        param = args[0]
        if is_range_request(param):
            if is_new_user:
                get_user(uid, user)
                await notify_admin_new_user(update, context, is_re_start=False)
            await request_queue.put({"type": "auto_number", "update": update, "context": context, "range_text": param})
            return
        elif is_referral_request(param):
            try:
                cand = int(param)
                if cand != uid and str(cand) in existing_data:
                    ref_id = cand
            except Exception:
                pass

    if is_new_user:
        get_user(uid, user)
        if ref_id is not None:
            new_count = get_referral_count(ref_id) + 1
            update_referral_count(ref_id, new_count)
            await update_db_balance(ref_id, REFERRAL_PRICE)
            log_global_activity(ref_id, "REFERRAL_JOINED", {"referred_user": uid})
            try:
                await context.bot.send_message(
                    ref_id,
                    pe(f"🎉 <b>NEW REFERRAL!</b>\n\n<blockquote>🗝️ ID: <code>{uid}</code>\n💰 REWARD: {format_balance(REFERRAL_PRICE)} BDT\n👥 TOTAL REFERS: {new_count}</blockquote>"),
                    parse_mode="HTML",
                )
            except Exception:
                pass
        await notify_admin_new_user(update, context, referrer_id=ref_id, is_re_start=False)
    else:
        await notify_admin_new_user(update, context, referrer_id=ref_id, is_re_start=True)

    if not await check_force_join(update, context):
        return

    context.user_data.clear()
    await update.message.reply_text(pe(get_welcome_message()), parse_mode="HTML")
    await update.message.reply_text("🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(uid))

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
        if not top or app_name not in top:
            await query.answer("App not found. Please try again.", show_alert=True)
            return
        ranges = top[app_name].get("ranges", [])
        range_counts = top[app_name].get("range_counts", {})
        if not ranges:
            await query.answer("No ranges available for this app right now.", show_alert=True)
            return

        context.user_data["sel_app"] = app_name
        context.user_data["sel_ranges"] = ranges

        # Group active numbers count by country label so each country shows active count
        country_groups = {}
        for i, r in enumerate(ranges):
            prefix = re.sub(r"[xX]+$", "", str(r)).strip()
            pfx_d = re.sub(r"\D", "", prefix)
            flag, cname = get_country_info(pfx_d)
            key = f"{flag} {cname}"
            cnt = range_counts.get(r, 1)
            if key not in country_groups:
                country_groups[key] = {"count": 0, "first_idx": i}
            country_groups[key]["count"] += cnt

        btns = []
        for key, grp in list(country_groups.items())[:24]:
            btns.append(InlineKeyboardButton(
                f"{key} ({grp['count']})",
                callback_data=f"sel_rng_{grp['first_idx']}",
                api_kwargs={"style": "primary"},
            ))

        rows = [btns[j:j+2] for j in range(0, len(btns), 2)]
        rows.append([InlineKeyboardButton("◀️ BACK", callback_data="back_apps", api_kwargs={"style": "primary"})])
        await query.message.edit_text(
            pe(
                f'{get_tg_emoji("get_number_btn")} <b>SELECT COUNTRY</b>\n'
                f'━━━━━━━━━━━━━━━━━━━━━\n'
                f'<blockquote>📱 App: <b>{html.escape(app_name)}</b></blockquote>\n'
                f'<blockquote>🌍 Select your Country (Active Numbers):</blockquote>'
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(rows),
        )
        return

    if data.startswith("sel_rng_"):
        idx = int(data[8:])
        ranges = context.user_data.get("sel_ranges", [])
        app_name = context.user_data.get("sel_app", "")
        if idx >= len(ranges):
            await query.answer("Range not found. Please try again.", show_alert=True)
            return
        await fast_allocate_number(query, context, ranges[idx], app_name)
        return

    if data == "custom_range":
        context.user_data["mode"] = "custom_range"
        await query.message.edit_text(
            pe("⚙️ <b>CUSTOM RANGE</b>\n\n<blockquote>📱 Type your custom range.\nExample: <code>234XXX</code></blockquote>"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ BACK", callback_data="back_apps", api_kwargs={"style": "primary"})]]),
        )
        return

    if data.startswith("manual_svc_"):
        idx = int(data[len("manual_svc_"):])
        s = load_settings()
        manual = s.get("manual_services", [])
        if idx >= len(manual):
            await query.answer("Service not found.", show_alert=True)
            return
        svc = manual[idx]
        countries = svc.get("countries", [])
        if not countries:
            await query.answer("No countries added for this service yet.", show_alert=True)
            return
        btns = []
        for ci, c in enumerate(countries):
            flag = c.get("flag", "🌍")
            cname = c.get("name", "Unknown")
            cnt = len(c.get("ranges", []))
            btns.append(InlineKeyboardButton(f"{flag} {cname} ({cnt})", callback_data=f"manual_cnt_{idx}_{ci}", api_kwargs={"style": "primary"}))
        rows = [btns[j:j+2] for j in range(0, len(btns), 2)]
        rows.append([InlineKeyboardButton("◀️ BACK", callback_data="back_apps", api_kwargs={"style": "primary"})])
        await query.message.edit_text(
            pe(f'🔧 <b>{html.escape(svc["name"])}</b>\n━━━━━━━━━━━━━━━━━━━━━\n<blockquote>📱 App: <b>{html.escape(svc["name"])}</b></blockquote>\n<blockquote>🌍 Select your Country:</blockquote>'),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(rows),
        )
        return

    if data.startswith("manual_cnt_"):
        parts = data.split("_")
        svc_idx, cnt_idx = int(parts[2]), int(parts[3])
        s = load_settings()
        manual = s.get("manual_services", [])
        if svc_idx >= len(manual):
            await query.answer("Service not found.", show_alert=True)
            return
        svc = manual[svc_idx]
        countries = svc.get("countries", [])
        if cnt_idx >= len(countries):
            await query.answer("Country not found.", show_alert=True)
            return
        ranges = countries[cnt_idx].get("ranges", [])
        if not ranges:
            await query.answer("No ranges for this country.", show_alert=True)
            return
        await fast_allocate_number(query, context, random.choice(ranges).strip().upper(), svc["name"])
        return

    if data in ("back_apps", "back_services"):
        top = context.user_data.get("top_ranges_by_app") or (_ranges_cache.get("data") or {})
        manual_rows = build_manual_service_buttons()
        zenex_rows = build_app_buttons_from_cache(top) if top else []
        all_rows = zenex_rows + manual_rows
        all_rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range", api_kwargs={"style": "primary"})])
        msg = f'{get_tg_emoji("get_number_btn")} <b>SELECT APP TO GET NUMBER</b>\n━━━━━━━━━━━━━━━━━━━━━'
        await query.message.edit_text(pe(msg), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(all_rows))
        return

    if data == "same_range":
        r_text = last_range.get(uid)
        if r_text:
            await process_numbers(update, context, r_text, 1)
        return

    if data == "withdraw_start":
        balance = get_user(uid)["balance"]
        min_withdraw = get_min_withdraw()
        if balance < min_withdraw:
            await query.message.reply_text(pe(f"<blockquote>💵 BALANCE: {format_balance(balance)} BDT\n📉 MIN WITHDRAW: {min_withdraw:.2f} BDT</blockquote>"), parse_mode="HTML")
            return
        context.user_data["withdraw_mode"] = "select_method"
        await query.message.reply_text("💳 SELECT YOUR PAYMENT METHOD!", reply_markup=withdraw_method_keyboard())
        return

    if data == "withdraw_confirm":
        await process_withdraw_confirm(update, context)
        return

    if data == "withdraw_cancel":
        await process_withdraw_cancel(update, context)
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    uid = update.effective_user.id
    text = (update.message.text or update.message.caption or "").strip()

    if context.user_data.get("withdraw_mode") == "select_method":
        await withdraw_method_selected(update, context)
        return
    if context.user_data.get("withdraw_mode") == "amount":
        await withdraw_amount_received(update, context)
        return
    if context.user_data.get("withdraw_mode") == "number":
        await withdraw_number_received(update, context)
        return

    if not is_admin(uid) and is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return

    if context.user_data.get("mode") == "custom_range":
        context.user_data["mode"] = None
        await request_queue.put({"type": "process_numbers", "update": update, "context": context, "range_text": text.upper(), "count": 1})
        return

    if context.user_data.get("mode") == "get_2fa":
        await process_2fa_key(update, context)
        return

    if text == "GET NUMBER":
        await show_app_selection(update, context)
        return
    if text == "GET 2FA":
        await get_2fa_code(update, context)
        return
    if text == "LEADERBOARD":
        await leaderboard_command(update, context)
        return
    if text == "PROFILE":
        context.user_data["account_menu"] = True
        await update.message.reply_text(pe("👤 <b>PROFILE MENU</b>"), parse_mode="HTML", reply_markup=account_keyboard())
        return
    if text == "VIEW PROFILE":
        u = get_user(uid, update.effective_user)
        st = get_user_stats(uid)
        await update.message.reply_text(
            pe(f"👤 <b>PROFILE</b>\n🆔 <code>{uid}</code>\n💵 Balance: <b>{format_balance(u.get('balance', 0))} BDT</b>\n📱 Today: {st['today_numbers']} | 🔑 OTPs: {st['today_otps']}"),
            parse_mode="HTML",
            reply_markup=account_keyboard(),
        )
        return
    if text == "BALANCE":
        u = get_user(uid, update.effective_user)
        await update.message.reply_text(
            pe(f"💰 <b>BALANCE:</b> <code>{format_balance(u.get('balance', 0))} BDT</code>"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 WITHDRAW", callback_data="withdraw_start", style="primary")]]),
        )
        return
    if text == "REFER AND EARN":
        await refer_command(update, context)
        return
    if text == "BACK TO MAIN":
        context.user_data.clear()
        await update.message.reply_text("🔙 Back to main menu.", reply_markup=main_keyboard(uid))
        return

    await update.message.reply_text("🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(uid))

async def withdraw_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text == "CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return
    if text in ("BKASH", "NAGAD", "ROCKET", "BINANCE"):
        context.user_data["withdraw_method"] = text
        context.user_data["withdraw_mode"] = "amount"
        await update.message.reply_text(pe(f"💸 SEND AMOUNT (Min: {get_min_withdraw():.2f} BDT):"), parse_mode="HTML", reply_markup=cancel_keyboard())

async def withdraw_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text == "CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return
    try:
        amount = float(text)
    except Exception:
        await update.message.reply_text("⚠️ INVALID AMOUNT!", reply_markup=cancel_keyboard())
        return
    if amount < get_min_withdraw() or amount > get_user(uid)["balance"]:
        await update.message.reply_text("🚫 INVALID OR INSUFFICIENT BALANCE!", reply_markup=cancel_keyboard())
        return
    context.user_data["withdraw_amount"] = amount
    context.user_data["withdraw_mode"] = "number"
    await update.message.reply_text("📞 SEND PAYMENT NUMBER (017XXXXXXXX):", reply_markup=cancel_keyboard())

async def withdraw_number_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    if text == "CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return
    if not is_valid_bangladesh_number(text):
        await update.message.reply_text("⚠️ SEND VALID 11-DIGIT NUMBER!", reply_markup=cancel_keyboard())
        return
    payment_id = generate_payment_id()
    context.user_data["temp_withdraw"] = {
        "method": context.user_data.get("withdraw_method"),
        "amount": context.user_data.get("withdraw_amount"),
        "number": text,
        "payment_id": payment_id,
    }
    await update.message.reply_text(
        pe(f"📝 Method: {context.user_data.get('withdraw_method')}\n📞 Number: {text}\n💰 Amount: {context.user_data.get('withdraw_amount'):.2f} BDT"),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ CANCEL", callback_data="withdraw_cancel", style="primary"),
            InlineKeyboardButton("✅ CONFIRM", callback_data="withdraw_confirm", style="primary"),
        ]]),
    )

async def process_withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    temp = context.user_data.get("temp_withdraw")
    if not temp:
        return
    await update_db_balance(uid, -temp["amount"])
    wr = load_withdraw_requests()
    wr[temp["payment_id"]] = {"user_id": uid, **temp, "status": "pending", "timestamp": datetime.now().isoformat()}
    save_withdraw_requests(wr)
    await query.message.edit_text(pe(f"✅ WITHDRAW REQUEST SUBMITTED\n🆔 <code>{temp['payment_id']}</code>"), parse_mode="HTML")
    for admin_id in get_admin_ids():
        try:
            await context.bot.send_message(admin_id, pe(f"💸 <b>NEW WITHDRAW</b>\n👤 <code>{uid}</code>\n💰 {temp['amount']:.2f} BDT\n📞 <code>{temp['number']}</code>"), parse_mode="HTML")
        except Exception:
            pass
    context.user_data["temp_withdraw"] = None
    context.user_data["withdraw_mode"] = None

async def process_withdraw_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data["temp_withdraw"] = None
    context.user_data["withdraw_mode"] = None
    await query.message.edit_text("❌ WITHDRAW CANCELLED")

async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={uid}"
    cnt = get_referral_count(uid)
    await update.message.reply_text(
        pe(f"🎁 <b>REFER &amp; EARN</b>\n\n🔗 <code>{ref_link}</code>\n👥 Refers: <b>{cnt}</b>"),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

# ==================== RENDER HEALTH SERVER & MAIN SECTION ====================

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
    app.add_handler(CommandHandler("get1number", get1number_command))
    app.add_handler(CommandHandler("searchotp", searchotp_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("refer", refer_command))
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

async def get1number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_app_selection(update, context)

async def searchotp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "search_otp"
    await update.message.reply_text("🔍 **ENTER THE NUMBER TO SEARCH OTP:**", parse_mode="Markdown")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"💰 BALANCE: `{format_balance(get_user(uid)['balance'])} BDT`", parse_mode="Markdown")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = get_user(uid, update.effective_user)
    await update.message.reply_text(f"👤 ID: `{uid}` | Balance: `{format_balance(u['balance'])} BDT`", parse_mode="Markdown")

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    main()
