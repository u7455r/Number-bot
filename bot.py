import asyncio
import io
import re
import json
import html
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx
import pyotp
import random
import string
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
try:
    from telegram import CopyTextButton   # one-tap copy button (needs a recent python-telegram-bot)
except Exception:
    CopyTextButton = None
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

# ==================== CONFIG SECTION ====================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8743808077:AAFKv93Fb0kiBV_0dM71bfn_YTyl5krTEhA")
API_KEY = os.environ.get("API_KEY", "MIAHSMS_93DD67448A88DFE96304F382")
BASE_URL = "https://miahsms.com/bot"           # Your panel domain (without trailing slash)

# ==================== EDIT HERE: ADMINS / GROUP ID / ALL TELEGRAM LINKS ====================
ADMINS = [8298133943]                           # Admin Telegram user IDs
OTP_GROUP_ID = -1003784095272                  # OTP group chat ID

SUPPORT_LINK = "https://t.me/bdgiveaways24"         # Support link
DEVELOPER_LINK = "http://t.me/rafimhossen"    # Developer link
CHANNEL_LINK = "https://t.me/bdgiveaways24"           # Channel link
OTP_GROUP_LINK = "https://t.me/hjdghjlk"     # OTP receive group link
RANGE_GROUP_LINK = "https://t.me/bdgiveaways24"      # Range group link
PANEL_BOT_LINK = "http://t.me/OTP19BOT_BOT"     # Bot link used on the "PANEL" button
# ===========================================================================================
# All data is now saved in a single SQLite database file — only the activity log stays in a separate JSON file
DATABASE_FILE = "miahsms_database.db"      # Real SQLite database file
USER_DATA_FILE = "users"
PAID_SMS_FILE = "paid_sms"
STATS_FILE = "user_stats"
REFERRAL_DATA_FILE = "referral_data"
BANNED_USERS_FILE = "banned_users"
WITHDRAW_DATA_FILE = "withdraw_requests"
DATA_RANGE_FILE = "datarange"
ACTIVITY_LOGS_FILE = "activity_logs.json"
SITE_SETTINGS_FILE = "site_settings"   # admin-editable settings (e.g. otp_rate), stored in the same DB

# ==================== WELCOME MESSAGE CONFIGURATION ====================
WELCOME_MESSAGE = """✨👑 *WELCOME TO SMSBOT* 👑✨
━━━━━━━━━━━━━━━━━━━━━━
🚀 Instant Virtual Numbers
🔐 100% Secure & Reliable Service
💎 Premium Quality Guaranteed
🌍 Worldwide Coverage
━━━━━━━━━━━━━━━━━━━━━━
🎉 *Welcome!* Get started from the menu below 👇"""

MENU_PROMPT_MESSAGE = """━━━━━━━━━━━━━━━━━━━━━━
🔹 *Select the option you need from the buttons below* 🔹
━━━━━━━━━━━━━━━━━━━━━━"""

WELCOME_MESSAGE_BN = """✨👑 *এসএমএস-BOTএ স্বাগতম* 👑✨
━━━━━━━━━━━━━━━━━━━━━━
🚀 তাৎক্ষণিক ভার্চুয়াল নাম্বার
🔐 ১০০% নিরাপদ ও নির্ভরযোগ্য সার্ভিস
💎 প্রিমিয়াম কোয়ালিটির নিশ্চয়তা
🌍 বিশ্বব্যাপী কভারেজ
━━━━━━━━━━━━━━━━━━━━━━
🎉 *স্বাগতম!* নিচের মেনু থেকে শুরু করুন 👇"""

MENU_PROMPT_MESSAGE_BN = """━━━━━━━━━━━━━━━━━━━━━━
🔹 *নিচের বাটন থেকে আপনার প্রয়োজনীয় অপশন সিলেক্ট করুন* 🔹
━━━━━━━━━━━━━━━━━━━━━━"""

# ==================== MULTI-LANGUAGE CONFIGURATION ====================
# Default language for every user is English ("en"). A user can switch to
# Bangla ("bn") only from inside the PROFILE screen — no other menu shows
# the language switch. The choice is stored per-user (users[uid]["lang"])
# and persists across sessions.
DEFAULT_LANG = "en"

TEXTS = {
    "en": {
        "welcome": WELCOME_MESSAGE,
        "menu_prompt": MENU_PROMPT_MESSAGE,
        "btn_get_number": "📞 GET NUMBER",
        "btn_search_otp": "🔍 SEARCH OTP",
        "btn_2fa": "⚡ GET 2FA",
        "btn_balance": "💰 BALANCE",
        "btn_refer": "REFER AND EARN",
        "btn_profile": "👤 PROFILE",
        "btn_leaderboard": "🏆 LEADERBOARD",
        "btn_support": "💬 SUPPORT",
        "btn_traffic": "🚦 TRAFFIC",
        "btn_admin_panel": "⚙️ ADMIN PANEL ⚙️",
        "banned": "🚫 YOU ARE BANNED 🚫",
        "support_text": "💬 SUPPORT 🎧\n\nCLICK THE BUTTON BELOW TO CONTACT SUPPORT 📩",
        "btn_support_inline": "💬 SUPPORT",
        "btn_developer": "👨‍💻 DEVELOPER BY",
        "btn_active_range": "📡 ACTIVE RANGE",
        "search_otp_prompt": "🔍 **ENTER THE NUMBER TO SEARCH OTP:**",
        "balance_title": "💰 <b>YOUR CURRENT BALANCE</b>",
        "balance_total": "TOTAL",
        "btn_withdraw": "💸 WITHDRAW",
        "profile_title": "👤 <b>YOUR PROFILE</b>",
        "profile_name": "NAME",
        "profile_username": "USERNAME",
        "profile_id": "TELEGRAM ID",
        "profile_balance": "BALANCE",
        "profile_today": "TODAY",
        "profile_7d": "LAST 7 DAYS",
        "profile_all": "ALL TIME",
        "profile_numbers": "NUMBERS",
        "profile_otps": "OTPS",
        "no_username": "No username",
        "btn_language": "🌐 LANGUAGE",
        "lang_select_prompt": "🌐 <b>SELECT LANGUAGE</b>\n\nChoose your preferred language below:",
        "btn_lang_en": "🇬🇧 English",
        "btn_lang_bn": "🇧🇩 বাংলা",
        "lang_changed": "✅ Language changed to <b>English</b>.",
    },
    "bn": {
        "welcome": WELCOME_MESSAGE_BN,
        "menu_prompt": MENU_PROMPT_MESSAGE_BN,
        "btn_get_number": "📞 নাম্বার নিন",
        "btn_search_otp": "🔍 ওটিপি সার্চ করুন",
        "btn_2fa": "⚡ 2FA কোড নিন",
        "btn_balance": "💰 ব্যালেন্স",
        "btn_refer": "রেফার করে আয় করুন",
        "btn_profile": "👤 প্রোফাইল",
        "btn_leaderboard": "🏆 লিডারবোর্ড",
        "btn_support": "💬 সাপোর্ট",
        "btn_traffic": "🚦 ট্রাফিক",
        "btn_admin_panel": "⚙️ অ্যাডমিন প্যানেল ⚙️",
        "banned": "🚫 আপনাকে ব্যান করা হয়েছে 🚫",
        "support_text": "💬 সাপোর্ট 🎧\n\nসাপোর্টের সাথে যোগাযোগ করতে নিচের বাটনে ক্লিক করুন 📩",
        "btn_support_inline": "💬 সাপোর্ট",
        "btn_developer": "👨‍💻 ডেভেলপার",
        "btn_active_range": "📡 লাইভ রেঞ্জ",
        "search_otp_prompt": "🔍 **যে নাম্বারের ওটিপি সার্চ করবেন সেটি লিখুন:**",
        "balance_title": "💰 <b>আপনার বর্তমান ব্যালেন্স</b>",
        "balance_total": "মোট",
        "btn_withdraw": "💸 উইথড্র",
        "profile_title": "👤 <b>আপনার প্রোফাইল</b>",
        "profile_name": "নাম",
        "profile_username": "ইউজারনেম",
        "profile_id": "টেলিগ্রাম আইডি",
        "profile_balance": "ব্যালেন্স",
        "profile_today": "আজকের",
        "profile_7d": "গত ৭ দিন",
        "profile_all": "সর্বমোট",
        "profile_numbers": "নাম্বার",
        "profile_otps": "ওটিপি",
        "no_username": "ইউজারনেম নেই",
        "btn_language": "🌐 ভাষা",
        "lang_select_prompt": "🌐 <b>ভাষা নির্বাচন করুন</b>\n\nআপনার পছন্দের ভাষা বেছে নিন:",
        "btn_lang_en": "🇬🇧 English",
        "btn_lang_bn": "🇧🇩 বাংলা",
        "lang_changed": "✅ ভাষা <b>বাংলা</b> করা হয়েছে।",
    },
}

def get_user_lang(uid):
    """Returns 'en' or 'bn' for this user. Defaults to English if never set."""
    user_data = get_user(uid)
    lang = user_data.get("lang", DEFAULT_LANG)
    return lang if lang in TEXTS else DEFAULT_LANG

async def set_user_lang(uid, lang):
    """Persists the user's chosen language ('en' or 'bn')."""
    if lang not in TEXTS:
        lang = DEFAULT_LANG
    uid = str(uid)
    async with balance_lock:
        data = load_data()
        if uid not in data:
            data[uid] = {"user_id": uid, "balance": 0.0, "total_numbers": 0, "referral_count": 0}
        data[uid]["lang"] = lang
        save_data(data)

def tr(uid, key):
    """Translated text lookup for this user's current language, with an
    English fallback if a key is ever missing from a language pack."""
    lang = get_user_lang(uid)
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, ""))

def is_menu_btn(text, key):
    """True if `text` matches the given button key in EITHER language —
    used so main-menu button taps are recognized no matter which language
    keyboard the user is currently looking at."""
    return text in (TEXTS["en"].get(key), TEXTS["bn"].get(key))

# ==================== OTP RATE CONFIGURATION ====================
DEFAULT_OTP_RATE = 0.50   # fallback used only if site_settings has never been saved

def get_otp_rate():
    """Admin-configurable OTP payout rate (BDT per OTP). Persisted in the
    same SQLite database (SITE_SETTINGS_FILE section); falls back to
    DEFAULT_OTP_RATE (0.50) until an admin changes it from SYSTEM CONFIGURATION."""
    settings = load_data(SITE_SETTINGS_FILE)
    try:
        rate = float(settings.get("otp_rate", DEFAULT_OTP_RATE))
        return rate if rate > 0 else DEFAULT_OTP_RATE
    except (TypeError, ValueError):
        return DEFAULT_OTP_RATE

def set_otp_rate(rate):
    settings = load_data(SITE_SETTINGS_FILE)
    settings["otp_rate"] = float(rate)
    save_data(settings, SITE_SETTINGS_FILE)

# ==================== REFER CONTROL (admin: SYSTEM CONFIGURATION -> REFER CONTROL) ====================
DEFAULT_REFERRAL_BONUS = 0.50   # BDT added to the referrer for every new person who joins
DEFAULT_REF_COMMISSION = 0.01   # BDT per successful OTP of a referred user (switch is OFF by default)

def _ref_setting(key, default):
    try:
        v = float(load_data(SITE_SETTINGS_FILE).get(key, default))
        return v if v >= 0 else default
    except (TypeError, ValueError):
        return default

def set_ref_setting(key, value):
    settings = load_data(SITE_SETTINGS_FILE)
    settings[key] = float(value)
    save_data(settings, SITE_SETTINGS_FILE)

def get_referral_bonus():
    return _ref_setting("referral_bonus", DEFAULT_REFERRAL_BONUS)

def get_ref_commission():
    return _ref_setting("ref_commission", DEFAULT_REF_COMMISSION)

def is_ref_commission_on():
    return get_switch("ref_commission", False)

def calc_ref_commission():
    """Commission per successful OTP of a referred user (fixed amount set by the admin)."""
    return round(get_ref_commission(), 4)

# ==================== SERVICE ENABLE / DISABLE (GET NUMBER SERVICES) ====================
# All liveaccess services (Facebook, Instagram, etc.) are enabled by default.
# Admin can disable individual services from SYSTEM CONFIGURATION → MANAGE SERVICES;
# disabled services are simply hidden from the user's GET NUMBER service list.

def get_disabled_services():
    _get_db_connection()
    return [n[4:] for n, s in _SWITCH_CACHE.items() if n.startswith("svc_") and s == "OFF"]

def is_service_enabled(sid):
    return get_switch("svc_" + str(sid), True)

def set_service_enabled(sid, enabled):
    set_switch("svc_" + str(sid), enabled)

# ==================== MAIN MENU BUTTON ENABLE / DISABLE ====================
# SEARCH OTP, GET 2FA, LEADERBOARD, PROFILE and SUPPORT can each be hidden from the
# main menu by the admin. GET 2FA and LEADERBOARD are OFF by default; the rest are ON.
DEFAULT_BUTTON_FLAGS = {
    "btn_search_otp": True,
    "btn_2fa": False,
    "btn_leaderboard": False,
    "btn_profile": True,
    "btn_support": True,
    "btn_traffic": True,
}

BUTTON_FLAG_LABELS = {
    "btn_search_otp": "🔍 SEARCH OTP",
    "btn_2fa": "⚡ GET 2FA",
    "btn_leaderboard": "🏆 LEADERBOARD",
    "btn_profile": "👤 PROFILE",
    "btn_support": "💬 SUPPORT",
    "btn_traffic": "🚦 TRAFFIC",
}

def get_button_flags():
    return {k: get_switch(k, d) for k, d in DEFAULT_BUTTON_FLAGS.items()}

def is_button_enabled(key):
    return get_switch(key, DEFAULT_BUTTON_FLAGS.get(key, True))

def set_button_enabled(key, enabled):
    set_switch(key, enabled)

# ==================== NUMBER MANAGE (OLD NUMBER DELETE) ====================
# Admin → SYSTEM CONFIGURATION → NUMBER MANAGE.
# OFF (default): pressing NEW NUMBER keeps the old number message above the new one.
# ON : pressing NEW NUMBER automatically deletes the old number message.

def is_old_number_delete_on():
    return get_switch("old_number_delete", False)

def set_old_number_delete(enabled):
    set_switch("old_number_delete", enabled)

# ==================== NUMBER TEMPLATE VERSION 2 ====================
# OFF: the normal "YOUR NUMBER" message (country / range / number / status).
# ON (default): very plain message - only country flag + number, with a one-tap copy button.

def is_number_template_v2_on():
    return get_switch("number_template_v2", True)

def set_number_template_v2(enabled):
    set_switch("number_template_v2", enabled)

def build_number_text_v2(flag, num=None, otp=None, sms=None):
    """V2 number message: just the flag + NEW NUMBER (the number itself is a copy button)."""
    text = f"{flag} <b>NEW NUMBER</b>"
    if otp:
        text += f"\n🔑 <code>{html.escape(str(otp))}</code>"
    return text

def build_otp_text_v2(flag, num, otp):
    """V2 OTP message: short and neat."""
    return (
        f"✅ <b>OTP RECEIVED</b> ✅\n\n"
        f"<blockquote>{flag} <code>+{num}</code></blockquote>\n"
        f"<blockquote>🔑 <code>{html.escape(str(otp))}</code></blockquote>"
    )

def build_otp_keyboard_v2(otp):
    """One-tap copy button for the OTP (V2 only)."""
    otp = str(otp or "").strip()
    if CopyTextButton is None or not otp or otp == "N/A":
        return None
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"🔑 {otp}", copy_text=CopyTextButton(text=otp), style="success")
    ]])

def build_number_keyboard(num=None, v2=False, flag="", sid=""):
    new_btn = InlineKeyboardButton("🔄 NEW NUMBER", callback_data="same_range", style="success")
    grp_btn = InlineKeyboardButton("📢 CHECK OTP GROUP", url=OTP_GROUP_LINK, style="primary")
    if not v2:
        return InlineKeyboardMarkup([[new_btn], [grp_btn]])

    rows = []
    # 1) platform / service
    if sid:
        rows.append([InlineKeyboardButton(f"📱 {sid}", callback_data="noop_svc", style="primary")])
    # 2) flag + number — tap = copy
    if num:
        label = f"{flag} +{num}".strip()
        if CopyTextButton is not None:
            rows.append([InlineKeyboardButton(label, copy_text=CopyTextButton(text=f"+{num}"), style="success")])
        else:
            rows.append([InlineKeyboardButton(label, callback_data=f"copy_text_+{num}", style="success")])
    # 3) change country (full width), then NEW NUMBER + OTP GROUP side by side
    rows.append([InlineKeyboardButton("🌍 CHANGE COUNTRY", callback_data="change_country", style="danger")])
    rows.append([new_btn, grp_btn])
    return InlineKeyboardMarkup(rows)

# ==================== REFERRAL / WITHDRAW CONFIGURATION ====================
# (referral reward is now set from Admin -> SYSTEM CONFIGURATION -> REFER CONTROL)
DEFAULT_MIN_WITHDRAW = 60   # fallback used only if site_settings has never been saved
BDT_TO_USD_RATE = 125       # used only to show the admin a USD estimate for BINANCE withdraws
MAX_WITHDRAW = 10000

# ==================== PAYMENT METHOD ENABLE / DISABLE ====================
# BKASH, NAGAD, ROCKET and BINANCE are all ON by default. Admin can turn any
# of them off from ADMIN PANEL → PAYMENT SETUP; disabled methods are
# simply hidden from the user's withdraw method list.
DEFAULT_PAYMENT_FLAGS = {
    "pm_bkash": True,
    "pm_nagad": True,
    "pm_rocket": True,
    "pm_binance": True,
}

PAYMENT_METHOD_LABELS = {
    "pm_bkash": "📱 BKASH",
    "pm_nagad": "💵 NAGAD",
    "pm_rocket": "🚀 ROCKET",
    "pm_binance": "🏦 BINANCE",
}

PAYMENT_METHOD_NAMES = {
    "pm_bkash": "BKASH",
    "pm_nagad": "NAGAD",
    "pm_rocket": "ROCKET",
    "pm_binance": "BINANCE",
}

def get_payment_flags():
    return {k: get_switch(k, d) for k, d in DEFAULT_PAYMENT_FLAGS.items()}

def is_payment_method_enabled(key):
    return get_switch(key, DEFAULT_PAYMENT_FLAGS.get(key, True))

def set_payment_method_enabled(key, enabled):
    set_switch(key, enabled)

# ==================== PER-METHOD MINIMUM WITHDRAW ====================
# Each payment method (BKASH/NAGAD/ROCKET/BINANCE) has its own minimum
# withdraw amount, set from ADMIN PANEL → PAYMENT SETUP → MINIMUM WITHDRAW LIMITS.

def get_min_withdraw_map():
    settings = load_data(SITE_SETTINGS_FILE)
    raw = settings.get("min_withdraw")
    raw = raw if isinstance(raw, dict) else {}
    result = {}
    for key in PAYMENT_METHOD_LABELS:
        try:
            amount = float(raw.get(key, DEFAULT_MIN_WITHDRAW))
            result[key] = amount if amount > 0 else DEFAULT_MIN_WITHDRAW
        except (TypeError, ValueError):
            result[key] = DEFAULT_MIN_WITHDRAW
    return result

def get_min_withdraw(key=None):
    """With a specific pm_xxx key, returns that method's own minimum withdraw.
    With no key (used before the user has picked a method), returns the lowest
    minimum among currently-enabled methods, so the initial balance gate is as
    permissive as possible."""
    amounts = get_min_withdraw_map()
    if key is None:
        enabled = [amounts[k] for k in amounts if is_payment_method_enabled(k)]
        return min(enabled) if enabled else DEFAULT_MIN_WITHDRAW
    return amounts.get(key, DEFAULT_MIN_WITHDRAW)

def set_min_withdraw(key, amount):
    settings = load_data(SITE_SETTINGS_FILE)
    raw = settings.get("min_withdraw")
    raw = dict(raw) if isinstance(raw, dict) else {}
    raw[key] = float(amount)
    settings["min_withdraw"] = raw
    save_data(settings, SITE_SETTINGS_FILE)

request_queue = asyncio.Queue()
MAX_WORKERS = 5000

client_async = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=5.0),
    headers={"X-API-Key": API_KEY},
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=5)
)

active_numbers = {}
last_range = {}
last_service = {}   # uid -> {"range": ..., "sid": ...}  (platform shown on the V2 number message)
CHECK_INTERVAL = 3.0       # poll speed while someone is waiting for an OTP
IDLE_CHECK_INTERVAL = 8.0  # sleep time when no number is waiting (no API call made)

# ==================== LIVEACCESS CACHE ====================
_liveaccess_cache = {"services": []}
LIVEACCESS_REFRESH_INTERVAL = 60

async def _do_liveaccess_fetch():
    global _liveaccess_cache
    try:
        r = await client_async.get(f"{BASE_URL}/api/liveaccess")
        data = r.json()
        if data.get("status") == "ok":
            svcs = data.get("services", [])
            if svcs:
                _liveaccess_cache["services"] = svcs
                print(f"[liveaccess] cache updated — {len(svcs)} service(s)")
    except Exception as e:
        print(f"[liveaccess] fetch error: {e}")

async def liveaccess_refresh_loop():
    while True:
        await _do_liveaccess_fetch()
        await asyncio.sleep(LIVEACCESS_REFRESH_INTERVAL)

def get_cached_services():
    return _liveaccess_cache["services"]

# ==================== CHECK IF USER IS ADMIN ====================

def is_admin(user_id):
    return user_id in ADMINS

# ==================== UNIFIED DATABASE (real SQLite database file) ====================
# users, paid_sms, user_stats, referral_data, banned_users, withdraw_requests, datarange —
# All these sections live in a single SQLite database file (DATABASE_FILE). activity_logs stays in a separate json file.

_DB_SECTION_DEFAULTS = {
    BANNED_USERS_FILE: [],
}

_DB_CONN = None
_DB_CACHE = {}   # section -> JSON text (write-through cache, avoids disk reads)
_SWITCH_CACHE = {}   # switch name -> "ON" / "OFF" (mirror of the `switches` table)

def get_switch(name, default=False):
    """Every admin ON/OFF switch lives as ONE row (name -> 'ON'/'OFF') in the
    `switches` table of the main database. Rows are updated in place, so
    nothing piles up over time."""
    _get_db_connection()
    state = _SWITCH_CACHE.get(name)
    if state is None:
        return bool(default)
    return state == "ON"

def set_switch(name, on):
    conn = _get_db_connection()
    state = "ON" if on else "OFF"
    if _SWITCH_CACHE.get(name) == state:
        return
    conn.execute(
        "INSERT INTO switches (name, state) VALUES (?, ?) "
        "ON CONFLICT(name) DO UPDATE SET state = excluded.state",
        (name, state)
    )
    conn.commit()
    _SWITCH_CACHE[name] = state

def _migrate_switches(conn):
    """One-time, safe to repeat: pull old switch values out of site_settings
    into the switches table, then remove the old copies."""
    for name, state in conn.execute("SELECT name, state FROM switches"):
        _SWITCH_CACHE[name] = state

    def put(name, on):
        if name not in _SWITCH_CACHE:
            set_switch(name, on)

    settings = load_data(SITE_SETTINGS_FILE)
    changed = False
    for key in ("button_flags", "payment_flags"):
        old = settings.pop(key, None)
        changed = True if old is not None else changed
        if isinstance(old, dict):
            for k, v in old.items():
                put(k, bool(v))
    old = settings.pop("disabled_services", None)
    changed = True if old is not None else changed
    if isinstance(old, list):
        for sid in old:
            put("svc_" + str(sid), False)
    for key in ("old_number_delete", "number_template_v2"):
        if key in settings:
            put(key, bool(settings.pop(key)))
            changed = True
    if changed:
        save_data(settings, SITE_SETTINGS_FILE)

    for k, d in DEFAULT_BUTTON_FLAGS.items():
        put(k, d)
    for k, d in DEFAULT_PAYMENT_FLAGS.items():
        put(k, d)
    put("old_number_delete", False)
    put("number_template_v2", True)

def _get_db_connection():
    global _DB_CONN
    if _DB_CONN is None:
        conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        try:
            # DELETE mode = no permanent -wal / -shm files. If an older run left the
            # database in WAL mode, this switches it back and merges + removes them.
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("PRAGMA synchronous=FULL")
        except Exception:
            pass
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sections ("
            "  section TEXT PRIMARY KEY,"
            "  data TEXT NOT NULL"
            ")"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS switches ("
            "  name TEXT PRIMARY KEY,"
            "  state TEXT NOT NULL CHECK (state IN ('ON','OFF'))"
            ")"
        )
        conn.commit()
        _DB_CONN = conn
        _migrate_switches(conn)
        try:
            if os.path.exists(ACTIVITY_LOGS_FILE):
                os.remove(ACTIVITY_LOGS_FILE)
        except OSError:
            pass
    return _DB_CONN

def load_data(section=USER_DATA_FILE):
    # activity log is no longer stored anywhere
    if section == ACTIVITY_LOGS_FILE:
        return []

    default = _DB_SECTION_DEFAULTS.get(section, {})
    text = _DB_CACHE.get(section)
    if text is None:
        conn = _get_db_connection()
        row = conn.execute("SELECT data FROM sections WHERE section = ?", (section,)).fetchone()
        if row is None:
            return default
        text = row[0]
        _DB_CACHE[section] = text
    try:
        value = json.loads(text)
    except:
        return default
    return value if isinstance(value, type(default)) else default

def save_data(data, section=USER_DATA_FILE):
    text = json.dumps(data)
    if _DB_CACHE.get(section) == text:
        return  # nothing changed — skip the disk write
    conn = _get_db_connection()
    conn.execute(
        "INSERT INTO sections (section, data) VALUES (?, ?) "
        "ON CONFLICT(section) DO UPDATE SET data = excluded.data",
        (section, text)
    )
    conn.commit()
    _DB_CACHE[section] = text

# ==================== WITHDRAW DATA FUNCTIONS ====================

def load_withdraw_requests():
    return load_data(WITHDRAW_DATA_FILE)

def save_withdraw_requests(data):
    save_data(data, WITHDRAW_DATA_FILE)

def generate_payment_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

# ==================== BANNED USERS FUNCTIONS ====================

def load_banned_users():
    return load_data(BANNED_USERS_FILE)

def save_banned_users(banned_list):
    save_data(banned_list, BANNED_USERS_FILE)

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
    return load_data(REFERRAL_DATA_FILE)

def save_referral_data(data):
    save_data(data, REFERRAL_DATA_FILE)

def update_referral_count(uid, count):
    referral_data = load_referral_data()
    uid_str = str(uid)
    if uid_str not in referral_data:
        referral_data[uid_str] = {"referral_count": 0}
    referral_data[uid_str]["referral_count"] = count
    save_referral_data(referral_data)

def add_referral_earning(uid, amount):
    rd = load_referral_data()
    e = rd.setdefault(str(uid), {"referral_count": 0})
    e["earned"] = round(float(e.get("earned", 0.0)) + float(amount), 4)
    save_referral_data(rd)

def get_referral_count(uid):
    referral_data = load_referral_data()
    uid_str = str(uid)
    return referral_data.get(uid_str, {}).get("referral_count", 0)

# ==================== DATA RANGE FILE ====================

def load_range_db():
    return load_data(DATA_RANGE_FILE)

def save_range_db(data):
    save_data(data, DATA_RANGE_FILE)

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
        "2376": ("🇨🇲", "Cameroon"),
        "2250": ("🇨🇮", "Ivory Coast"),
        "2613": ("🇲🇬", "Madagascar"),
        "4077": ("🇷🇴", "Romania"),
        "237": ("🇨🇲", "Cameroon"),
        "225": ("🇨🇮", "Ivory Coast"),
        "261": ("🇲🇬", "Madagascar"),
        "20": ("🇪🇬", "Egypt"),
        "27": ("🇿🇦", "South Africa"),
        "234": ("🇳🇬", "Nigeria"),
        "254": ("🇰🇪", "Kenya"),
        "233": ("🇬🇭", "Ghana"),
        "212": ("🇲🇦", "Morocco"),
        "213": ("🇩🇿", "Algeria"),
        "216": ("🇹🇳", "Tunisia"),
        "218": ("🇱🇾", "Libya"),
        "249": ("🇸🇩", "Sudan"),
        "251": ("🇪🇹", "Ethiopia"),
        "252": ("🇸🇴", "Somalia"),
        "253": ("🇩🇯", "Djibouti"),
        "255": ("🇹🇿", "Tanzania"),
        "256": ("🇺🇬", "Uganda"),
        "257": ("🇧🇮", "Burundi"),
        "258": ("🇲🇿", "Mozambique"),
        "260": ("🇿🇲", "Zambia"),
        "263": ("🇿🇼", "Zimbabwe"),
        "264": ("🇳🇦", "Namibia"),
        "265": ("🇲🇼", "Malawi"),
        "266": ("🇱🇸", "Lesotho"),
        "267": ("🇧🇼", "Botswana"),
        "268": ("🇸🇿", "Swaziland"),
        "269": ("🇰🇲", "Comoros"),
        "220": ("🇬🇲", "Gambia"),
        "221": ("🇸🇳", "Senegal"),
        "222": ("🇲🇷", "Mauritania"),
        "223": ("🇲🇱", "Mali"),
        "224": ("🇬🇳", "Guinea"),
        "226": ("🇧🇫", "Burkina Faso"),
        "227": ("🇳🇪", "Niger"),
        "228": ("🇹🇬", "Togo"),
        "229": ("🇧🇯", "Benin"),
        "230": ("🇲🇺", "Mauritius"),
        "231": ("🇱🇷", "Liberia"),
        "232": ("🇸🇱", "Sierra Leone"),
        "235": ("🇹🇩", "Chad"),
        "236": ("🇨🇫", "Central African Republic"),
        "238": ("🇨🇻", "Cape Verde"),
        "239": ("🇸🇹", "Sao Tome and Principe"),
        "240": ("🇬🇶", "Equatorial Guinea"),
        "241": ("🇬🇦", "Gabon"),
        "242": ("🇨🇬", "Congo"),
        "243": ("🇨🇩", "DR Congo"),
        "244": ("🇦🇴", "Angola"),
        "245": ("🇬🇼", "Guinea-Bissau"),
        "247": ("🇸🇭", "Saint Helena"),
        "248": ("🇸🇨", "Seychelles"),
        "250": ("🇷🇼", "Rwanda"),
        "290": ("🇸🇭", "Saint Helena"),
        "291": ("🇪🇷", "Eritrea"),
        "40": ("🇷🇴", "Romania"),
        "44": ("🇬🇧", "United Kingdom"),
        "33": ("🇫🇷", "France"),
        "49": ("🇩🇪", "Germany"),
        "39": ("🇮🇹", "Italy"),
        "34": ("🇪🇸", "Spain"),
        "31": ("🇳🇱", "Netherlands"),
        "32": ("🇧🇪", "Belgium"),
        "41": ("🇨🇭", "Switzerland"),
        "43": ("🇦🇹", "Austria"),
        "46": ("🇸🇪", "Sweden"),
        "47": ("🇳🇴", "Norway"),
        "45": ("🇩🇰", "Denmark"),
        "358": ("🇫🇮", "Finland"),
        "351": ("🇵🇹", "Portugal"),
        "353": ("🇮🇪", "Ireland"),
        "36": ("🇭🇺", "Hungary"),
        "48": ("🇵🇱", "Poland"),
        "380": ("🇺🇦", "Ukraine"),
        "370": ("🇱🇹", "Lithuania"),
        "371": ("🇱🇻", "Latvia"),
        "372": ("🇪🇪", "Estonia"),
        "373": ("🇲🇩", "Moldova"),
        "374": ("🇦🇲", "Armenia"),
        "375": ("🇧🇾", "Belarus"),
        "376": ("🇦🇩", "Andorra"),
        "377": ("🇲🇨", "Monaco"),
        "381": ("🇷🇸", "Serbia"),
        "382": ("🇲🇪", "Montenegro"),
        "385": ("🇭🇷", "Croatia"),
        "386": ("🇸🇮", "Slovenia"),
        "387": ("🇧🇦", "Bosnia and Herzegovina"),
        "389": ("🇲🇰", "North Macedonia"),
        "350": ("🇬🇮", "Gibraltar"),
        "352": ("🇱🇺", "Luxembourg"),
        "354": ("🇮🇸", "Iceland"),
        "355": ("🇦🇱", "Albania"),
        "356": ("🇲🇹", "Malta"),
        "357": ("🇨🇾", "Cyprus"),
        "359": ("🇧🇬", "Bulgaria"),
        "421": ("🇸🇰", "Slovakia"),
        "420": ("🇨🇿", "Czech Republic"),
        "298": ("🇫🇴", "Faroe Islands"),
        "299": ("🇬🇱", "Greenland"),
        "1": ("🇺🇸", "United States"),
        "7": ("🇷🇺", "Russia"),
        "91": ("🇮🇳", "India"),
        "92": ("🇵🇰", "Pakistan"),
        "880": ("🇧🇩", "Bangladesh"),
        "86": ("🇨🇳", "China"),
        "81": ("🇯🇵", "Japan"),
        "82": ("🇰🇷", "South Korea"),
        "84": ("🇻🇳", "Vietnam"),
        "66": ("🇹🇭", "Thailand"),
        "62": ("🇮🇩", "Indonesia"),
        "60": ("🇲🇾", "Malaysia"),
        "65": ("🇸🇬", "Singapore"),
        "63": ("🇵🇭", "Philippines"),
        "95": ("🇲🇲", "Myanmar"),
        "94": ("🇱🇰", "Sri Lanka"),
        "977": ("🇳🇵", "Nepal"),
        "93": ("🇦🇫", "Afghanistan"),
        "98": ("🇮🇷", "Iran"),
        "90": ("🇹🇷", "Turkey"),
        "964": ("🇮🇶", "Iraq"),
        "963": ("🇸🇾", "Syria"),
        "961": ("🇱🇧", "Lebanon"),
        "962": ("🇯🇴", "Jordan"),
        "965": ("🇰🇼", "Kuwait"),
        "966": ("🇸🇦", "Saudi Arabia"),
        "967": ("🇾🇪", "Yemen"),
        "968": ("🇴🇲", "Oman"),
        "971": ("🇦🇪", "United Arab Emirates"),
        "972": ("🇮🇱", "Israel"),
        "973": ("🇧🇭", "Bahrain"),
        "974": ("🇶🇦", "Qatar"),
        "994": ("🇦🇿", "Azerbaijan"),
        "995": ("🇬🇪", "Georgia"),
        "996": ("🇰🇬", "Kyrgyzstan"),
        "992": ("🇹🇯", "Tajikistan"),
        "993": ("🇹🇲", "Turkmenistan"),
        "998": ("🇺🇿", "Uzbekistan"),
        "855": ("🇰🇭", "Cambodia"),
        "856": ("🇱🇦", "Laos"),
        "976": ("🇲🇳", "Mongolia"),
        "850": ("🇰🇵", "North Korea"),
        "55": ("🇧🇷", "Brazil"),
        "52": ("🇲🇽", "Mexico"),
        "54": ("🇦🇷", "Argentina"),
        "57": ("🇨🇴", "Colombia"),
        "51": ("🇵🇪", "Peru"),
        "58": ("🇻🇪", "Venezuela"),
        "56": ("🇨🇱", "Chile"),
        "593": ("🇪🇨", "Ecuador"),
        "591": ("🇧🇴", "Bolivia"),
        "595": ("🇵🇾", "Paraguay"),
        "598": ("🇺🇾", "Uruguay"),
        "502": ("🇬🇹", "Guatemala"),
        "503": ("🇸🇻", "El Salvador"),
        "504": ("🇭🇳", "Honduras"),
        "506": ("🇨🇷", "Costa Rica"),
        "507": ("🇵🇦", "Panama"),
        "509": ("🇭🇹", "Haiti"),
        "501": ("🇧🇿", "Belize"),
        "61": ("🇦🇺", "Australia"),
        "64": ("🇳🇿", "New Zealand"),
        "675": ("🇵🇬", "Papua New Guinea"),
        "679": ("🇫🇯", "Fiji"),
        "1246": ("🇧🇧", "Barbados"),
        "1876": ("🇯🇲", "Jamaica"),
        "53": ("🇨🇺", "Cuba"),
        "592": ("🇬🇾", "Guyana"),
    }

    clean_num = str(number).replace('+', '').replace(' ', '').replace('-', '').strip()
    sorted_prefixes = sorted(country_map.keys(), key=len, reverse=True)

    for prefix in sorted_prefixes:
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
        "tiktok": "TIKTOK",
        "twitter": "TWITTER", "x.com": "TWITTER",
        "snapchat": "SNAPCHAT", "snap": "SNAPCHAT",
        "whatsapp": "WHATSAPP",
        "telegram": "TELEGRAM",
        "discord": "DISCORD",
        "messenger": "MESSENGER",
        "linkedin": "LINKEDIN",
        "google": "GOOGLE", "gmail": "GOOGLE",
        "amazon": "AMAZON",
        "microsoft": "MICROSOFT", "outlook": "MICROSOFT",
        "yahoo": "YAHOO",
        "paypal": "PAYPAL",
        "binance": "BINANCE",
        "coinbase": "COINBASE",
        "spotify": "SPOTIFY",
        "netflix": "NETFLIX",
        "uber": "UBER",
        "apple": "APPLE", "icloud": "APPLE",
        "bkash": "BKASH",
        "nagad": "NAGAD",
        "stripe": "STRIPE",
        "line": "LINE",
        "wechat": "WECHAT",
        "viber": "VIBER",
        "signal": "SIGNAL",
        "pubg": "PUBG",
        "free fire": "FREE FIRE",
    }

    for keyword, service_name in sorted(service_keywords.items(), key=lambda x: len(x[0]), reverse=True):
        if keyword in sms_lower:
            return service_name

    return "SMS SERVICE"

# ==================== KEYBOARDS SECTION ====================
# GET 2FA and SEARCH OTP button positions were swapped

from telegram import KeyboardButton, ReplyKeyboardMarkup

def main_keyboard(user_id):
    keyboard = [
        [
            KeyboardButton(
                text=tr(user_id, "btn_get_number"),
                style="success"
            )
        ]
    ]

    # All the optional/toggleable buttons are collected into one flat list
    # (in display order) and then packed two-per-row. This way, if one
    # button in what used to be a "pair" is disabled from MANAGE BUTTONS,
    # the other one doesn't end up alone in a full-width row — it just
    # shifts up and pairs with the next enabled button in the list.
    optional_buttons = []

    if is_button_enabled("btn_search_otp"):
        optional_buttons.append(KeyboardButton(text=tr(user_id, "btn_search_otp"), style="primary"))
    if is_button_enabled("btn_2fa"):
        optional_buttons.append(KeyboardButton(text=tr(user_id, "btn_2fa"), style="danger"))

    optional_buttons.append(KeyboardButton(text=tr(user_id, "btn_balance"), style="success"))
    optional_buttons.append(KeyboardButton(text=tr(user_id, "btn_refer"), style="primary"))

    if is_button_enabled("btn_profile"):
        optional_buttons.append(KeyboardButton(text=tr(user_id, "btn_profile"), style="primary"))
    if is_button_enabled("btn_leaderboard"):
        optional_buttons.append(KeyboardButton(text=tr(user_id, "btn_leaderboard"), style="danger"))
    if is_button_enabled("btn_support"):
        optional_buttons.append(KeyboardButton(text=tr(user_id, "btn_support"), style="primary"))
    if is_button_enabled("btn_traffic"):
        optional_buttons.append(KeyboardButton(text=tr(user_id, "btn_traffic"), style="success"))

    for i in range(0, len(optional_buttons), 2):
        keyboard.append(optional_buttons[i:i + 2])

    if is_admin(user_id):
        keyboard.append([
            KeyboardButton(
                text=tr(user_id, "btn_admin_panel"),
                style="danger"
            )
        ])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

def cancel_keyboard():
    keyboard = [[KeyboardButton("❌ CANCEL", style="danger")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_main_keyboard():
    keyboard = [
        [KeyboardButton("👥 USER MANAGEMENT", style="success"), KeyboardButton("💳 PAYMENT SETUP", style="success")],
        [KeyboardButton("⚙️ SYSTEM CONFIGURATION", style="success")],
        [KeyboardButton("🔙 BACK TO MAIN", style="danger")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def user_management_keyboard():
    keyboard = [
        [KeyboardButton("📢 BROADCAST", style="success"), KeyboardButton("🆔 ALL USER ID", style="primary")],
        [KeyboardButton("📜 BAN USER LIST", style="primary"), KeyboardButton("💰 ALL USER BALANCE", style="primary")],
        [KeyboardButton("🔙 BACK TO ADMIN", style="danger")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def system_config_keyboard():
    keyboard = [
        [KeyboardButton("📈 TODAY ALL STATUS", style="success"), KeyboardButton("👤 USER STATUS CHECK", style="success")],
        [KeyboardButton("⛔ BAN USER", style="danger"), KeyboardButton("🔓 UNBAN USER", style="primary")],
        [KeyboardButton("📜 BAN USER LIST", style="primary"), KeyboardButton("💱 OTP RATE", style="primary")],
        [KeyboardButton("➖ REMOVE BALANCE", style="danger"), KeyboardButton("➕ ADD BALANCE", style="success")],
        [KeyboardButton("📡 MANAGE SERVICES", style="primary"), KeyboardButton("🔘 MANAGE BUTTONS", style="primary")],
        [KeyboardButton("🔢 NUMBER MANAGE", style="primary"), KeyboardButton("🎁 REFER CONTROL", style="primary")],
        [KeyboardButton("🔙 BACK TO ADMIN", style="danger")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def withdraw_method_keyboard():
    flags = get_payment_flags()
    styles = {"pm_bkash": "success", "pm_nagad": "success", "pm_rocket": "primary", "pm_binance": "primary"}
    buttons = [
        KeyboardButton(PAYMENT_METHOD_LABELS[key], style=styles[key])
        for key in ("pm_bkash", "pm_nagad", "pm_rocket", "pm_binance")
        if flags.get(key, True)
    ]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([KeyboardButton("❌ CANCEL", style="danger")])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

# ==================== HELPER FUNCTIONS SECTION ====================

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
    today_midnight = datetime(now.year, now.month, now.day, 0, 0, 0)
    return today_midnight

def is_valid_bangladesh_number(number):
    number = re.sub(r'\D', '', str(number))
    return len(number) == 11 and number.startswith('01')

def is_valid_binance_id(binance_id):
    """Binance Pay ID / UID is a plain numeric identifier (not a phone number) —
    typically 8-12 digits, but we accept 6-15 to be safe across account types."""
    binance_id = re.sub(r'\D', '', str(binance_id))
    return 6 <= len(binance_id) <= 15

def is_range_request(param):
    return 'X' in param.upper()

def is_referral_request(param):
    return param.isdigit()

# ==================== DATABASE FUNCTIONS SECTION ====================
# load_data/save_data are now defined above (work with the unified database)

# Serializes all read-modify-write balance operations so concurrent OTP credits,
# withdraws, and admin add/remove-balance actions can't overwrite each other.
balance_lock = asyncio.Lock()

def get_user(uid):
    uid = str(uid)
    data = load_data()
    if uid not in data:
        data[uid] = {"user_id": uid, "balance": 0.0, "total_numbers": 0, "referral_count": 0}
        save_data(data)
    return data[uid]

async def update_db_balance(uid, amount):
    uid = str(uid)
    async with balance_lock:
        data = load_data()
        if uid not in data:
            data[uid] = {"user_id": uid, "balance": 0.0, "total_numbers": 0, "referral_count": 0}
        data[uid]["balance"] = round(data[uid].get("balance", 0.0) + amount, 2)
        save_data(data)
        return data[uid]["balance"]

async def try_deduct_balance(uid, amount):
    """Atomically deduct `amount` from uid's balance only if funds are sufficient.
    Returns the new balance on success, or None if the balance was too low
    (prevents two concurrent withdraws from both passing an earlier balance check)."""
    uid = str(uid)
    async with balance_lock:
        data = load_data()
        if uid not in data:
            data[uid] = {"user_id": uid, "balance": 0.0, "total_numbers": 0, "referral_count": 0}
        current = data[uid].get("balance", 0.0)
        if current < amount:
            return None
        data[uid]["balance"] = round(current - amount, 2)
        save_data(data)
        return data[uid]["balance"]

# Serializes "is this OTP already paid?" checks so the auto-monitor and a manual
# SEARCH OTP request can never both see "not yet paid" for the same OTP and both
# credit it — balance is only ever added once per real OTP, no matter which path
# notices it first.
otp_credit_lock = asyncio.Lock()

async def credit_otp_if_new(sms_key, uid, otp_code=None):
    """Atomically marks sms_key as paid and credits OTP_RATE to uid, but only the
    first time this sms_key is seen. Returns True if this call actually credited
    it, False if it was already paid out (by any code path) — so callers never
    double-pay or double-notify for the same OTP."""
    uid = str(uid)
    async with otp_credit_lock:
        paid_data = load_data(PAID_SMS_FILE)
        if sms_key in paid_data:
            return False
        paid_data[sms_key] = {"uid": uid, "otp": otp_code}
        save_data(paid_data, PAID_SMS_FILE)
    await update_db_balance(uid, get_otp_rate())
    add_otp_received(uid)
    try:
        if is_ref_commission_on():
            ref = load_data(USER_DATA_FILE).get(uid, {}).get("referred_by")
            comm = calc_ref_commission()
            if ref and comm > 0 and not is_user_banned(ref):
                await update_db_balance(ref, comm)
                add_referral_earning(ref, comm)
    except Exception as e:
        print(f"Referral commission error: {e}")
    return True

def get_all_users():
    data = load_data(USER_DATA_FILE)
    return list(data.keys()) if data else []

def user_exists(uid):
    data = load_data(USER_DATA_FILE)
    return str(uid) in data

# ==================== STATS FUNCTIONS SECTION ====================

def load_stats():
    return load_data(STATS_FILE)

def save_stats(stats):
    save_data(stats, STATS_FILE)

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

    today_numbers = sum(1 for t in numbers_taken if datetime.fromisoformat(t) >= today_midnight)
    today_otps = sum(1 for t in otps_received if datetime.fromisoformat(t) >= today_midnight)
    last24h_numbers = sum(1 for t in numbers_taken if datetime.fromisoformat(t) > last_24h)
    last24h_otps = sum(1 for t in otps_received if datetime.fromisoformat(t) > last_24h)
    last7d_numbers = sum(1 for t in numbers_taken if datetime.fromisoformat(t) > last_7d)
    last7d_otps = sum(1 for t in otps_received if datetime.fromisoformat(t) > last_7d)
    total_numbers = len(numbers_taken)
    total_otps = len(otps_received)

    return {
        "total_numbers": total_numbers, "total_otps": total_otps,
        "today_numbers": today_numbers, "today_otps": today_otps,
        "last24h_numbers": last24h_numbers, "last24h_otps": last24h_otps,
        "last7d_numbers": last7d_numbers, "last7d_otps": last7d_otps
    }

def log_global_activity(uid, action, details):
    """Activity log is disabled: nothing is written to any file or database."""
    return

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

# ==================== LEADERBOARD SECTION ====================

async def remember_user_name(user):
    """Keep the user's Telegram name/username in their record (used by the leaderboard)."""
    try:
        uid_str = str(user.id)
        full = (user.full_name or "").strip()
        uname = user.username or ""
        async with balance_lock:
            data = load_data(USER_DATA_FILE)
            rec = data.get(uid_str)
            if rec is not None and (rec.get("full_name") != full or rec.get("username") != uname):
                rec["full_name"] = full
                rec["username"] = uname
                save_data(data)
    except Exception as e:
        print(f"remember_user_name error: {e}")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return

    stats_data = load_stats()
    today_midnight = get_date_reset_time()
    user_data_all = load_data(USER_DATA_FILE)

    user_today_counts = []

    for uid_str, user_stats in stats_data.items():
        otps_received = user_stats.get("otps_received", [])
        today_count = 0
        for ts in otps_received:
            try:
                dt = datetime.fromisoformat(ts)
                if dt >= today_midnight:
                    today_count += 1
            except:
                continue
        if today_count > 0:
            name = (user_data_all.get(uid_str, {}).get("full_name") or "").strip()
            if not name:
                name = (user_data_all.get(uid_str, {}).get("username") or "").strip()
            if not name:
                name = "Unknown User"
            user_today_counts.append((uid_str, today_count, html.escape(name[:25])))

    user_today_counts.sort(key=lambda x: x[1], reverse=True)
    top10 = user_today_counts[:10]

    if not top10:
        msg = (
            "<b>🏆 TOP 10 OTP LEADERBOARD 🏆</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "❌ No one has received an OTP today yet.\n"
        )
    else:
        msg = (
            "<b>🏆 TOP 10 OTP RECEIVERS (TODAY) 🏆</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for idx, (uid_str, count, name) in enumerate(top10, 1):
            if idx == 1:
                medal = "🥇"
            elif idx == 2:
                medal = "🥈"
            elif idx == 3:
                medal = "🥉"
            else:
                medal = f"{idx}️⃣"
            msg += f"{medal} <b>{name}</b>\n   🔑 <code>{count}</code> OTPs\n\n"
        msg += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📊 <i>Resets daily at 12 AM</i>"
        )

    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=main_keyboard(uid))

# ==================== TRAFFIC SECTION ====================
# Shows the 10 ranges receiving the most OTPs on the panel (the panel itself decides
# how far back its list goes and when it resets), with the service seen most on each range.

_TRAFFIC_EXTRA = {
    "imo": "IMO", "chatgpt": "CHATGPT", "openai": "OPENAI", "tinder": "TINDER", "bumble": "BUMBLE",
    "grab": "GRAB", "foodpanda": "FOODPANDA", "shopee": "SHOPEE", "lazada": "LAZADA", "temu": "TEMU",
    "aliexpress": "ALIEXPRESS", "alibaba": "ALIBABA", "airbnb": "AIRBNB", "booking": "BOOKING",
    "steam": "STEAM", "roblox": "ROBLOX", "garena": "GARENA", "truecaller": "TRUECALLER",
    "skype": "SKYPE", "zoom": "ZOOM", "dropbox": "DROPBOX", "paytm": "PAYTM", "phonepe": "PHONEPE",
    "gcash": "GCASH", "payoneer": "PAYONEER", "okx": "OKX", "bybit": "BYBIT", "kucoin": "KUCOIN",
    "bitget": "BITGET", "mexc": "MEXC", "huawei": "HUAWEI", "samsung": "SAMSUNG", "vk": "VK",
    "yandex": "YANDEX", "kakao": "KAKAO", "naver": "NAVER", "zalo": "ZALO", "likee": "LIKEE",
    "bigo": "BIGO", "botim": "BOTIM", "ebay": "EBAY", "shein": "SHEIN", "hotmail": "MICROSOFT",
    "twitter": "TWITTER", "tiktok": "TIKTOK", "facebook": "FACEBOOK", "instagram": "INSTAGRAM",
    "whatsapp": "WHATSAPP", "telegram": "TELEGRAM", "google": "GOOGLE", "snapchat": "SNAPCHAT",
}

def _traffic_service(o, sms):
    """Best-effort service name for one OTP: panel field -> known keywords -> brand found in the SMS."""
    for k in ("service", "app", "app_name", "sid", "platform", "cli", "sender"):
        v = o.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().upper()
    name = detect_service(sms)
    if name and name != "SMS SERVICE":
        return name
    low = (sms or "").lower()
    for kw, nm in sorted(_TRAFFIC_EXTRA.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", low):
            return nm
    for pat in (r"\[([^\]]{2,20})\]",
                r"(?:your|use|enter)\s+([A-Za-z][A-Za-z0-9]{1,15})\s+(?:verification|confirmation|security|login|log-in|code|otp|pin)",
                r"^\W*([A-Za-z][A-Za-z0-9]{1,15})\s+(?:verification|confirmation|security|login|code|otp)",
                r"([A-Za-z][A-Za-z0-9]{1,15})\s+is your"):
        m = re.search(pat, sms or "", re.I)
        if m and not m.group(1).strip().isdigit() and m.group(1).strip().lower() not in ("your", "the", "this", "verification", "security", "login", "code", "otp", "one", "sms"):
            return m.group(1).strip().upper()
    return "OTHER"

async def traffic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return

    try:
        r = await client_async.get(f"{BASE_URL}/api/success-otp-info")
        otps = (r.json().get("data") or {}).get("otps") or []
    except Exception:
        otps = []

    known = {}
    for svc in get_cached_services():
        for rng in svc.get("ranges", []):
            pre = re.sub(r"\D", "", re.sub(r"[xX]+$", "", str(rng)))
            if pre:
                known[pre] = str(rng)
    prefixes = sorted(known, key=len, reverse=True)

    # platform -> {range -> OTP count}
    platforms = {}
    for o in otps:
        num = normalize_number(o.get("number", ""))
        if not num:
            continue
        rng = next((known[pre] for pre in prefixes if num.startswith(pre)), None)
        if not rng:
            rng = (num[:-3] if len(num) > 3 else num) + "XXX"
        sms = o.get("message") or o.get("otp") or o.get("sms") or ""
        name = _traffic_service(o, sms)
        pr = platforms.setdefault(name, {})
        pr[rng] = pr.get(rng, 0) + 1

    # biggest platform first ("OTHER" always last); each shows its top 3 ranges
    ordered = sorted(platforms.items(), key=lambda x: (x[0] == "OTHER", -sum(x[1].values())))[:10]

    if not ordered:
        msg = (
            "<b>🚦 TRAFFIC 🚦</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "❌ No traffic data available right now.\n"
        )
    else:
        nums = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        head = (
            "<b>🚦 LIVE RANGE TRAFFIC 🚦</b>\n"
            "<i>Top 3 ranges of each platform</i>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        foot = (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🕒 <i>Last 1 Hour</i>"
        )
        blocks = []
        for idx, (name, rngs) in enumerate(ordered):
            top3 = sorted(rngs.items(), key=lambda x: x[1], reverse=True)[:3]
            best = top3[0][1]
            lines = []
            for rng, count in top3:
                flag, _cname = get_country_info(re.sub(r"\D", "", re.sub(r"[xX]+$", "", rng)))
                filled = max(1, round(5 * count / best))
                bar = "▰" * filled + "▱" * (5 - filled)
                lines.append(f"{flag} <code>{html.escape(rng)}</code> · <b>{count}</b> {bar}")
            blocks.append(
                f"{nums[idx]} <b>{html.escape(str(name))}</b> · 🔑 {sum(rngs.values())} OTP\n"
                f"<blockquote>" + "\n".join(lines) + "</blockquote>\n"
            )
        while len(blocks) > 1 and len(head) + sum(len(b_) for b_ in blocks) + len(foot) > 3900:
            blocks.pop()
        msg = head + "".join(blocks) + foot

    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=main_keyboard(uid))

# ==================== 2FA CODE GENERATOR SECTION ====================

def generate_2fa_code(secret_key):
    try:
        clean_secret = secret_key.replace(" ", "").strip()
        totp = pyotp.TOTP(clean_secret)
        otp = totp.now()
        return otp, clean_secret
    except:
        return None, None

async def get_2fa_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return
    context.user_data["mode"] = "get_2fa"
    await update.message.reply_text(
        "⚡ <b>GET 2FA CODE</b> ⚡\n\n"
        "<blockquote>🔑 ENTER YOUR 2FA SECRET KEY:</blockquote>",
        parse_mode="HTML"
    )

async def process_2fa_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    secret_key = update.message.text.strip()
    context.user_data["mode"] = None

    otp_code, clean_key = generate_2fa_code(secret_key)

    if otp_code is None:
        await update.message.reply_text(
            "❌ <b>INVALID 2FA SECRET KEY</b>\n\n⚠️ Please send a valid base32 key.",
            parse_mode="HTML",
            reply_markup=main_keyboard(uid)
        )
        return

    now = datetime.now()
    final_msg = (
        "✅ <b>2FA CODE GENERATED!</b>\n\n"
        f"<blockquote>🔑 KEY: <code>{clean_key}</code></blockquote>\n"
        f"<blockquote>🔢 CODE: <code>{otp_code}</code></blockquote>\n"
        f"<blockquote>⏳ EXPIRES IN: 30 SECONDS</blockquote>\n"
        f"📅 {now.strftime('%d %B, %Y')} | {now.strftime('%I:%M %p')}"
    )
    await update.message.reply_text(final_msg, parse_mode="HTML")

# ==================== GET NUMBER — LIVEACCESS SERVICE SELECTION (FIXED: REMOVED HTML TAGS) ====================

# ── Service list layout ──
# 2 columns. Each service gets its own icon, the count sits after a dot, and the
# button colour shows the stock level:  green = many, blue = medium, red = few.
_SVC_NAME_MAX = 11
_SVC_HIGH = 10      # this many ranges or more  -> green
_SVC_MID = 3        # this many ranges or more  -> blue, below that -> red

_SVC_ICONS = {
    "FACEBOOK": "📘", "INSTAGRAM": "📸", "WHATSAPP": "💬", "TELEGRAM": "✈️",
    "TIKTOK": "🎵", "IMO": "💙", "TWILIO": "🔔", "BOLT": "⚡", "UBER": "🚕",
    "DISCORD": "🎮", "TINDER": "🔥", "ALIPAY": "💳", "VERIFY": "✅",
    "LETZ": "🎯", "GOOGLE": "🔍", "TWITTER": "🐦", "SNAPCHAT": "👻",
    "PAYPAL": "💰", "AMAZON": "📦", "MICROSOFT": "🪟", "APPLE": "🍎",
}

def _svc_display_name(sid):
    name = str(sid).strip().upper()
    if name.isdigit():                      # a phone number used as a service name
        name = "+" + name
        return name[:8] + "…" if len(name) > 8 else name
    if len(name) > _SVC_NAME_MAX:
        name = name[:_SVC_NAME_MAX - 1] + "…"
    return name

def _svc_icon(sid):
    key = str(sid).strip().upper()
    if key.isdigit():
        return "📞"
    for word, icon in _SVC_ICONS.items():
        if word in key:
            return icon
    return "📱"

def _svc_style(count):
    if count >= _SVC_HIGH:
        return "success"
    if count >= _SVC_MID:
        return "primary"
    return "danger"

# ── Which design is live (admin: MANAGE SERVICES → V1 / V2 / V3) ──
SERVICE_DESIGN_NAMES = {1: "V1 · Classic", 2: "V2 · Icons", 3: "V3 · Bars"}
DEFAULT_SERVICE_DESIGN = 1

def get_service_design():
    try:
        v = int(load_data(SITE_SETTINGS_FILE).get("service_design", DEFAULT_SERVICE_DESIGN))
    except (TypeError, ValueError):
        v = DEFAULT_SERVICE_DESIGN
    return v if v in SERVICE_DESIGN_NAMES else DEFAULT_SERVICE_DESIGN

def set_service_design(v):
    settings = load_data(SITE_SETTINGS_FILE)
    settings["service_design"] = int(v)
    save_data(settings, SITE_SETTINGS_FILE)

def _legend_html():
    """Small colour/bar guide shown under the GET NUMBER text (V2 and V3 only)."""
    v = get_service_design()
    if v == 2:
        return "\n<i>🟢 Many  🔵 Medium  🔴 Few</i>"
    if v == 3:
        return "\n<i>▰▰▰ stock level  ·  🟢 Many  🔵 Medium  🔴 Few</i>"
    return ""

# ── V1: the original classic layout (rocket icon, count in brackets, colour cycle) ──
_SVC_STYLES = ["danger", "primary", "success", "danger", "primary", "success",
               "danger", "primary", "success", "danger", "primary", "success"]

def _build_services_keyboard_v1(services):
    buttons = []
    for i, svc in enumerate(services):
        sid = svc.get("sid", f"Service {i+1}")
        label = f"🚀 {sid} ({len(svc.get('ranges', []))})"
        buttons.append(InlineKeyboardButton(label, callback_data=f"svc_{i}", style=_SVC_STYLES[i % len(_SVC_STYLES)]))
    max_len = max((len(btn.text) for btn in buttons), default=0)
    cols = 2 if max_len > 14 else 3
    rows = [buttons[j:j + cols] for j in range(0, len(buttons), cols)]
    rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range", style="danger")])
    return InlineKeyboardMarkup(rows)

# ── V3: 2 columns, no icons — name + small 3-step stock bar + count ──
_SVC_V3_NAME_MAX = 9

def _svc_v3_name(sid):
    name = _svc_display_name(sid)
    return name if len(name) <= _SVC_V3_NAME_MAX else name[:_SVC_V3_NAME_MAX - 1] + "…"

def _build_services_keyboard_v3(services):
    items = [(i, svc.get("sid", f"Service {i+1}"), len(svc.get("ranges", [])))
             for i, svc in enumerate(services)]
    items.sort(key=lambda t: -t[2])
    buttons = []
    for i, sid, count in items:
        filled = 0 if count <= 0 else (3 if count >= _SVC_HIGH else 2 if count >= _SVC_MID else 1)
        bar = "▰" * filled + "▱" * (3 - filled)
        buttons.append(InlineKeyboardButton(f"{_svc_v3_name(sid)} {bar} {count}",
                                            callback_data=f"svc_{i}", style=_svc_style(count)))
    rows = [buttons[j:j + 2] for j in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range", style="danger")])
    return InlineKeyboardMarkup(rows)

def _build_services_keyboard(services):
    v = get_service_design()
    if v == 3:
        return _build_services_keyboard_v3(services)
    if v == 2:
        return _build_services_keyboard_v2(services)
    return _build_services_keyboard_v1(services)

def _build_services_keyboard_v2(services):
    items = []
    for i, svc in enumerate(services):
        sid = svc.get("sid", f"Service {i+1}")
        items.append((i, sid, len(svc.get("ranges", []))))

    # biggest first; callback_data keeps the ORIGINAL index i, so the click handler is unaffected.
    items.sort(key=lambda t: -t[2])

    buttons = [
        InlineKeyboardButton(f"{_svc_icon(sid)} {_svc_display_name(sid)} · {count}",
                             callback_data=f"svc_{i}", style=_svc_style(count))
        for i, sid, count in items
    ]
    rows = [buttons[j:j + 2] for j in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range", style="danger")])
    return InlineKeyboardMarkup(rows)

def _build_countries_keyboard(ranges, service_idx):
    """Shows the country flag + name from the ranges."""
    btns = []
    seen = {}
    # country button colors rotate
    clrs = ["primary", "success", "danger", "primary", "success", "danger"]
    ci   = 0
    for i, r in enumerate(ranges[:24]):
        prefix = re.sub(r'[xX]+$', '', str(r)).strip()
        prefix_clean = re.sub(r'\D', '', prefix)
        flag, cname = get_country_info(prefix_clean)
        label = f"{flag} {cname}"
        if label not in seen:
            seen[label] = i
            color = clrs[ci % len(clrs)]
            ci += 1
            btns.append(InlineKeyboardButton(label, callback_data=f"rng_{i}", style=color))
    rows = [btns[j:j+2] for j in range(0, len(btns), 2)]
    rows.append([InlineKeyboardButton("◀️ BACK", callback_data="back_services", style="danger")])
    return InlineKeyboardMarkup(rows)

async def show_app_selection(update, context):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return

    services = get_cached_services()
    if not services:
        await _do_liveaccess_fetch()
        services = get_cached_services()

    disabled = get_disabled_services()
    services = [s for s in services if s.get("sid") not in disabled]

    if not services:
        await update.message.reply_text(
            "⚠️ <b>No service available</b>\n⏳ Please try again in a moment.",
            parse_mode="HTML",
            reply_markup=main_keyboard(uid)
        )
        return

    context.user_data["la_services"] = services
    keyboard = _build_services_keyboard(services)
    await update.message.reply_text(
        "📞 <b>GET NUMBER</b>\n\n"
        "<blockquote>✨ Select your preferred <b>Service</b> from below:</blockquote>" + _legend_html(),
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ==================== AUTO OTP MONITOR SECTION ====================

async def monitor_loop(app):
    range_db = load_data(DATA_RANGE_FILE)
    # Local per-session cache of sms_keys already seen, just to skip redundant
    # lock/DB round-trips within this loop's lifetime. NOT the source of truth —
    # credit_otp_if_new() re-checks the real DB atomically before paying out.
    processed_in_session = set()

    while True:
        if not active_numbers:
            # Nobody is waiting for an OTP — don't hit the panel API at all.
            await asyncio.sleep(IDLE_CHECK_INTERVAL)
            continue
        if len(processed_in_session) > 5000:
            processed_in_session.clear()
        try:
            r = await client_async.get(f"{BASE_URL}/api/success-otp-info")
            res = r.json()
            if "data" in res and "otps" in res["data"]:
                otps = res["data"]["otps"]

                for otp in otps:
                    num = normalize_number(otp.get("number", ""))
                    full_sms = otp.get('message') or otp.get('otp') or otp.get('sms') or "No SMS Content"
                    otp_code = extract_otp(full_sms)
                    otp_id = str(otp.get("otp_id", ""))
                    sms_key = otp_id if otp_id else f"{num}_{full_sms}"

                    if num in active_numbers and sms_key not in processed_in_session:
                        details = active_numbers[num]

                        credited = await credit_otp_if_new(sms_key, details["uid"], otp_code)
                        processed_in_session.add(sms_key)
                        if not credited:
                            # Already paid via another path (e.g. a manual SEARCH OTP
                            # that raced ahead of us) — don't pay or notify again.
                            continue

                        log_global_activity(details["uid"], "OTP_RECEIVED", {"number": num, "otp": otp_code, "sms": full_sms})

                        num_range_info = range_db.get(num, {}).get("range", "")
                        if not num_range_info:
                            num_range_info = active_numbers.get(num, {}).get("range", "")
                        if not num_range_info and num:
                            _d = re.sub(r'\D', '', str(num))
                            num_range_info = (_d[:-3] + 'XXX') if len(_d) > 3 else (_d + 'XXX')

                        country_flag, country_name = get_country_info(num)
                        service_name = detect_service(full_sms)
                        clean_num = num.replace('+', '').strip()
                        full_number = f"+{clean_num}"
                        masked_number = f"+{mask_number(clean_num)}"

                        safe_full_sms = html.escape(str(full_sms))
                        safe_otp_code = html.escape(str(otp_code))

                        user_msg = (
                            f"✅ <b>OTP RECEIVE SUCCESSFUL</b> ✅\n\n"
                            f"<blockquote>📶 RANGE: <code>{num_range_info}</code></blockquote>\n"
                            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
                            f"<blockquote>📱 SERVICE: <code>{service_name}</code></blockquote>\n"
                            f"<blockquote>📞 NUMBER: <code>{full_number}</code></blockquote>\n"
                            f"<blockquote>🔑 OTP: <code>{safe_otp_code}</code></blockquote>\n\n"
                            f"<blockquote>📩 FULL SMS:\n<code>{safe_full_sms}</code></blockquote>\n\n"
                            f"<b>💵 ADD BALANCE FOR {get_otp_rate():.2f} BDT</b>"
                        )
                        # NUMBER TEMPLATE V2 ON → plain OTP message (flag + number + OTP only)
                        user_markup = None
                        if is_number_template_v2_on():
                            user_msg = build_otp_text_v2(country_flag, clean_num, otp_code)
                            user_markup = build_otp_keyboard_v2(otp_code)

                        group_msg = (
                            f"✅ <b>OTP RECEIVE SUCCESSFUL</b> ✅\n\n"
                            f"<blockquote>📶 RANGE: <code>{num_range_info}</code></blockquote>\n"
                            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
                            f"<blockquote>📱 SERVICE: <code>{service_name}</code></blockquote>\n"
                            f"<blockquote>📞 NUMBER: <code>{masked_number}</code></blockquote>\n"
                            f"<blockquote>🔑 OTP: <code>{safe_otp_code}</code></blockquote>\n\n"
                            f"<blockquote>📩 FULL SMS:\n<code>{safe_full_sms}</code></blockquote>"
                        )

                        # ★★★ GROUP BUTTONS COLOR UPDATED ★★★
                        group_buttons = InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton("‼️ PANEL", url=PANEL_BOT_LINK, style="danger"),
                                InlineKeyboardButton("📢 CHANNEL", url=CHANNEL_LINK, style="success")
                            ]
                        ])

                        try:
                            await app.bot.send_message(details["uid"], user_msg, parse_mode="HTML", reply_markup=user_markup)
                        except Exception as e:
                            print(f"❌ User Message Send Fail: {e}")

                        try:
                            await app.bot.send_message(OTP_GROUP_ID, group_msg, parse_mode="HTML", reply_markup=group_buttons)
                        except Exception as e:
                            print(f"❌ Group Send Fail: {e}")

                current_time = datetime.now()
                for num_key in list(active_numbers.keys()):
                    entry = active_numbers[num_key]
                    if 'timestamp' not in entry:
                        entry['timestamp'] = current_time
                    elif (current_time - entry['timestamp']).total_seconds() > 3600:
                        del active_numbers[num_key]

        except Exception as e:
            print(f"Monitor Error: {e}")
        await asyncio.sleep(CHECK_INTERVAL)

# ==================== WORKER & API SECTION ====================

async def fetch_number_async(range_str):
    try:
        r = await client_async.post(
            f"{BASE_URL}/api/getnum",
            json={"range": range_str, "is_national": False}
        )
        data = r.json()
        d = data.get("data", {})
        if "full_number" in d:
            return {
                "number":  d["full_number"],
                "otp_now": bool(d.get("otp_now", False)),
                "otp":     d.get("otp"),
                "sms":     d.get("sms"),
            }
    except Exception as e:
        print(f"Fetch number error: {e}")
    return None

async def fast_allocate_number(query, context, range_text, sid):
    uid = query.from_user.id

    if is_user_banned(uid):
        await query.message.edit_text(tr(uid, "banned"))
        return

    try:
        res = await fetch_number_async(range_text)
    except Exception as e:
        await query.message.edit_text(f"❌ Server error: {str(e)[:100]}")
        return

    if not res or not res.get("number"):
        await query.message.edit_text(
            "❌ <b>No number found.</b>\n\n"
            "<blockquote>⚠️ No number is available in this range right now, or the server is busy.\n"
            "Please try another range.</blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 BACK", callback_data="back_services", style="danger")
            ]])
        )
        return

    clean_num = normalize_number(res["number"])
    add_number_taken(uid, 1)
    last_range[uid] = range_text
    last_service[uid] = {"range": range_text, "sid": sid}
    active_numbers[clean_num] = {"uid": uid, "range": range_text, "timestamp": datetime.now()}
    save_number_range_info(uid, clean_num, range_text)

    country_flag, country_name = get_country_info(clean_num)

    _v2 = is_number_template_v2_on()
    if res.get("otp_now") and res.get("otp"):
        otp_safe = html.escape(str(res["otp"]))
        sms_safe  = html.escape(str(res.get("sms") or ""))
        add_otp_received(uid)
        text = build_number_text_v2(country_flag, clean_num, res["otp"], res.get("sms")) if _v2 else (
            f"✅ <b>YOUR NUMBER</b> ✅\n\n"
            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {html.escape(country_name)}</code></blockquote>\n"
            f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n"
            f"<blockquote>📞 NUMBER: <code>+{clean_num}</code></blockquote>\n"
            f"<blockquote>🔑 OTP: <code>{otp_safe}</code></blockquote>"
            + (f"\n<blockquote>📩 SMS: <code>{sms_safe}</code></blockquote>" if sms_safe else "")
            + "\n\n<b>✅ OTP RECEIVED INSTANTLY!</b>"
        )
    else:
        text = build_number_text_v2(country_flag, clean_num) if _v2 else (
            f"✅ <b>YOUR NUMBER</b> ✅\n\n"
            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {html.escape(country_name)}</code></blockquote>\n"
            f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n"
            f"<blockquote>📞 NUMBER: <code>+{clean_num}</code></blockquote>\n\n"
            f"<b>📩 SMS STATUS: ⏳ WAITING...</b>"
        )

    # ★★★ USER BUTTONS COLOR UPDATED ★★★
    keyboard = build_number_keyboard(clean_num, _v2, country_flag, sid)
    try:
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        print(f"fast_allocate edit error: {e}")

async def worker():
    while True:
        task = await request_queue.get()
        try:
            if task['type'] == 'process_numbers':
                await process_numbers(task['update'], task['context'], task['range_text'], task['count'])
            elif task['type'] == 'search_otp':
                await perform_otp_search(task['update'], task['context'], task['target_num'])
            elif task['type'] == 'auto_number':
                await process_auto_number(task['update'], task['context'], task['range_text'])
        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            request_queue.task_done()

# ==================== AUTO NUMBER FROM LINK / DEEP LINK ====================

async def process_auto_number(update, context, range_text):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    if is_user_banned(uid):
        await context.bot.send_message(chat_id=chat_id, text=tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return

    status_msg = await context.bot.send_message(chat_id=chat_id, text="🔍 SEARCHING...")

    try:
        res = await fetch_number_async(range_text)
        if not res:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return

        generated_num = normalize_number(res["number"]) if res else None
        if not generated_num:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return

        add_number_taken(uid, 1)
        last_range[uid] = range_text
        last_service.pop(uid, None)
        active_numbers[generated_num] = {"uid": uid, "range": range_text, "timestamp": datetime.now()}
        save_number_range_info(uid, generated_num, range_text)

        country_flag, country_name = get_country_info(generated_num)

        _v2 = is_number_template_v2_on()
        if res.get("otp_now") and res.get("otp"):
            instant_otp = html.escape(str(res["otp"]))
            instant_sms = html.escape(str(res.get("sms") or ""))
            add_otp_received(uid)
            final_text = build_number_text_v2(country_flag, generated_num, res["otp"], res.get("sms")) if _v2 else (
                f"✅ <b>YOUR NUMBER DETAILS</b> ✅\n\n"
                f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
                f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n\n"
                f"<blockquote>📞 NUMBER: <code>+{generated_num}</code></blockquote>\n\n"
                f"<blockquote>🔑 OTP: <code>{instant_otp}</code></blockquote>\n"
                + (f"<blockquote>📩 SMS: <code>{instant_sms}</code></blockquote>\n" if instant_sms else "")
                + f"\n<b>✅ OTP RECEIVED INSTANTLY!</b>"
            )
        else:
            final_text = build_number_text_v2(country_flag, generated_num) if _v2 else (
                f"✅ <b>YOUR NUMBER DETAILS</b> ✅\n\n"
                f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
                f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n\n"
                f"<blockquote>📞 NUMBER: <code>+{generated_num}</code></blockquote>\n\n"
                f"<b>📩 SMS STATUS: ⏳ WAITING...</b>"
            )

        # ★★★ SAME RANGE BUTTON COLOR IN AUTO NUMBER (FOR CONSISTENCY) ★★★
        keyboard = build_number_keyboard(generated_num, _v2, country_flag, "")
        await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        print(f"Auto Number Error: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")

# ==================== USER PANEL — PROCESS NUMBERS ====================

async def process_numbers(update_or_query, context, range_text, count):
    if isinstance(update_or_query, Update) and update_or_query.callback_query:
        uid = update_or_query.callback_query.from_user.id
        chat_id = update_or_query.callback_query.message.chat_id
    else:
        uid = update_or_query.effective_user.id
        chat_id = update_or_query.effective_chat.id

    if is_user_banned(uid):
        await context.bot.send_message(chat_id=chat_id, text=tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return

    status_msg = await context.bot.send_message(chat_id=chat_id, text="🔍 SEARCHING . . .")

    try:
        add_number_taken(uid, count)
        last_range[uid] = range_text

        tasks = [fetch_number_async(range_text) for _ in range(count)]
        results = await asyncio.gather(*tasks)
        valid_results = [r for r in results if r and r.get("number")]

        if not valid_results:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return False

        num_entries = []
        for r in valid_results:
            clean_num = normalize_number(r["number"])
            if clean_num:
                active_numbers[clean_num] = {"uid": uid, "range": range_text, "timestamp": datetime.now()}
                save_number_range_info(uid, clean_num, range_text)
                num_entries.append({
                    "num":     clean_num,
                    "otp_now": r.get("otp_now", False),
                    "otp":     r.get("otp"),
                    "sms":     r.get("sms"),
                })

        if not num_entries:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return False

        country_flag, country_name = get_country_info(num_entries[0]["num"])

        num_lines = []
        for entry in num_entries:
            if entry["otp_now"] and entry["otp"]:
                otp_safe = html.escape(str(entry["otp"]))
                sms_safe = html.escape(str(entry.get("sms") or ""))
                add_otp_received(uid)
                line = (
                    f"<blockquote>📞 NUMBER: <code>+{entry['num']}</code>\n"
                    f"🔑 OTP: <code>{otp_safe}</code>"
                    + (f"\n📩 SMS: <code>{sms_safe}</code>" if sms_safe else "")
                    + "</blockquote>"
                )
            else:
                line = f"<blockquote>📞 NUMBER: <code>+{entry['num']}</code></blockquote>"
            num_lines.append(line)

        num_list_text = "\n".join(num_lines)
        any_instant = any(e["otp_now"] and e["otp"] for e in num_entries)
        sms_status = "✅ OTP RECEIVED INSTANTLY!" if any_instant else "📩 SMS STATUS: ⏳ WAITING..."

        final_text = (
            f"✅ <b>YOUR NUMBER DETAILS</b> ✅\n\n"
            f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
            f"<blockquote>📶 RANGE: <code>{range_text}</code></blockquote>\n\n"
            f"{num_list_text}\n\n"
            f"<b>{sms_status}</b>"
        )

        # ★★★ NUMBER TEMPLATE VERSION 2 (flag + number only) ★★★
        _v2 = is_number_template_v2_on()
        if _v2:
            _e0 = num_entries[0]
            final_text = build_number_text_v2(country_flag, _e0["num"], _e0["otp"] if _e0["otp_now"] else None)

        # ★★★ PROCESS NUMBERS BUTTONS COLOR UPDATE (FOR SINGLE NUMBER) ★★★
        _svc = last_service.get(uid) or {}
        _sid = _svc.get("sid", "") if _svc.get("range") == range_text else ""
        keyboard = build_number_keyboard(num_entries[0]["num"], _v2, country_flag, _sid)

        await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=keyboard)
        return True

    except Exception as e:
        print(f"Process Number Error: {e}")
        await status_msg.edit_text(f"❌ System Error: {str(e)}")
        return False

async def perform_otp_search(update, context, target_num):
    uid = str(update.effective_user.id)

    if is_user_banned(int(uid)):
        await update.message.reply_text(tr(int(uid), "banned"), reply_markup=main_keyboard(int(uid)))
        return

    # Ownership check — only let a user search OTPs for a number they actually took
    # themselves. Uses the persistent range_db (not the in-memory active_numbers,
    # which expires after 1hr / resets on restart) so this still works for recovery,
    # but blocks users from fishing for OTPs/credit on numbers that aren't theirs.
    if not is_admin(int(uid)):
        range_db = load_range_db()
        owner_record = range_db.get(target_num)
        if not owner_record or str(owner_record.get("user_id")) != uid:
            await update.message.reply_text(
                "🚫 <b>এই নাম্বারটি আপনার নেওয়া নয়।</b>\n\n"
                "<blockquote>শুধু নিজের নেওয়া নাম্বারের OTP সার্চ করা যাবে।</blockquote>",
                parse_mode="HTML",
                reply_markup=main_keyboard(int(uid))
            )
            return

    status_msg = await update.message.reply_text("🔍 SEARCHING IN SERVER...")

    try:
        r = await client_async.get(f"{BASE_URL}/api/success-otp-info")
        res = r.json()

        if "data" in res and "otps" in res["data"]:
            all_otps = res["data"]["otps"]
            found_otps = [o for o in all_otps if normalize_number(o.get("number", "")) == target_num]

            if not found_otps:
                error_msg = (
                    "━━━━━━━━━━━━━━━━━━\n❌ NO OTP FOUND\n━━━━━━━━━━━━━━━━━━\n\n"
                    f"📞 NUMBER:\n`+{target_num}`\n\n⏳ PLEASE TRY AGAIN LATER\n━━━━━━━━━━━━━━━━━━"
                )
                await status_msg.edit_text(error_msg, parse_mode="Markdown")
                await update.message.reply_text("🔙 RETURNING TO MAIN MENU...", reply_markup=main_keyboard(int(uid)))
            else:
                await status_msg.delete()

                for o in found_otps:
                    full_sms = o.get('message') or o.get('otp') or o.get('sms') or "No Content Found"
                    otp_code = extract_otp(full_sms)
                    otp_id = str(o.get("otp_id", ""))
                    sms_key = otp_id if otp_id else f"{target_num}_{full_sms}"

                    credited = await credit_otp_if_new(sms_key, uid, otp_code)
                    if credited:
                        payment_status = f"💵 ADD BALANCE FOR {get_otp_rate():.2f} BDT"
                    else:
                        payment_status = "❌ ALREADY PAID"

                    country_flag, country_name = get_country_info(target_num)
                    service_name = detect_service(full_sms)

                    msg = (
                        f"✅ <b>OTP FOUND!</b>\n\n"
                        f"<blockquote>🌍 COUNTRY: <code>{country_flag} {country_name}</code></blockquote>\n"
                        f"<blockquote>📱 SERVICE: <code>{service_name}</code></blockquote>\n"
                        f"<blockquote>📞 NUMBER: <code>+{target_num}</code></blockquote>\n"
                        f"<blockquote>🔑 OTP: <code>{html.escape(otp_code)}</code></blockquote>\n\n"
                        f"<blockquote>📩 FULL SMS:\n<code>{html.escape(str(full_sms))}</code></blockquote>\n\n"
                        f"<b>{payment_status}</b>"
                    )
                    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=main_keyboard(int(uid)))
        else:
            await status_msg.edit_text("❌ SERVER RETURNED AN ERROR.")
            await update.message.reply_text("🔙 Returning to Main Menu...", reply_markup=main_keyboard(int(uid)))

    except Exception as e:
        try:
            await status_msg.edit_text(f"❌ Error: {str(e)}")
        except:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        await update.message.reply_text("🔙 Returning to Main Menu...", reply_markup=main_keyboard(int(uid)))

# ==================== REFER AND EARN SECTION ====================

async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return

    user_data = get_user(uid)
    bot_info = await context.bot.get_me()

    referral_link = f"https://t.me/{bot_info.username}?start={uid}"
    successful_refers = get_referral_count(uid)
    bonus = get_referral_bonus()
    total_reward = float(load_referral_data().get(str(uid), {}).get("earned", 0.0))
    comm_line = ""
    if is_ref_commission_on() and calc_ref_commission() > 0:
        comm_line = f"<blockquote>💸 PLUS {calc_ref_commission():g} BDT FOR EVERY OTP YOUR REFERRALS RECEIVE</blockquote>\n\n"

    refer_msg = (
        f"🎁 <b>REFER AND EARN SYSTEM</b> 🎁\n\n"
        f"<blockquote>🚀 INVITE FRIENDS &amp; EARN {format_balance(bonus)} BDT EACH! 💸</blockquote>\n\n"
        f"{comm_line}"
        f"<b>🔗 YOUR REFERRAL LINK:</b>\n"
        f"<blockquote><code>{referral_link}</code></blockquote>\n\n"
        f"<b>📊 YOUR STATS:</b>\n"
        f"<blockquote>👥 TOTAL REFERS: {successful_refers}\n"
        f"💰 TOTAL EARNED: {format_balance(total_reward)} BDT</blockquote>\n\n"
        f"✨ <b>SHARE LINK &amp; EARN MONEY!</b> ✨"
    )

    await update.message.reply_text(
        refer_msg,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("👥 YOUR REFERRAL", callback_data=f"my_ref_{uid}", style="primary")
        ]])
    )

# ==================== WITHDRAW FUNCTIONS ====================

async def withdraw_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id

    if text == "❌ CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return

    label_to_key = {v: k for k, v in PAYMENT_METHOD_LABELS.items() if is_payment_method_enabled(k)}
    method_map = {v: PAYMENT_METHOD_NAMES[k] for k, v in PAYMENT_METHOD_LABELS.items() if is_payment_method_enabled(k)}
    if text in method_map:
        balance = get_user(uid)['balance']
        method_key = label_to_key[text]
        context.user_data["withdraw_method"] = method_map[text]
        context.user_data["withdraw_method_key"] = method_key
        context.user_data["withdraw_mode"] = "amount"
        msg = (
            f"<blockquote>💸 SEND YOUR AMOUNT!\n"
            f"💵 TOTAL BALANCE: {format_balance(balance)} BDT</blockquote>\n\n"
            f"<blockquote>📉 MINIMUM WITHDRAW {get_min_withdraw(method_key):.0f} BDT</blockquote>"
        )
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=cancel_keyboard())
    else:
        await update.message.reply_text("⚠️ PLEASE SELECT A VALID PAYMENT METHOD!", reply_markup=withdraw_method_keyboard())

async def withdraw_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id

    if text == "❌ CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return

    try:
        amount = float(text)
    except:
        await update.message.reply_text("⚠️ PLEASE SEND A VALID AMOUNT!", reply_markup=cancel_keyboard())
        return

    balance = get_user(uid)['balance']
    min_withdraw = get_min_withdraw(context.user_data.get("withdraw_method_key"))
    if amount < min_withdraw or amount > MAX_WITHDRAW:
        await update.message.reply_text(f"📉 MIN: {min_withdraw:.0f} BDT | MAX: {MAX_WITHDRAW} BDT", reply_markup=cancel_keyboard())
        return
    if amount > balance:
        await update.message.reply_text("🚫 INSUFFICIENT BALANCE!", reply_markup=cancel_keyboard())
        return

    context.user_data["withdraw_amount"] = amount
    context.user_data["withdraw_mode"] = "number"

    method_key = context.user_data.get("withdraw_method_key")
    if method_key == "pm_binance":
        await update.message.reply_text(
            "🆔 PLEASE SEND YOUR BINANCE ID!\n\n<blockquote>🔢 EXAMPLE: 432767980</blockquote>",
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
    else:
        await update.message.reply_text(
            "📞 PLEASE SEND YOUR PAYMENT NUMBER!\n\n<blockquote>🔢 EXAMPLE: 017XXXXXXXX</blockquote>",
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )

async def withdraw_number_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id

    if text == "❌ CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return

    method_key = context.user_data.get("withdraw_method_key")
    is_binance = method_key == "pm_binance"

    if is_binance:
        if not is_valid_binance_id(text):
            await update.message.reply_text("⚠️ PLEASE SEND A VALID BINANCE ID!", reply_markup=cancel_keyboard())
            return
    else:
        if not is_valid_bangladesh_number(text):
            await update.message.reply_text("⚠️ PLEASE SEND VALID NUMBER! 017XXXXXXXX", reply_markup=cancel_keyboard())
            return

    method = context.user_data.get("withdraw_method")
    amount = context.user_data.get("withdraw_amount")
    payment_number = text
    payment_id = generate_payment_id()

    context.user_data["temp_withdraw"] = {
        "method": method, "amount": amount,
        "number": payment_number, "payment_id": payment_id
    }

    number_label = "BINANCE ID" if is_binance else "NUMBER"
    msg = (
        "✨ <b>YOUR PAYMENT DETAILS!</b> ✨\n\n"
        f"<blockquote>📝 METHOD: {method}\n"
        f"📞 {number_label}: {payment_number}\n\n"
        f"✅ CORRECT → CONFIRM\n❌ WRONG → CANCEL</blockquote>"
    )
    await update.message.reply_text(
        msg, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ CANCEL", callback_data="withdraw_cancel", style="danger"),
            InlineKeyboardButton("✅ CONFIRM", callback_data="withdraw_confirm", style="success")
        ]])
    )

async def process_withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    temp_data = context.user_data.get("temp_withdraw")
    if not temp_data:
        await query.message.reply_text("⚠️ SESSION EXPIRED.", reply_markup=main_keyboard(uid))
        return

    # Clear immediately so a rapid double-tap on CONFIRM can't submit two withdraw requests
    context.user_data["temp_withdraw"] = None
    context.user_data["withdraw_mode"] = None

    method = temp_data["method"]
    amount = temp_data["amount"]
    payment_number = temp_data["number"]
    payment_id = temp_data["payment_id"]

    new_balance = await try_deduct_balance(uid, amount)
    if new_balance is None:
        await query.message.edit_text("🚫 INSUFFICIENT BALANCE! Your balance may have changed since you started this request.")
        return

    wr = load_withdraw_requests()
    wr[str(payment_id)] = {
        "user_id": uid, "method": method, "amount": amount,
        "number": payment_number, "payment_id": payment_id,
        "status": "pending", "timestamp": datetime.now().isoformat()
    }
    save_withdraw_requests(wr)

    number_label = "BINANCE ID" if method == "BINANCE" else "NUMBER"

    await query.message.edit_text(
        f"✅ <b>WITHDRAWAL REQUEST SUBMITTED</b> ✅\n\n"
        f"<blockquote>📝 METHOD: <code>{method}</code>\n"
        f"📞 {number_label}: <code>{payment_number}</code>\n"
        f"💰 AMOUNT: <code>{format_balance(amount)} BDT</code>\n"
        f"🆔 ID: <code>{payment_id}</code></blockquote>",
        parse_mode="HTML"
    )
    await context.bot.send_message(uid, "🎉 <b>WITHDRAW REQUEST SUBMITTED!</b>", parse_mode="HTML", reply_markup=main_keyboard(uid))

    usd_line = f"\n💵 USD (≈{BDT_TO_USD_RATE} BDT/$): <code>{amount / BDT_TO_USD_RATE:.2f} USD</code>" if method == "BINANCE" else ""
    admin_msg = (
        f"✅ <b>NEW WITHDRAWAL REQUEST</b>\n\n"
        f"<blockquote>🆔 USER: <code>{uid}</code>\n"
        f"📝 METHOD: <code>{method}</code>\n"
        f"📞 {number_label}: <code>{payment_number}</code>\n"
        f"💰 AMOUNT: <code>{format_balance(amount)} BDT</code>{usd_line}\n"
        f"🆔 ID: <code>{payment_id}</code></blockquote>"
    )
    admin_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ REJECT", callback_data=f"admin_reject_{payment_id}", style="danger"),
        InlineKeyboardButton("✅ APPROVE", callback_data=f"admin_approve_{payment_id}", style="success")
    ]])
    for admin_id in ADMINS:
        try:
            await context.bot.send_message(admin_id, admin_msg, parse_mode="HTML", reply_markup=admin_kb)
        except Exception as e:
            print(f"Admin notify fail {admin_id}: {e}")

async def process_withdraw_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    context.user_data["temp_withdraw"] = None
    context.user_data["withdraw_mode"] = None
    await query.message.edit_text("❌ WITHDRAW CANCELLED")
    await context.bot.send_message(uid, tr(uid, "menu_prompt"), parse_mode="Markdown", reply_markup=main_keyboard(uid))

# ==================== ADMIN PANEL - WITHDRAW APPROVAL ====================

async def admin_approve_withdraw(update, context, payment_id):
    query = update.callback_query
    await query.answer()
    wr = load_withdraw_requests()
    if payment_id not in wr:
        await query.message.reply_text("⚠️ REQUEST NOT FOUND!")
        return
    rd = wr[payment_id]
    uid = rd["user_id"]
    method = rd["method"]
    amount = rd["amount"]
    payment_number = rd["number"]

    current_status = rd.get("status")
    if current_status in ("approved", "rejected"):
        await query.answer(f"⚠️ Already {current_status}, no action taken.", show_alert=True)
        return

    wr[payment_id]["status"] = "approved"
    save_withdraw_requests(wr)

    try:
        await context.bot.send_message(
            uid,
            f"🎉 <b>WITHDRAWAL APPROVED!</b>\n\n"
            f"<blockquote>📝 METHOD: <code>{method}</code>\n"
            f"📞 NUMBER: <code>{payment_number}</code>\n"
            f"💰 AMOUNT: <code>{format_balance(amount)} BDT</code></blockquote>",
            parse_mode="HTML"
        )
    except:
        pass
    await query.message.edit_text(
        f"✅ APPROVED | User: {uid} | Amount: {format_balance(amount)} BDT",
        reply_markup=None
    )

async def admin_reject_withdraw(update, context, payment_id):
    query = update.callback_query
    await query.answer()
    wr = load_withdraw_requests()
    if payment_id not in wr:
        await query.message.reply_text("⚠️ REQUEST NOT FOUND!")
        return
    rd = wr[payment_id]
    uid = rd["user_id"]
    amount = rd["amount"]

    current_status = rd.get("status")
    if current_status in ("approved", "rejected"):
        await query.answer(f"⚠️ Already {current_status}, no action taken.", show_alert=True)
        return

    wr[payment_id]["status"] = "rejected"
    save_withdraw_requests(wr)

    # Refund the deducted amount back to the user's balance
    new_balance = await update_db_balance(uid, amount)

    try:
        await context.bot.send_message(
            uid,
            f"❌ <b>WITHDRAWAL REQUEST REJECTED</b>\n\n"
            f"<blockquote>💰 AMOUNT REFUNDED: <code>{format_balance(amount)} BDT</code>\n"
            f"💵 NEW BALANCE: <code>{format_balance(new_balance)} BDT</code></blockquote>\n\n"
            f"Contact admin for more info.",
            parse_mode="HTML"
        )
    except:
        pass
    await query.message.edit_text(
        f"❌ REJECTED & REFUNDED | User: {uid} | Amount: {format_balance(amount)} BDT",
        reply_markup=None
    )

# ==================== ADMIN PANEL - BALANCE MANAGEMENT ====================

async def admin_add_balance_start(update, context):
    context.user_data["add_balance_mode"] = True
    context.user_data["remove_balance_mode"] = False
    await update.message.reply_text("💰 SEND USER ID TO ADD BALANCE:")

async def admin_remove_balance_start(update, context):
    context.user_data["remove_balance_mode"] = True
    context.user_data["add_balance_mode"] = False
    await update.message.reply_text("💸 SEND USER ID TO REMOVE BALANCE:")

async def process_add_balance_user(update, context):
    uid_to_add = update.message.text.strip()
    if not uid_to_add.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_add_int = int(uid_to_add)
    if not user_exists(uid_to_add_int):
        await update.message.reply_text("❌ USER NOT FOUND!")
        context.user_data["add_balance_mode"] = False
        return
    context.user_data["pending_add_user"] = uid_to_add_int
    await update.message.reply_text("💵 SEND AMOUNT TO ADD:")

async def process_remove_balance_user(update, context):
    uid_to_remove = update.message.text.strip()
    if not uid_to_remove.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_remove_int = int(uid_to_remove)
    if not user_exists(uid_to_remove_int):
        await update.message.reply_text("❌ USER NOT FOUND!")
        context.user_data["remove_balance_mode"] = False
        return
    context.user_data["pending_remove_user"] = uid_to_remove_int
    await update.message.reply_text("💸 SEND AMOUNT TO REMOVE:")

async def process_add_balance_amount(update, context):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0: raise ValueError
    except:
        await update.message.reply_text("❌ INVALID AMOUNT!")
        return
    uid = context.user_data.get("pending_add_user")
    if not uid:
        context.user_data["add_balance_mode"] = False
        await update.message.reply_text("⚠️ SESSION EXPIRED.")
        return
    old_balance = get_user(uid).get("balance", 0)
    new_balance = await update_db_balance(uid, amount)
    await update.message.reply_text(
        f"✅ **ADD BALANCE SUCCESSFUL**\n🆔 USER: `{uid}`\n"
        f"💰 ADDED: `{format_balance(amount)} BDT`\n"
        f"📈 NEW BALANCE: `{format_balance(new_balance)} BDT`",
        parse_mode="Markdown"
    )
    try:
        await context.bot.send_message(uid, f"🎉 ADMIN ADDED `{format_balance(amount)} BDT` TO YOUR ACCOUNT!\n💵 NEW BALANCE: `{format_balance(new_balance)} BDT`", parse_mode="Markdown")
    except:
        pass
    context.user_data["add_balance_mode"] = False
    context.user_data["pending_add_user"] = None

async def process_remove_balance_amount(update, context):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0: raise ValueError
    except:
        await update.message.reply_text("❌ INVALID AMOUNT!")
        return
    uid = context.user_data.get("pending_remove_user")
    if not uid:
        context.user_data["remove_balance_mode"] = False
        await update.message.reply_text("⚠️ SESSION EXPIRED.")
        return
    old_balance = get_user(uid).get("balance", 0)
    if amount > old_balance:
        await update.message.reply_text(f"❌ INSUFFICIENT BALANCE! Current: {format_balance(old_balance)} BDT")
        context.user_data["remove_balance_mode"] = False
        context.user_data["pending_remove_user"] = None
        return
    new_balance = await update_db_balance(uid, -amount)
    await update.message.reply_text(
        f"✅ **REMOVE BALANCE SUCCESSFUL**\n🆔 USER: `{uid}`\n"
        f"💸 REMOVED: `{format_balance(amount)} BDT`\n"
        f"📉 NEW BALANCE: `{format_balance(new_balance)} BDT`",
        parse_mode="Markdown"
    )
    try:
        await context.bot.send_message(uid, f"⚠️ ADMIN REMOVED `{format_balance(amount)} BDT` FROM YOUR ACCOUNT!\n💵 NEW BALANCE: `{format_balance(new_balance)} BDT`", parse_mode="Markdown")
    except:
        pass
    context.user_data["remove_balance_mode"] = False
    context.user_data["pending_remove_user"] = None

# ==================== ADMIN PANEL - OTP RATE ====================

async def admin_otp_rate_start(update, context):
    context.user_data["otp_rate_mode"] = True
    current = get_otp_rate()
    await update.message.reply_text(
        f"💱 CURRENT OTP RATE: `{current:.2f} BDT`\n\n💵 SEND THE NEW RATE (e.g. 0.60):",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )

async def process_otp_rate_amount(update, context):
    context.user_data["otp_rate_mode"] = False
    try:
        new_rate = float(update.message.text.strip())
        if new_rate <= 0:
            raise ValueError
    except (TypeError, ValueError):
        await update.message.reply_text("❌ INVALID RATE! SEND A POSITIVE NUMBER, e.g. 0.60", reply_markup=system_config_keyboard())
        return
    set_otp_rate(new_rate)
    await update.message.reply_text(
        f"✅ **OTP RATE UPDATED**\n💱 NEW RATE: `{new_rate:.2f} BDT` PER OTP",
        parse_mode="Markdown",
        reply_markup=system_config_keyboard()
    )

# ==================== ADMIN PANEL - BAN/UNBAN ====================

async def admin_ban_user_start(update, context):
    context.user_data["admin_ban_mode"] = True
    context.user_data["admin_unban_mode"] = False
    await update.message.reply_text("🚫 SEND TELEGRAM ID TO BAN USER:")

async def admin_unban_user_start(update, context):
    context.user_data["admin_unban_mode"] = True
    context.user_data["admin_ban_mode"] = False
    await update.message.reply_text("🔓 SEND TELEGRAM ID TO UNBAN USER:")

async def process_ban_user(update, context):
    uid_to_ban = update.message.text.strip()
    if not uid_to_ban.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_ban_int = int(uid_to_ban)
    if not user_exists(uid_to_ban_int):
        await update.message.reply_text("❌ USER NOT FOUND!")
        context.user_data["admin_ban_mode"] = False
        return
    if is_user_banned(uid_to_ban_int):
        await update.message.reply_text("⚠️ USER IS ALREADY BANNED!")
        context.user_data["admin_ban_mode"] = False
        return
    ban_user(uid_to_ban_int)
    try:
        await context.bot.send_message(uid_to_ban_int, "🚫 **YOU HAVE BEEN BANNED**\n📞 Contact support.", parse_mode="Markdown")
    except:
        pass
    await update.message.reply_text(f"✅ USER `{uid_to_ban}` BANNED!", parse_mode="Markdown", reply_markup=system_config_keyboard())
    context.user_data["admin_ban_mode"] = False

async def process_unban_user(update, context):
    uid_to_unban = update.message.text.strip()
    if not uid_to_unban.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_unban_int = int(uid_to_unban)
    if not is_user_banned(uid_to_unban_int):
        await update.message.reply_text("⚠️ THIS USER IS NOT BANNED!")
        context.user_data["admin_unban_mode"] = False
        return
    unban_user(uid_to_unban_int)
    try:
        await context.bot.send_message(uid_to_unban_int, "✅ **YOU HAVE BEEN UNBANNED!** Use /start", parse_mode="Markdown")
    except:
        pass
    await update.message.reply_text(f"✅ USER `{uid_to_unban}` UNBANNED!", parse_mode="Markdown", reply_markup=system_config_keyboard())
    context.user_data["admin_unban_mode"] = False

async def show_banned_users_list(update, context):
    banned_list = load_banned_users()
    if not banned_list:
        await update.message.reply_text("📜 NO BANNED USERS.", reply_markup=system_config_keyboard())
        return
    text = "📜 **BANNED USER LIST**\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, uid in enumerate(banned_list, 1):
        text += f"{i}. `{uid}`\n"
    text += f"\n📊 Total: {len(banned_list)}"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=system_config_keyboard())

# ==================== ADMIN PANEL - SERVICE ON/OFF MANAGEMENT ====================

def _build_manage_services_rows(services):
    disabled = get_disabled_services()
    buttons = []
    for i, svc in enumerate(services):
        sid = svc.get("sid", f"Service {i+1}")
        is_off = sid in disabled
        status = "❌" if is_off else "✅"
        buttons.append(InlineKeyboardButton(
            f"{status} {sid}",
            callback_data=f"togsvc_{i}",
            style=("danger" if is_off else "success")
        ))
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    cur = get_service_design()
    design_row = [
        InlineKeyboardButton(("✅ " if n == cur else "") + f"DESIGN V{n}",
                             callback_data=f"svcdesign_{n}",
                             style=("success" if n == cur else "primary"))
        for n in SERVICE_DESIGN_NAMES
    ]
    rows.insert(0, design_row)
    rows.append([InlineKeyboardButton("🔙 CLOSE", callback_data="close_admin_menu", style="danger")])
    return rows

async def show_manage_services_menu(update, context):
    services = get_cached_services()
    if not services:
        await _do_liveaccess_fetch()
        services = get_cached_services()
    if not services:
        await update.message.reply_text(
            "⚠️ No services are loaded yet. Please try again in a moment.",
            reply_markup=system_config_keyboard()
        )
        return
    context.user_data["admin_svc_list"] = services
    rows = _build_manage_services_rows(services)
    await update.message.reply_text(
        "📡 <b>MANAGE SERVICES</b>\n\n"
        "<blockquote>✅ = shown to users | ❌ = hidden from users\n"
        "Tap a service to enable/disable it in GET NUMBER.\n\n"
        "🎨 DESIGN V1 = Classic | V2 = Icons | V3 = Bars\n"
        "Tap a design to change how GET NUMBER looks.</blockquote>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows)
    )

# ==================== ADMIN PANEL - PAYMENT SETUP ====================

def _build_payment_management_rows():
    flags = get_payment_flags()
    buttons = []
    for key, label in PAYMENT_METHOD_LABELS.items():
        enabled = flags.get(key, True)
        status = "✅" if enabled else "❌"
        buttons.append(InlineKeyboardButton(
            f"{status} {label}",
            callback_data=f"togpay_{key}",
            style=("success" if enabled else "danger")
        ))
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("📉 MINIMUM WITHDRAW LIMITS", callback_data="minwd_menu", style="primary")])
    rows.append([InlineKeyboardButton("🔙 CLOSE", callback_data="close_admin_menu", style="danger")])
    return rows

def _build_min_withdraw_menu_rows():
    amounts = get_min_withdraw_map()
    buttons = [
        InlineKeyboardButton(f"{PAYMENT_METHOD_LABELS[key]}: {amounts[key]:.0f} BDT", callback_data=f"selminwd_{key}", style="primary")
        for key in PAYMENT_METHOD_LABELS
    ]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("🔙 BACK", callback_data="minwd_back", style="danger")])
    return rows

async def show_payment_management_menu(update, context):
    rows = _build_payment_management_rows()
    await update.message.reply_text(
        "💳 <b>PAYMENT SETUP</b>\n\n"
        "<blockquote>✅ = shown to users | ❌ = hidden from withdraw list\n"
        "Tap a payment method to turn it on/off, or tap MINIMUM WITHDRAW LIMITS to set each method's own minimum.</blockquote>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def admin_min_withdraw_start(update, context, key):
    context.user_data["min_withdraw_mode"] = True
    context.user_data["min_withdraw_target"] = key
    current = get_min_withdraw(key)
    await update.effective_message.reply_text(
        f"📉 {PAYMENT_METHOD_LABELS[key]} — CURRENT MINIMUM WITHDRAW: `{current:.0f} BDT`\n\n💵 SEND THE NEW MINIMUM (e.g. 50):",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )

async def process_min_withdraw_amount(update, context):
    context.user_data["min_withdraw_mode"] = False
    key = context.user_data.get("min_withdraw_target")
    context.user_data["min_withdraw_target"] = None
    if key not in PAYMENT_METHOD_LABELS:
        await update.message.reply_text("⚠️ Session expired — please reopen MINIMUM WITHDRAW LIMITS.", reply_markup=admin_main_keyboard())
        return
    try:
        new_amount = float(update.message.text.strip())
        if new_amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        await update.message.reply_text("❌ INVALID AMOUNT! SEND A POSITIVE NUMBER, e.g. 50", reply_markup=admin_main_keyboard())
        return
    set_min_withdraw(key, new_amount)
    await update.message.reply_text(
        f"✅ **MINIMUM WITHDRAW UPDATED**\n{PAYMENT_METHOD_LABELS[key]} — NEW MINIMUM: `{new_amount:.0f} BDT`",
        parse_mode="Markdown",
        reply_markup=admin_main_keyboard()
    )

# ==================== ADMIN PANEL - MAIN MENU BUTTON MANAGEMENT ====================

def _build_manage_buttons_rows():
    flags = get_button_flags()
    buttons = []
    for key, label in BUTTON_FLAG_LABELS.items():
        enabled = flags.get(key, True)
        status = "✅" if enabled else "❌"
        buttons.append(InlineKeyboardButton(
            f"{status} {label}",
            callback_data=f"togbtn_{key}",
            style=("success" if enabled else "danger")
        ))
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("🔙 CLOSE", callback_data="close_admin_menu", style="danger")])
    return rows

async def show_manage_buttons_menu(update, context):
    rows = _build_manage_buttons_rows()
    await update.message.reply_text(
        "🔘 <b>MANAGE BUTTONS</b>\n\n"
        "<blockquote>✅ = visible in main menu | ❌ = hidden from main menu\n"
        "Tap a button to show/hide it for users.</blockquote>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows)
    )

# ==================== ADMIN PANEL - NUMBER MANAGE ====================

def _build_number_manage_rows():
    on = is_old_number_delete_on()
    v2 = is_number_template_v2_on()
    return [
        [InlineKeyboardButton(
            f"{'✅' if on else '❌'} OLD NUMBER DELETE: {'ON' if on else 'OFF'}",
            callback_data="togoldnum",
            style=("success" if on else "danger")
        )],
        [InlineKeyboardButton(
            f"{'✅' if v2 else '❌'} NUMBER TEMPLATE V2: {'ON' if v2 else 'OFF'}",
            callback_data="togtplv2",
            style=("success" if v2 else "danger")
        )],
        [InlineKeyboardButton("🔙 CLOSE", callback_data="close_admin_menu", style="danger")]
    ]

async def show_number_manage_menu(update, context):
    await update.message.reply_text(
        "🔢 <b>NUMBER MANAGE</b>\n\n"
        "<blockquote>❌ OFF (default) = old number stays above when a user gets a NEW NUMBER\n"
        "✅ ON = old number message is deleted automatically when a user gets a NEW NUMBER</blockquote>\n\n"
        "<blockquote>🧾 <b>NUMBER TEMPLATE V2</b>\n"
        "❌ OFF (default) = normal message (country, range, number, status)\n"
        "✅ ON = flag + NEW NUMBER header, platform button, number as a one-tap copy button, CHANGE COUNTRY, NEW NUMBER / OTP GROUP buttons, and a neat OTP RECEIVED message</blockquote>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(_build_number_manage_rows())
    )

# ==================== ADMIN PANEL - REFER CONTROL ====================

def _build_refer_control_rows():
    on = is_ref_commission_on()
    return [
        [InlineKeyboardButton(f"🎁 REFER BONUS: {get_referral_bonus():.2f} BDT ✏️", callback_data="refctl_bonus", style="primary")],
        [InlineKeyboardButton(f"{'✅' if on else '❌'} OTP COMMISSION: {'ON' if on else 'OFF'}", callback_data="refctl_tog", style=("success" if on else "danger"))],
        [InlineKeyboardButton(f"💰 COMMISSION PER OTP: {get_ref_commission():.2f} BDT ✏️", callback_data="refctl_comm", style="primary")],
        [InlineKeyboardButton("🔙 CLOSE", callback_data="close_admin_menu", style="danger")]
    ]

def _refer_control_text():
    return (
        "🎁 <b>REFER CONTROL</b>\n\n"
        f"<blockquote>🎁 <b>REFER BONUS</b>\nA new user joins with someone's link → that person gets {get_referral_bonus():.2f} BDT.</blockquote>\n\n"
        f"<blockquote>💸 <b>OTP COMMISSION</b> (OFF by default)\nEvery successful OTP of a referred user pays the referrer {get_ref_commission():.2f} BDT extra (paid by the bot, not taken from the user).</blockquote>"
    )

async def show_refer_control_menu(update, context):
    await update.message.reply_text(
        _refer_control_text(), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(_build_refer_control_rows())
    )

_REF_INPUT = {
    "bonus": ("referral_bonus", "REFER BONUS"),
    "comm": ("ref_commission", "COMMISSION PER OTP"),
}

async def process_ref_input(update, context):
    key = context.user_data.get("ref_input")
    context.user_data["ref_input"] = None
    setting, label = _REF_INPUT[key]
    try:
        value = float(update.message.text.strip())
        if value < 0:
            raise ValueError
    except (TypeError, ValueError):
        await update.message.reply_text("❌ INVALID AMOUNT! SEND A NUMBER, e.g. 0.50", reply_markup=system_config_keyboard())
        return
    set_ref_setting(setting, value)
    await update.message.reply_text(f"✅ {label} UPDATED: {value:.2f} BDT", reply_markup=system_config_keyboard())
    await show_refer_control_menu(update, context)

# ==================== MESSAGE HANDLER SECTION ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    uid = update.effective_user.id
    await remember_user_name(update.effective_user)
    text = (update.message.text or "").strip()

    # FIX: escape hatch for "BACK TO ADMIN" / "BACK TO MAIN" — must be checked
    # BEFORE any admin mode flags below, otherwise the button text itself gets
    # swallowed as invalid input (e.g. "invalid user id") and the mode flag
    # never gets cleared, permanently locking the admin out of that section.
    if text in ("🔙 BACK TO ADMIN", "🔙 BACK TO MAIN") and is_admin(uid):
        context.user_data["admin_ban_mode"] = False
        context.user_data["admin_unban_mode"] = False
        context.user_data["add_balance_mode"] = False
        context.user_data["remove_balance_mode"] = False
        context.user_data["pending_add_user"] = None
        context.user_data["pending_remove_user"] = None
        context.user_data["otp_rate_mode"] = False
        context.user_data["ref_input"] = None
        context.user_data["min_withdraw_mode"] = False
        context.user_data["min_withdraw_target"] = None
        context.user_data["mode"] = None
        context.user_data["broadcast_mode"] = False

        if text == "🔙 BACK TO ADMIN":
            context.user_data["user_management_mode"] = None
            context.user_data["system_config_mode"] = None
            context.user_data["admin_mode"] = "main"
            await update.message.reply_text("🔙 Back to admin panel.", reply_markup=admin_main_keyboard())
        else:
            context.user_data["admin_mode"] = None
            await update.message.reply_text("🔙 Back to main menu.", reply_markup=main_keyboard(uid))
        return

    # Withdraw flow
    if context.user_data.get("withdraw_mode") == "select_method":
        await withdraw_method_selected(update, context)
        return
    if context.user_data.get("withdraw_mode") == "amount":
        await withdraw_amount_received(update, context)
        return
    if context.user_data.get("withdraw_mode") == "number":
        await withdraw_number_received(update, context)
        return

    # Admin balance
    if context.user_data.get("add_balance_mode") and is_admin(uid):
        if context.user_data.get("pending_add_user"):
            await process_add_balance_amount(update, context)
        else:
            await process_add_balance_user(update, context)
        return
    if context.user_data.get("remove_balance_mode") and is_admin(uid):
        if context.user_data.get("pending_remove_user"):
            await process_remove_balance_amount(update, context)
        else:
            await process_remove_balance_user(update, context)
        return
    if context.user_data.get("ref_input") and is_admin(uid):
        await process_ref_input(update, context)
        return
    if context.user_data.get("otp_rate_mode") and is_admin(uid):
        await process_otp_rate_amount(update, context)
        return
    if context.user_data.get("min_withdraw_mode") and is_admin(uid):
        await process_min_withdraw_amount(update, context)
        return

    # Admin ban/unban
    if context.user_data.get("admin_ban_mode") and is_admin(uid):
        await process_ban_user(update, context)
        return
    if context.user_data.get("admin_unban_mode") and is_admin(uid):
        await process_unban_user(update, context)
        return

    # CUSTOM RANGE — user sent a range text
    if context.user_data.get("mode") == "custom_range":
        context.user_data["mode"] = None
        range_text = text.strip().upper()
        if not re.search(r'\d', range_text):
            await update.message.reply_text(
                "❌ <b>INVALID RANGE!</b>\n\n"
                "<blockquote>Correct example: <code>234XXX</code></blockquote>",
                parse_mode="HTML",
                reply_markup=main_keyboard(uid)
            )
            return
        await request_queue.put({
            'type': 'process_numbers',
            'update': update,
            'context': context,
            'range_text': range_text,
            'count': 1
        })
        return

    # Ban check
    if not is_admin(uid) and is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return

    # Cancel
    if text == "❌ CANCEL":
        context.user_data.clear()
        await update.message.reply_text("❌ CANCELLED", reply_markup=main_keyboard(uid))
        return

    # Main menu buttons
    if is_menu_btn(text, "btn_profile") and is_button_enabled("btn_profile"):
        user_data = get_user(uid)
        stats = get_user_stats(uid)
        user = update.effective_user
        full_name = html.escape(user.full_name)
        username = html.escape(user.username or tr(uid, "no_username"))
        profile_text = (
            f"{tr(uid, 'profile_title')}\n\n"
            f"<blockquote>🏷️ {tr(uid, 'profile_name')}: <b>{full_name}</b></blockquote>\n"
            f"<blockquote>🆔 {tr(uid, 'profile_username')}: @{username}</blockquote>\n"
            f"<blockquote>🗝️ {tr(uid, 'profile_id')}: <code>{uid}</code></blockquote>\n\n"
            f"<blockquote>💵 {tr(uid, 'profile_balance')}: <b>{format_balance(user_data.get('balance', 0))} BDT</b></blockquote>\n\n"
            f"✨ <b>{tr(uid, 'profile_today')}</b>\n"
            f"<blockquote>📱 {tr(uid, 'profile_numbers')}: {stats['today_numbers']}\n🔑 {tr(uid, 'profile_otps')}: {stats['today_otps']}</blockquote>\n\n"
            f"🔥 <b>{tr(uid, 'profile_7d')}</b>\n"
            f"<blockquote>📱 {tr(uid, 'profile_numbers')}: {stats['last7d_numbers']}\n🔑 {tr(uid, 'profile_otps')}: {stats['last7d_otps']}</blockquote>\n\n"
            f"🌐 <b>{tr(uid, 'profile_all')}</b>\n"
            f"<blockquote>📱 {tr(uid, 'profile_numbers')}: {stats['total_numbers']}\n🔑 {tr(uid, 'profile_otps')}: {stats['total_otps']}</blockquote>"
        )
        await update.message.reply_text(
            profile_text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tr(uid, "btn_language"), callback_data="lang_menu", style="primary")
            ]])
        )
        return

    if is_menu_btn(text, "btn_balance"):
        balance = get_user(uid)['balance']
        await update.message.reply_text(
            f"{tr(uid, 'balance_title')}\n\n"
            f"<blockquote>💵 {tr(uid, 'balance_total')}: <b>{format_balance(balance)} BDT</b></blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tr(uid, "btn_withdraw"), callback_data="withdraw_start", style="primary")
            ]])
        )
        return

    if is_menu_btn(text, "btn_refer"):
        await refer_command(update, context)
        return

    # SEARCH OTP
    if is_menu_btn(text, "btn_search_otp") and is_button_enabled("btn_search_otp"):
        context.user_data["mode"] = "search_otp"
        await update.message.reply_text(tr(uid, "search_otp_prompt"), parse_mode="Markdown")
        return

    if context.user_data.get("mode") == "search_otp":
        context.user_data["mode"] = None
        await request_queue.put({'type': 'search_otp', 'update': update, 'context': context, 'target_num': normalize_number(text)})
        return

    # GET 2FA
    if is_menu_btn(text, "btn_2fa") and is_button_enabled("btn_2fa"):
        await get_2fa_code(update, context)
        return

    # GET NUMBER
    if is_menu_btn(text, "btn_get_number"):
        await show_app_selection(update, context)
        return

    if context.user_data.get("mode") == "get_2fa":
        await process_2fa_key(update, context)
        return

    # LEADERBOARD
    if is_menu_btn(text, "btn_leaderboard") and is_button_enabled("btn_leaderboard"):
        await leaderboard_command(update, context)
        return

    # TRAFFIC
    if is_menu_btn(text, "btn_traffic") and is_button_enabled("btn_traffic"):
        await traffic_command(update, context)
        return

    # SUPPORT BUTTON HANDLER
    if is_menu_btn(text, "btn_support") and is_button_enabled("btn_support"):
        support_text = tr(uid, "support_text")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(tr(uid, "btn_support_inline"), url=SUPPORT_LINK, style="primary")],
            [InlineKeyboardButton(tr(uid, "btn_developer"), url=DEVELOPER_LINK, style="danger")],
            [InlineKeyboardButton(tr(uid, "btn_active_range"), url=RANGE_GROUP_LINK, style="success")]
        ])
        await update.message.reply_text(support_text, reply_markup=keyboard, parse_mode="Markdown")
        return

    # Admin panel
    if is_menu_btn(text, "btn_admin_panel") and is_admin(uid):
        context.user_data["admin_mode"] = "main"
        await update.message.reply_text(
            "⌬━━━━━━━━━━━━━━━━━━━━⌬\n   WELCOME ADMIN PANEL\n⌬━━━━━━━━━━━━━━━━━━━━⌬",
            reply_markup=admin_main_keyboard()
        )
        return

    if text == "🔙 BACK TO MAIN" and context.user_data.get("admin_mode"):
        context.user_data["admin_mode"] = None
        await update.message.reply_text("🔙 Back to main menu.", reply_markup=main_keyboard(uid))
        return

    if text == "🔙 BACK TO ADMIN":
        context.user_data["user_management_mode"] = None
        context.user_data["system_config_mode"] = None
        context.user_data["admin_mode"] = "main"
        await update.message.reply_text("🔙 Back to admin panel.", reply_markup=admin_main_keyboard())
        return

    if text == "👥 USER MANAGEMENT" and context.user_data.get("admin_mode") == "main" and is_admin(uid):
        context.user_data["user_management_mode"] = "main"
        await update.message.reply_text("👥 User Management:", reply_markup=user_management_keyboard())
        return

    if text == "⚙️ SYSTEM CONFIGURATION" and context.user_data.get("admin_mode") == "main" and is_admin(uid):
        context.user_data["system_config_mode"] = "main"
        await update.message.reply_text("⚙️ System Configuration:", reply_markup=system_config_keyboard())
        return

    if text == "💳 PAYMENT SETUP" and context.user_data.get("admin_mode") == "main" and is_admin(uid):
        await show_payment_management_menu(update, context)
        return

    if text == "📈 TODAY ALL STATUS" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        t_n, t_o, s_n, s_o, tot_n, tot_o = get_global_system_stats()
        msg = (
            f"📊 <b>SYSTEM STATUS</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ <b>TODAY</b>\n📱 NUMBERS: {t_n}\n🔑 OTPS: {t_o}\n\n"
            f"🔥 <b>LAST 7 DAYS</b>\n📱 NUMBERS: {s_n}\n🔑 OTPS: {s_o}\n\n"
            f"🌐 <b>ALL TIME</b>\n📱 NUMBERS: {tot_n}\n🔑 OTPS: {tot_o}"
        )
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    if text == "👤 USER STATUS CHECK" and is_admin(uid):
        context.user_data["mode"] = "input_user_id"
        await update.message.reply_text("🔍 ENTER TELEGRAM ID:", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("mode") == "input_user_id" and is_admin(uid):
        target_uid = text.strip()
        if not target_uid.isdigit():
            await update.message.reply_text("❌ INVALID ID!")
            return
        context.user_data["mode"] = None
        stats = get_user_stats(target_uid)
        msg = (
            f"👤 <b>USER STATUS</b> — <code>{target_uid}</code>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ TODAY: 📱 {stats['today_numbers']} | 🔑 {stats['today_otps']}\n"
            f"🔥 7 DAYS: 📱 {stats['last7d_numbers']} | 🔑 {stats['last7d_otps']}\n"
            f"🌐 ALL TIME: 📱 {stats['total_numbers']} | 🔑 {stats['total_otps']}"
        )
        await update.message.reply_text(
            msg, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📂 CHECK ALL DATA", callback_data=f"full_logs_{target_uid}", style="primary")
            ]])
        )
        return

    if text == "🆔 ALL USER ID" and context.user_data.get("user_management_mode") == "main" and is_admin(uid):
        users = get_all_users()
        if users:
            content = "\n".join(f"{i}. {u}" for i, u in enumerate(users, 1))
            f = io.BytesIO(content.encode()); f.name = f"ALL_USERS_{len(users)}.txt"
            await update.message.reply_document(document=f, caption=f"👥 Total Users: {len(users)}", reply_markup=user_management_keyboard())
        else:
            await update.message.reply_text("No users found.", reply_markup=user_management_keyboard())
        return

    if text == "💰 ALL USER BALANCE" and context.user_data.get("user_management_mode") == "main" and is_admin(uid):
        user_db = load_data(USER_DATA_FILE)
        if user_db:
            total_bal = sum(v.get("balance", 0) for v in user_db.values())
            lines = [f"{i}. {uid_}: {v.get('balance', 0):.2f} BDT" for i, (uid_, v) in enumerate(user_db.items(), 1)]
            content = f"💰 TOTAL BALANCE: {total_bal:.2f} BDT\n\n" + "\n".join(lines)
            f = io.BytesIO(content.encode()); f.name = f"BALANCES_{total_bal:.0f}.txt"
            await update.message.reply_document(document=f, caption=f"💵 Total Balance: {total_bal:.2f} BDT", reply_markup=user_management_keyboard())
        else:
            await update.message.reply_text("No data.", reply_markup=user_management_keyboard())
        return

    if text == "📜 BAN USER LIST" and is_admin(uid):
        await show_banned_users_list(update, context)
        return

    if text == "⛔ BAN USER" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await admin_ban_user_start(update, context)
        return

    if text == "🔓 UNBAN USER" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await admin_unban_user_start(update, context)
        return

    if text == "➕ ADD BALANCE" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await admin_add_balance_start(update, context)
        return

    if text == "➖ REMOVE BALANCE" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await admin_remove_balance_start(update, context)
        return

    if text == "💱 OTP RATE" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await admin_otp_rate_start(update, context)
        return

    if text == "📡 MANAGE SERVICES" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await show_manage_services_menu(update, context)
        return

    if text == "🔘 MANAGE BUTTONS" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await show_manage_buttons_menu(update, context)
        return

    if text == "🎁 REFER CONTROL" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await show_refer_control_menu(update, context)
        return

    if text == "🔢 NUMBER MANAGE" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await show_number_manage_menu(update, context)
        return

    # ==================== FIXED BROADCAST (TEXT, PHOTO, VIDEO, FILE, ETC.) ====================
    if text == "📢 BROADCAST" and is_admin(uid):
        context.user_data["broadcast_mode"] = True
        await update.message.reply_text(
            "📢 <b>ADMIN BROADCAST SYSTEM (PRO)</b>\n\n"
            "💬 Whatever you send now (Text, Photo, Video, Document, Voice, Audio, Animation, Sticker) will go out to all users with a professional header.\n\n"
            "✨ If it contains a range (e.g. 237XXX), it will automatically become click-to-copy.", 
            parse_mode="HTML", 
            reply_markup=cancel_keyboard()
        )
        return

    if context.user_data.get("broadcast_mode") and is_admin(uid):
        context.user_data["broadcast_mode"] = False
        
        user_db = load_data(USER_DATA_FILE)
        all_uids = list(user_db.keys())
        
        if not all_uids:
            await update.message.reply_text("❌ No users found to send to!")
            return

        success_ids, fail_ids = [], []
        status_msg = await update.message.reply_text(f"🚀 <b>Broadcast started...</b>\n🎯 Target: {len(all_uids)} users.", parse_mode="HTML")

        def format_broadcast_caption(caption_text):
            if not caption_text:
                return "<blockquote>📢 <b>ADMIN NOTICE :</b></blockquote>"
            formatted = re.sub(r'(\d{3,}[xX]{3,})', r'<code>\1</code>', str(caption_text))
            return f"<blockquote>📢 <b>ADMIN NOTICE :</b></blockquote>\n\n{formatted}"

        for user_id_str in all_uids:
            try:
                target_id = int(user_id_str)
                
                # Text message
                if update.message.text:
                    await context.bot.send_message(
                        chat_id=target_id, 
                        text=format_broadcast_caption(update.message.text), 
                        parse_mode="HTML"
                    )
                # Photo
                elif update.message.photo:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_photo(
                        chat_id=target_id,
                        photo=update.message.photo[-1].file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # Video
                elif update.message.video:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_video(
                        chat_id=target_id,
                        video=update.message.video.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # Document (any file)
                elif update.message.document:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_document(
                        chat_id=target_id,
                        document=update.message.document.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # Audio
                elif update.message.audio:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_audio(
                        chat_id=target_id,
                        audio=update.message.audio.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # Voice
                elif update.message.voice:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_voice(
                        chat_id=target_id,
                        voice=update.message.voice.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # Animation (GIF)
                elif update.message.animation:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_animation(
                        chat_id=target_id,
                        animation=update.message.animation.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # Sticker
                elif update.message.sticker:
                    await context.bot.send_sticker(
                        chat_id=target_id,
                        sticker=update.message.sticker.file_id
                    )
                # Everything else (forward/copy)
                else:
                    try:
                        await context.bot.copy_message(
                            chat_id=target_id,
                            from_chat_id=update.message.chat_id,
                            message_id=update.message.message_id
                        )
                    except:
                        await context.bot.send_message(
                            chat_id=target_id,
                            text="📢 <b>ADMIN NOTICE :</b>\n\nYou have a new message, but it could not be displayed.",
                            parse_mode="HTML"
                        )
                success_ids.append(user_id_str)
            except Exception as e:
                print(f"Broadcast fail to {user_id_str}: {e}")
                fail_ids.append(user_id_str)
            
            await asyncio.sleep(0.05)

        report_text = (
            f"✅ <b>ADMIN NOTICE COMPLETE !</b>\n\n"
            f"📊 <b>BROADCAST REPORT:</b>\n\n"
            f"<blockquote>✅ SUCCESSFULLY SENT: {len(success_ids)} USERS !</blockquote>\n"
            f"<blockquote>❌ FAILED TO SEND: {len(fail_ids)} USERS !</blockquote>"
        )
        
        await status_msg.delete()
        await context.bot.send_message(chat_id=uid, text=report_text, parse_mode="HTML", reply_markup=main_keyboard(uid))

        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if success_ids:
            s_file = io.BytesIO(("\n".join(success_ids)).encode()); s_file.name = f"SUCCESS_{random_suffix}.txt"
            await context.bot.send_document(chat_id=uid, document=s_file, caption="✅ Success User List")
        if fail_ids:
            f_file = io.BytesIO(("\n".join(fail_ids)).encode()); f_file.name = f"FAILED_{random_suffix}.txt"
            await context.bot.send_document(chat_id=uid, document=f_file, caption="❌ Failed User List")
        
        return

    await update.message.reply_text(tr(uid, "menu_prompt"), parse_mode="Markdown", reply_markup=main_keyboard(uid))

# ==================== COMMAND HANDLERS SECTION ====================

async def get1number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return
    await show_app_selection(update, context)

async def searchotp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return
    context.user_data["mode"] = "search_otp"
    await update.message.reply_text("🔍 **ENTER THE NUMBER TO SEARCH OTP:**", parse_mode="Markdown")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return
    balance = get_user(uid)['balance']
    await update.message.reply_text(f"💰 BALANCE: `{format_balance(balance)} BDT`", parse_mode="Markdown", reply_markup=main_keyboard(uid))

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return
    user_data = get_user(uid)
    stats = get_user_stats(uid)
    user = update.effective_user
    username = user.username or tr(uid, "no_username")
    profile_text = (
        f"{tr(uid, 'profile_title')}\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷️ {tr(uid, 'profile_name')}: `{user.full_name}`\n"
        f"🆔 {tr(uid, 'profile_username')}: @{username}\n"
        f"🗝️ {tr(uid, 'profile_id')}: `{uid}`\n\n"
        f"💵 {tr(uid, 'profile_balance')}: {format_balance(user_data.get('balance', 0))} BDT\n\n"
        f"✨ {tr(uid, 'profile_today')}: 📱 {stats['today_numbers']} | 🔑 {stats['today_otps']}\n"
        f"🔥 {tr(uid, 'profile_7d')}: 📱 {stats['last7d_numbers']} | 🔑 {stats['last7d_otps']}\n"
        f"🌐 {tr(uid, 'profile_all')}: 📱 {stats['total_numbers']} | 🔑 {stats['total_otps']}"
    )
    await update.message.reply_text(
        profile_text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(tr(uid, "btn_language"), callback_data="lang_menu", style="primary")
        ]])
    )

async def refer_command_slash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return
    await refer_command(update, context)

async def leaderboard_command_slash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text(tr(uid, "banned"), reply_markup=main_keyboard(uid))
        return
    await leaderboard_command(update, context)

# ==================== START & CALLBACK SECTION ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    uid_str = str(uid)

    async with balance_lock:
        existing_data = load_data(USER_DATA_FILE)
        is_new_user = uid_str not in existing_data
        if is_new_user:
            existing_data[uid_str] = {"user_id": uid_str, "balance": 0.0, "total_numbers": 0, "referral_count": 0}
            save_data(existing_data)
    await remember_user_name(update.effective_user)

    args = context.args
    if args:
        param = args[0]
        if is_referral_request(param):
            print(f"[referral] user={uid} param={param} new_user={is_new_user} referrer_found={param in existing_data}")
        if is_range_request(param):
            await request_queue.put({'type': 'auto_number', 'update': update, 'context': context, 'range_text': param})
            return
        elif is_referral_request(param) and is_new_user:
            try:
                referrer_id = int(param)
                if referrer_id != uid and str(referrer_id) in existing_data:
                    current_count = get_referral_count(referrer_id)
                    new_count = current_count + 1
                    update_referral_count(referrer_id, new_count)
                    _rd = load_referral_data()
                    _rd.setdefault(str(referrer_id), {"referral_count": new_count}).setdefault("referred", []).append(
                        {"id": str(uid), "time": datetime.now().isoformat()})
                    save_referral_data(_rd)
                    bonus = get_referral_bonus()
                    await update_db_balance(referrer_id, bonus)
                    add_referral_earning(referrer_id, bonus)
                    async with balance_lock:
                        _ud = load_data(USER_DATA_FILE)
                        if uid_str in _ud:
                            _ud[uid_str]["referred_by"] = str(referrer_id)
                            save_data(_ud)
                    log_global_activity(referrer_id, "REFERRAL_JOINED", {"referred_user": uid})
                    try:
                        await context.bot.send_message(
                            referrer_id,
                            f"🎉 <b>NEW REFERRAL!</b>\n\n<blockquote>🗝️ ID: <code>{uid}</code>\n💰 REWARD: {format_balance(bonus)} BDT\n👥 TOTAL REFERS: {new_count}</blockquote>",
                            parse_mode="HTML"
                        )
                    except:
                        pass
            except Exception as e:
                print(f"Referral error: {e}")

    context.user_data.clear()
    await update.message.reply_text(tr(uid, "welcome"), parse_mode="Markdown")
    await update.message.reply_text(tr(uid, "menu_prompt"), parse_mode="Markdown", reply_markup=main_keyboard(uid))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    await query.answer()

    if not is_admin(uid) and is_user_banned(uid):
        await query.edit_message_text(tr(uid, "banned"))
        return

    # platform button on the V2 number message (display only)
    if data == "noop_svc":
        return

    # ==================== ADMIN — CLOSE AN INLINE MANAGEMENT MENU ====================
    if data == "close_admin_menu":
        try:
            await query.message.delete()
        except Exception:
            try:
                await query.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
        return

    # ==================== ADMIN — CHOOSE GET NUMBER DESIGN (MANAGE SERVICES) ====================
    if data.startswith("svcdesign_") and is_admin(uid):
        try:
            n = int(data.replace("svcdesign_", ""))
        except ValueError:
            n = 0
        if n not in SERVICE_DESIGN_NAMES:
            await query.answer("⚠️ Unknown design.", show_alert=True)
            return
        set_service_design(n)
        services = context.user_data.get("admin_svc_list") or get_cached_services() or []
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(_build_manage_services_rows(services)))
        except Exception:
            pass
        await query.answer(f"🎨 GET NUMBER design: {SERVICE_DESIGN_NAMES[n]}")
        return

    # ==================== ADMIN — TOGGLE A SERVICE ON/OFF (MANAGE SERVICES) ====================
    if data.startswith("togsvc_") and is_admin(uid):
        idx = int(data.replace("togsvc_", ""))
        services = context.user_data.get("admin_svc_list") or get_cached_services()
        if idx >= len(services):
            await query.answer("⚠️ Service list changed — please reopen MANAGE SERVICES.", show_alert=True)
            return
        sid = services[idx].get("sid", f"Service {idx+1}")
        currently_enabled = is_service_enabled(sid)
        set_service_enabled(sid, not currently_enabled)
        rows = _build_manage_services_rows(services)
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(rows))
        except Exception:
            pass
        await query.answer(f"{'✅ Enabled' if not currently_enabled else '❌ Disabled'}: {sid}")
        return

    # ==================== ADMIN — TOGGLE A MAIN-MENU BUTTON ON/OFF (MANAGE BUTTONS) ====================
    if data.startswith("togbtn_") and is_admin(uid):
        key = data.replace("togbtn_", "")
        if key not in BUTTON_FLAG_LABELS:
            await query.answer("⚠️ Unknown button.", show_alert=True)
            return
        current = is_button_enabled(key)
        set_button_enabled(key, not current)
        rows = _build_manage_buttons_rows()
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(rows))
        except Exception:
            pass
        await query.answer(f"{'✅ Enabled' if not current else '❌ Disabled'}: {BUTTON_FLAG_LABELS[key]}")
        return

    # ==================== ADMIN — OLD NUMBER DELETE ON/OFF (NUMBER MANAGE) ====================
    if data == "togoldnum" and is_admin(uid):
        now_on = not is_old_number_delete_on()
        set_old_number_delete(now_on)
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(_build_number_manage_rows()))
        except Exception:
            pass
        await query.answer(f"{'✅ ON' if now_on else '❌ OFF'}: OLD NUMBER DELETE")
        return

    # ==================== ADMIN — REFER CONTROL ====================
    if data == "refctl_tog" and is_admin(uid):
        now_on = not is_ref_commission_on()
        set_switch("ref_commission", now_on)
        try:
            await query.message.edit_text(_refer_control_text(), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(_build_refer_control_rows()))
        except Exception:
            pass
        await query.answer(f"{'✅ ON' if now_on else '❌ OFF'}: OTP COMMISSION")
        return
    if data in ("refctl_bonus", "refctl_comm") and is_admin(uid):
        key = data.replace("refctl_", "")
        context.user_data["ref_input"] = key
        setting, label = _REF_INPUT[key]
        cur = {"bonus": get_referral_bonus(), "comm": get_ref_commission()}[key]
        await context.bot.send_message(
            uid, f"✏️ CURRENT {label}: {cur:.2f} BDT\n\n💵 SEND THE NEW AMOUNT (e.g. 0.50):",
            reply_markup=cancel_keyboard()
        )
        return

    # ==================== ADMIN — NUMBER TEMPLATE V2 ON/OFF (NUMBER MANAGE) ====================
    if data == "togtplv2" and is_admin(uid):
        now_on = not is_number_template_v2_on()
        set_number_template_v2(now_on)
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(_build_number_manage_rows()))
        except Exception:
            pass
        await query.answer(f"{'✅ ON' if now_on else '❌ OFF'}: NUMBER TEMPLATE V2")
        return

    # ==================== ADMIN — TOGGLE A PAYMENT METHOD ON/OFF (PAYMENT SETUP) ====================
    if data.startswith("togpay_") and is_admin(uid):
        key = data.replace("togpay_", "")
        if key not in PAYMENT_METHOD_LABELS:
            await query.answer("⚠️ Unknown payment method.", show_alert=True)
            return
        current = is_payment_method_enabled(key)
        set_payment_method_enabled(key, not current)
        rows = _build_payment_management_rows()
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(rows))
        except Exception:
            pass
        await query.answer(f"{'✅ Enabled' if not current else '❌ Disabled'}: {PAYMENT_METHOD_LABELS[key]}")
        return

    # ==================== ADMIN — MINIMUM WITHDRAW LIMITS (PAYMENT SETUP) ====================
    if data == "minwd_menu" and is_admin(uid):
        rows = _build_min_withdraw_menu_rows()
        try:
            await query.message.edit_text(
                "📉 <b>MINIMUM WITHDRAW LIMITS</b>\n\n"
                "<blockquote>Tap a payment method, then send the new minimum amount for that method only.</blockquote>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(rows)
            )
        except Exception:
            pass
        return

    if data == "minwd_back" and is_admin(uid):
        rows = _build_payment_management_rows()
        try:
            await query.message.edit_text(
                "💳 <b>PAYMENT SETUP</b>\n\n"
                "<blockquote>✅ = shown to users | ❌ = hidden from withdraw list\n"
                "Tap a payment method to turn it on/off, or tap MINIMUM WITHDRAW LIMITS to set each method's own minimum.</blockquote>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(rows)
            )
        except Exception:
            pass
        return

    if data.startswith("selminwd_") and is_admin(uid):
        key = data.replace("selminwd_", "")
        if key not in PAYMENT_METHOD_LABELS:
            await query.answer("⚠️ Unknown payment method.", show_alert=True)
            return
        await admin_min_withdraw_start(update, context, key)
        return

    # ==================== LANGUAGE SELECTION (from PROFILE only) ====================
    if data == "lang_menu":
        await query.message.reply_text(
            tr(uid, "lang_select_prompt"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tr(uid, "btn_lang_en"), callback_data="set_lang_en", style="primary"),
                InlineKeyboardButton(tr(uid, "btn_lang_bn"), callback_data="set_lang_bn", style="success"),
            ]])
        )
        return

    if data in ("set_lang_en", "set_lang_bn"):
        new_lang = "en" if data == "set_lang_en" else "bn"
        await set_user_lang(uid, new_lang)
        await query.message.reply_text(tr(uid, "lang_changed"), parse_mode="HTML")
        # Refresh the bottom keyboard so its button labels switch language too
        await context.bot.send_message(uid, tr(uid, "menu_prompt"), parse_mode="Markdown", reply_markup=main_keyboard(uid))
        return

    # CHANGE COUNTRY (NUMBER TEMPLATE V2) — back to the country list of the selected service
    if data == "change_country":
        _ranges = context.user_data.get("la_ranges")
        _idx = context.user_data.get("la_svc_idx")
        _sid = context.user_data.get("la_sid", "")
        if _ranges and _idx is not None and _sid:
            await query.message.edit_text(
                f"📞 <b>GET NUMBER</b>\n\n"
                f"<blockquote>📱 Service: <b>{html.escape(_sid)}</b></blockquote>\n"
                f"<blockquote>🌍 Select your preferred <b>Country</b>:</blockquote>",
                parse_mode="HTML",
                reply_markup=_build_countries_keyboard(_ranges, _idx)
            )
            return
        data = "back_services"   # no service context (custom range / link) → service list

    # LIVEACCESS — SERVICE SELECTION
    if data.startswith("svc_"):
        idx = int(data.replace("svc_", ""))
        services = context.user_data.get("la_services", [])
        if not services:
            services = get_cached_services()
            context.user_data["la_services"] = services
        if idx >= len(services):
            await query.answer("Service not found. Please try again.", show_alert=True)
            return

        svc = services[idx]
        sid = svc.get("sid", "Service")
        ranges = svc.get("ranges", [])

        if not is_service_enabled(sid):
            await query.answer("This service is currently disabled.", show_alert=True)
            return

        if not ranges:
            await query.answer("No ranges available for this service right now.", show_alert=True)
            return

        context.user_data["la_svc_idx"] = idx
        context.user_data["la_sid"] = sid
        context.user_data["la_ranges"] = ranges

        keyboard = _build_countries_keyboard(ranges, idx)
        await query.message.edit_text(
            f"📞 <b>GET NUMBER</b>\n\n"
            f"<blockquote>📱 Service: <b>{html.escape(sid)}</b></blockquote>\n"
            f"<blockquote>🌍 Select your preferred <b>Country</b>:</blockquote>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    # LIVEACCESS — RANGE SELECTION
    if data.startswith("rng_"):
        idx = int(data.replace("rng_", ""))
        ranges = context.user_data.get("la_ranges", [])
        if idx >= len(ranges):
            await query.answer("Range not found. Please try again.", show_alert=True)
            return

        range_text = ranges[idx]
        sid = context.user_data.get("la_sid", "")

        asyncio.create_task(fast_allocate_number(query, context, range_text, sid))
        return

    # CUSTOM RANGE — user types range manually
    if data == "custom_range":
        context.user_data["mode"] = "custom_range"
        await query.message.edit_text(
            "⚙️ <b>CUSTOM RANGE</b>\n\n"
            "<blockquote>📶 Type your custom range.\n"
            "Example: <code>234XXX</code> or <code>225XXX</code></blockquote>\n\n"
            "<blockquote>⌨️ Type the range below and Send it:</blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ BACK", callback_data="back_services", style="danger")
            ]])
        )
        return

    # LIVEACCESS — BACK TO SERVICES
    if data == "back_services":
        services = get_cached_services() or context.user_data.get("la_services", [])
        disabled = get_disabled_services()
        services = [s for s in services if s.get("sid") not in disabled]
        if not services:
            await query.message.edit_text("❌ Could not load services. Please try again later.")
            return
        context.user_data["la_services"] = services
        keyboard = _build_services_keyboard(services)
        await query.message.edit_text(
            "📞 <b>GET NUMBER</b>\n\n"
            "<blockquote>📱 Select a <b>Service</b> from below:</blockquote>" + _legend_html(),
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    # SAME RANGE
    if data == "same_range":
        r_text = last_range.get(uid)
        if r_text:
            # old message: drop NEW NUMBER / CHANGE COUNTRY, keep copy + group buttons
            try:
                kept = []
                _old_rm = query.message.reply_markup
                for row in (_old_rm.inline_keyboard if _old_rm else []):
                    nrow = [b for b in row if b.callback_data not in ("same_range", "change_country")]
                    if nrow:
                        kept.append(nrow)
                if not kept:
                    raise ValueError("no buttons left")
                await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(kept))
            except Exception:
                try:
                    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📢 CHECK OTP GROUP", url=OTP_GROUP_LINK, style="primary")
                    ]]))
                except Exception:
                    pass
            ok = await process_numbers(update, context, r_text, 1)
            # OLD NUMBER DELETE (NUMBER MANAGE): remove the previous number message
            # only after the new number was delivered successfully.
            if ok and is_old_number_delete_on():
                try:
                    await query.message.delete()
                except Exception as e:
                    print(f"Old number delete error: {e}")
        return

    # WITHDRAW
    if data == "withdraw_start":
        balance = get_user(uid)['balance']
        min_withdraw = get_min_withdraw()
        if balance < min_withdraw:
            await query.message.reply_text(
                f"<blockquote>💵 BALANCE: {format_balance(balance)} BDT\n📉 MIN WITHDRAW: {min_withdraw:.0f} BDT</blockquote>",
                parse_mode="HTML"
            )
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

    if data.startswith("admin_approve_"):
        await admin_approve_withdraw(update, context, data.replace("admin_approve_", ""))
        return

    if data.startswith("admin_reject_"):
        await admin_reject_withdraw(update, context, data.replace("admin_reject_", ""))
        return

    # COPY / MISC CALLBACKS
    if data.startswith("copy_id_"):
        await query.answer(f"✅ Copied ID: {data.replace('copy_id_', '')}", show_alert=True)
        return

    if data.startswith("copy_text_"):
        await query.answer(f"✅ Copied: {data.replace('copy_text_', '')}", show_alert=True)
        return

    if data.startswith("my_ref_"):
        target_uid = data.replace("my_ref_", "")
        my_referrals = load_referral_data().get(str(target_uid), {}).get("referred", [])
        content = f"👥 REFERRAL REPORT — {target_uid}\n━━━━━━━━━━━━\nTOTAL: {get_referral_count(target_uid)}\n\n"
        for i, r_ in enumerate(my_referrals, 1):
            try:
                dt_obj = datetime.fromisoformat(r_['time'])
                content += f"{i}. ID: {r_['id']} | {dt_obj.strftime('%d/%m/%Y %I:%M %p')}\n"
            except Exception:
                continue
        f = io.BytesIO(content.encode())
        f.name = f"REF_{target_uid}.txt"
        await context.bot.send_document(chat_id=uid, document=f, caption="✅ **REFERRAL DATA**", parse_mode="Markdown")
        return

    if data.startswith("full_logs_"):
        target_uid = data.replace("full_logs_", "")
        stats = get_user_stats(target_uid)
        all_logs = load_data(ACTIVITY_LOGS_FILE)
        user_db = load_data(USER_DATA_FILE)
        user_info = user_db.get(str(target_uid), {})
        user_otps = [log for log in all_logs if str(log.get('uid')) == str(target_uid) and log.get('action') == "OTP_RECEIVED"]
        content = (
            f"📊 USER DATA REPORT — {target_uid}\n"
            f"💰 BALANCE: {user_info.get('balance', 0):.2f} BDT\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"TODAY NUMBERS: {stats['today_numbers']}\n"
            f"TODAY OTPS: {stats['today_otps']}\n"
            f"7D NUMBERS: {stats['last7d_numbers']}\n"
            f"7D OTPS: {stats['last7d_otps']}\n"
            f"TOTAL NUMBERS: {stats['total_numbers']}\n"
            f"TOTAL OTPS: {stats['total_otps']}\n"
            f"━━━━━━━━━━━━━━━━━━\n\nOTP LOGS:\n"
        )
        for i, log in enumerate(user_otps, 1):
            try:
                dt_obj = datetime.fromisoformat(log['timestamp'])
                d = log.get('details', {})
                content += f"{i}. {dt_obj.strftime('%d/%m/%Y %I:%M %p')}\n   📞 {d.get('number', 'N/A')}\n   🔑 {d.get('otp', 'N/A')}\n\n"
            except:
                continue
        f = io.BytesIO(content.encode())
        f.name = f"USER_{target_uid}.txt"
        await context.bot.send_document(
            chat_id=uid, document=f,
            caption=f"✅ <b>DATA FOR USER: <code>{target_uid}</code></b>",
            parse_mode="HTML"
        )
        return

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
    for _ in range(5):
        asyncio.create_task(worker())
    asyncio.create_task(monitor_loop(application))
    asyncio.create_task(liveaccess_refresh_loop())


def main():
    print("🤖 SMSBOT STARTING...")
    _start_keepalive_server()
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(16)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .get_updates_write_timeout(30.0)
        .get_updates_pool_timeout(30.0)
        .post_init(post_init)
        .build()
    )

    app.add_error_handler(error_handler)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get1number", get1number_command))
    app.add_handler(CommandHandler("searchotp", searchotp_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("refer", refer_command_slash))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command_slash))

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
    main()
