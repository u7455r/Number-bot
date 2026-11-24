import os
import re
import json
import html
import time
import uuid
import pickle
import shutil
import random
import hashlib
import threading
from threading import Thread
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus

import cloudscraper
import requests
import phonenumbers
from phonenumbers import geocoder
from phonenumbers.phonenumberutil import region_code_for_number, COUNTRY_CODE_TO_REGION_CODE
import pycountry
import urllib3
from bs4 import BeautifulSoup
from flask import Flask
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Render Keep-Alive Server (30s Timeout / Open Port Fix) ────────────────
app = Flask(__name__)

@app.route("/")
def index():
    return "OTP Bot is live on Render!", 200

@app.route("/health")
def health():
    return "OK", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

Thread(target=run_web_server, daemon=True).start()
# ─────────────────────────────────────────────────────────────────────────────

BOT_TOKEN = "8743808077:AAHyZkSyiwODeMIAkM7hqMBOwjPi3dLD55c"
MAIN_ADMIN_ID = 8298133943

def create_backup(source_files, backup_dir="backups"):
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup_dir = os.path.join(backup_dir, f"backup_{timestamp}")
    os.makedirs(current_backup_dir, exist_ok=True)

    for file in source_files:
        if file and os.path.exists(file):
            try:
                dest_path = os.path.join(current_backup_dir, os.path.basename(file))
                if os.path.isdir(file):
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    shutil.copytree(file, dest_path)
                else:
                    shutil.copy2(file, current_backup_dir)
            except Exception as e:
                print(f"Error backing up {file}: {e}")

    zip_name = f"{current_backup_dir}.zip"
    try:
        shutil.make_archive(current_backup_dir, "zip", current_backup_dir)
        shutil.rmtree(current_backup_dir)
        return zip_name
    except Exception as e:
        print(f"Error zipping backup: {e}")
        return current_backup_dir

class BackupManager:
    def create_backup(self):
        files_to_backup = []
        for var in [
            "SETTINGS_FILE",
            "SESSIONS_FILE",
            "USERS_FILE",
            "ADMINS_FILE",
            "GROUPS_FILE",
            "COUNTRIES_FILE",
            "CHANNELS_FILE",
        ]:
            val = globals().get(var)
            if val:
                files_to_backup.append(val)
        if os.path.exists("database"):
            files_to_backup.append("database")
        return create_backup(files_to_backup)

    def restore_backup(self, zip_path):
        return False

backup_manager = BackupManager()

def list_backups(backup_dir="backups"):
    if not os.path.exists(backup_dir):
        return []
    return sorted(
        [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))],
        reverse=True,
    )

SETTINGS_FILE = "ii287.json"
SESSIONS_FILE = "limogpt.json"
COUNTRIES_FILE = "countriesi.json"
CHANNELS_FILE = "channelsi.json"
USERS_FILE = "usersi.json"
ADMINS_FILE = "admins.ijson"
BANNED_FILE = "bannedi.json"
OTP_GROUP_FILE = "otp_groupi.json"
GROUPS_FILE = "groupsi.json"
STATISTICS_FILE = "statisticsi.json"
REFERRALS_FILE = "referralsi.json"
REFERRAL_SETTINGS_FILE = "referral_settings.json"
WITHDRAWAL_REQUESTS_FILE = "withdrawal_requests.json"
WITHDRAWAL_METHODS_FILE = "withdrawal_methods.json"
WELCOME_MESSAGES_FILE = "welcome_messages.json"
NUMBERS_ADMINS_FILE = "numbers_admins.json"
BUTTON_LINKS_FILE = "button_links.json"
OTP_BUTTONS_FILE = "otp_buttons.json"

COOKIES_FILE = "cookies.pkl"
COOKIES_FILE_SITE3 = "cookies_site3.pkl"
COOKIES_FILE_SITE4 = "cookies_site4.pkl"
COOKIES_FILE_SITE5 = "cookies_ivasms.json"
COOKIES_FILE_SITE6 = "cookies_msi.pkl"
COOKIES_FILE_SITE7 = "cookies_share.pkl"
COOKIES_FILE_SITE8 = "cookies_ims.pkl"
COOKIES_FILE_SITE9 = "cookies_roxy.pkl"
COOKIES_FILE_SITE10 = "cookies_timesms.pkl"

LAST_MESSAGE_FILE = "last_message.txt"
LAST_MESSAGE_FILE_SITE2 = "last_message_site2.txt"
LAST_MESSAGE_FILE_SITE3 = "last_message_site3.txt"
LAST_MESSAGE_FILE_SITE4 = "last_message_site4.txt"
LAST_MESSAGE_FILE_SITE5 = "last_message_ivasms.txt"
LAST_MESSAGE_FILE_SITE6 = "last_message_msi.txt"
LAST_MESSAGE_FILE_SITE7 = "last_message_share.txt"
LAST_MESSAGE_FILE_SITE8 = "last_message_ims.txt"
LAST_MESSAGE_FILE_SITE9 = "last_message_roxy.txt"
LAST_MESSAGE_FILE_SITE10 = "last_message_timesms.txt"

IDX_DATE_SITE2 = 0
IDX_NUMBER_SITE2 = 2
IDX_SMS_SITE2 = 5
IDX_DATE_SITE3 = 0
IDX_NUMBER_SITE3 = 2
IDX_SMS_SITE3 = 5

def load_env():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env()

DEFAULT_SETTINGS = {
    "GROUP": {
        "name": "GROUP",
        "accounts": [{"id": str(uuid.uuid4()), "username": "Yousseffh123", "password": "Yousseffh123"}],
        "base_url": "http://139.99.63.204",
        "login_page_url": "http://139.99.63.204/ints/login",
        "login_post_url": "http://139.99.63.204/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True,
    },
    "Fly sms": {
        "name": "Fly sms",
        "accounts": [{"id": str(uuid.uuid4()), "username": "ud08", "password": "aud$$"}],
        "base_url": "http://193.70.33.154",
        "login_page_url": "http://193.70.33.154/ints/login",
        "login_post_url": "http://193.70.33.154/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 1,
        "timeout": 60,
        "enabled": True,
    },
    "Number_Panel": {
        "name": "Number Panel",
        "accounts": [
            {
                "id": "SFBTR0ZBUzRWkE9Xd2GRVIeViIVBk3BpXnCTiElodkFhVWFYdYOLZA==",
                "api_token": "SFBTR0ZBUzRWkE9Xd2GRVIeViIVBk3BpXnCTiElodkFhVWFYdYOLZA==",
            }
        ],
        "base_url": "http://147.135.212.197/crapi/st/viewstats",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True,
    },
    "Bolt": {
        "name": "Bolt",
        "accounts": [{"id": str(uuid.uuid4()), "username": "abuar113", "password": "abuun_Z113"}],
        "base_url": "http://93.190.143.35/ints",
        "login_page_url": "http://93.190.143.35/ints/Login",
        "login_post_url": "http://93.190.143.35/ints/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True,
    },
    "iVASMS": {
        "name": "iVAS SMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "micahc7@gmail.com",
                "password": "12011",
                "api_key": "sk_4b5ff02b42635e4c4891bd5d2f8fcb7aff2f7af6d5daecf8498ba91092dfcbb6",
            }
        ],
        "api_url": "https://maroon-wombat-183778.hostingersite.com/apiivasms/api.php",
        "check_interval": 5,
        "timeout": 15,
        "enabled": True,
    },
    "MSI": {
        "name": "MSI",
        "accounts": [{"id": str(uuid.uuid4()), "username": "Yo123X", "password": "ef64"}],
        "base_url": "http://145.239.130.45/ints",
        "login_page_url": "http://145.239.130.45/ints/login",
        "login_post_url": "http://145.239.130.45/ints/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True,
    },
    "proton SMS": {
        "name": "proton SMS",
        "accounts": [{"id": str(uuid.uuid4()), "username": "LLL", "password": "ELL"}],
        "base_url": "http://109.236.84.81/ints",
        "login_page_url": "http://109.236.84.81/ints/login",
        "login_post_url": "http://109.236.84.81/ints/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 60,
        "enabled": True,
    },
    "IMS": {
        "name": "IMS",
        "accounts": [{"id": str(uuid.uuid4()), "username": "Ahmone", "password": "98"}],
        "base_url": "http://45.82.67.20",
        "login_page_url": "http://45.82.67.20/ints/login",
        "login_post_url": "http://45.82.67.20/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 16,
        "timeout": 30,
        "enabled": True,
    },
    "Roxy SMS": {
        "name": "Roxy SMS",
        "accounts": [{"id": str(uuid.uuid4()), "username": "sool", "password": "Yo123"}],
        "base_url": "http://www.roxysms.net",
        "login_page_url": "http://www.roxysms.net/Login",
        "login_post_url": "http://www.roxysms.net/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True,
        "use_scraper": True,
    },
    "TimeSMS": {
        "name": "TimeSMS",
        "accounts": [{"id": str(uuid.uuid4()), "username": "a", "password": "7"}],
        "base_url": "https://timesms.org",
        "login_page_url": "https://timesms.org/login",
        "login_post_url": "http://timesms.org/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True,
    },
}

account_scrapers = {}
account_sessions = {}
account_last_seen = {}
account_stop_events = {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def migrate_old_settings(settings):
    migrated = False
    for site_key in ["GROUP", "Fly sms", "Number_Panel", "Bolt", "iVASMS", "MSI", "proton SMS", "IMS", "Roxy SMS", "TimeSMS"]:
        if site_key in settings:
            if "username" in settings[site_key] and "accounts" not in settings[site_key]:
                settings[site_key]["accounts"] = [
                    {
                        "id": str(uuid.uuid4()),
                        "username": settings[site_key].pop("username"),
                        "password": settings[site_key].pop("password", ""),
                    }
                ]
                migrated = True
            if settings[site_key].get("check_interval", 5) == 7:
                settings[site_key]["check_interval"] = 5
                migrated = True

    for k in ["iVASMS", "MSI", "proton SMS", "IMS", "Roxy SMS", "TimeSMS"]:
        if k not in settings:
            settings[k] = DEFAULT_SETTINGS[k].copy()
            migrated = True

    if "Share" in settings:
        if "proton SMS" not in settings:
            settings["proton SMS"] = settings["Share"].copy()
            settings["proton SMS"]["name"] = "proton SMS"
        del settings["Share"]
        migrated = True

    return settings, migrated

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                settings, migrated = migrate_old_settings(settings)
                if migrated:
                    save_settings(settings)
                return settings
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def get_site_accounts(site_key):
    return SETTINGS.get(site_key, {}).get("accounts", [])

def add_account(site_key, username, password):
    if site_key not in SETTINGS:
        return False
    account = {"id": str(uuid.uuid4()), "username": username, "password": password}
    SETTINGS[site_key].setdefault("accounts", []).append(account)
    save_settings(SETTINGS)
    return account

def delete_account(site_key, account_id):
    if site_key not in SETTINGS or "accounts" not in SETTINGS[site_key]:
        return False
    accounts = SETTINGS[site_key]["accounts"]
    initial_count = len(accounts)
    SETTINGS[site_key]["accounts"] = [acc for acc in accounts if acc["id"] != account_id]
    if len(SETTINGS[site_key]["accounts"]) < initial_count:
        stop_key = f"{site_key}_{account_id}"
        if stop_key in account_stop_events:
            account_stop_events[stop_key].set()
            del account_stop_events[stop_key]
        for file_path in [
            f"cookies_{site_key}_{account_id}.pkl",
            f"last_message_{site_key}_{account_id}.txt",
            f"sent_messages_{site_key}_{account_id}.json",
        ]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        account_sessions.pop(stop_key, None)
        account_last_seen.pop(stop_key, None)
        save_settings(SETTINGS)
        return True
    return False

def get_account_by_id(site_key, account_id):
    for acc in get_site_accounts(site_key):
        if not account_id or acc["id"] == account_id or acc["id"].startswith(account_id):
            return acc
    accounts = get_site_accounts(site_key)
    return accounts[0] if accounts else None

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)

SETTINGS = load_settings()
SESSIONS = load_sessions()

def get_first_account(site_key):
    accounts = get_site_accounts(site_key)
    return accounts[0] if accounts else {"username": "", "password": ""}

USERNAME = get_first_account("GROUP").get("username", "")
PASSWORD = get_first_account("GROUP").get("password", "")
BASE_URL = SETTINGS["GROUP"]["base_url"]
LOGIN_PAGE_URL = SETTINGS["GROUP"]["login_page_url"]
LOGIN_POST_URL = SETTINGS["GROUP"]["login_post_url"]
AJAX_PATH = SETTINGS["GROUP"]["ajax_path"]
HTTP_TIMEOUT = SETTINGS["GROUP"]["timeout"]
CHECK_INTERVAL = SETTINGS["GROUP"]["check_interval"]

USERNAME2 = get_first_account("Fly sms").get("username", "")
PASSWORD2 = get_first_account("Fly sms").get("password", "")
BASE_URL2 = SETTINGS["Fly sms"]["base_url"]
LOGIN_PAGE_URL2 = SETTINGS["Fly sms"]["login_page_url"]
LOGIN_POST_URL2 = SETTINGS["Fly sms"]["login_post_url"]
AJAX_PATH2 = SETTINGS["Fly sms"]["ajax_path"]
HTTP_TIMEOUT2 = SETTINGS["Fly sms"]["timeout"]
CHECK_INTERVAL2 = SETTINGS["Fly sms"]["check_interval"]

USERNAME3 = get_first_account("Number_Panel").get("username", "")
PASSWORD3 = get_first_account("Number_Panel").get("password", "")
BASE_URL3 = SETTINGS["Number_Panel"]["base_url"]
LOGIN_PAGE_URL3 = SETTINGS["Number_Panel"].get("login_page_url", "")
LOGIN_POST_URL3 = SETTINGS["Number_Panel"].get("login_post_url", "")
AJAX_PATH3 = SETTINGS["Number_Panel"].get("ajax_path", "")
HTTP_TIMEOUT3 = SETTINGS["Number_Panel"]["timeout"]
CHECK_INTERVAL3 = SETTINGS["Number_Panel"]["check_interval"]

USERNAME4 = get_first_account("Bolt").get("username", "")
PASSWORD4 = get_first_account("Bolt").get("password", "")
BASE_URL4 = SETTINGS["Bolt"]["base_url"]
LOGIN_PAGE_URL4 = SETTINGS["Bolt"]["login_page_url"]
LOGIN_POST_URL4 = SETTINGS["Bolt"]["login_post_url"]
AJAX_PATH4 = SETTINGS["Bolt"]["ajax_path"]
HTTP_TIMEOUT4 = SETTINGS["Bolt"]["timeout"]
CHECK_INTERVAL4 = SETTINGS["Bolt"]["check_interval"]

USERNAME5 = get_first_account("iVASMS").get("username", "")
PASSWORD5 = get_first_account("iVASMS").get("password", "")
IVASMS_API_URL = SETTINGS["iVASMS"].get("api_url", "https://maroon-wombat-183778.hostingersite.com/apiivasms/api.php")
IVASMS_API_KEY = get_first_account("iVASMS").get("api_key", "")
HTTP_TIMEOUT5 = SETTINGS["iVASMS"]["timeout"]
CHECK_INTERVAL5 = SETTINGS["iVASMS"]["check_interval"]
LOGIN_PAGE_URL5 = ""
LOGIN_POST_URL5 = ""
SMS_RECEIVED_URL5 = ""
GET_SMS_URL5 = ""
GET_SMS_NUMBER_URL5 = ""
GET_SMS_MESSAGE_URL5 = ""

USERNAME6 = get_first_account("MSI").get("username", "")
PASSWORD6 = get_first_account("MSI").get("password", "")
BASE_URL6 = SETTINGS["MSI"]["base_url"]
LOGIN_PAGE_URL6 = SETTINGS["MSI"]["login_page_url"]
LOGIN_POST_URL6 = SETTINGS["MSI"]["login_post_url"]
AJAX_PATH6 = SETTINGS["MSI"]["ajax_path"]
HTTP_TIMEOUT6 = SETTINGS["MSI"]["timeout"]
CHECK_INTERVAL6 = SETTINGS["MSI"]["check_interval"]

USERNAME7 = get_first_account("proton SMS").get("username", "")
PASSWORD7 = get_first_account("proton SMS").get("password", "")
BASE_URL7 = SETTINGS["proton SMS"]["base_url"]
LOGIN_PAGE_URL7 = SETTINGS["proton SMS"]["login_page_url"]
LOGIN_POST_URL7 = SETTINGS["proton SMS"]["login_post_url"]
AJAX_PATH7 = SETTINGS["proton SMS"]["ajax_path"]
HTTP_TIMEOUT7 = SETTINGS["proton SMS"]["timeout"]
CHECK_INTERVAL7 = SETTINGS["proton SMS"]["check_interval"]

USERNAME8 = get_first_account("IMS").get("username", "")
PASSWORD8 = get_first_account("IMS").get("password", "")
BASE_URL8 = SETTINGS["IMS"]["base_url"]
LOGIN_PAGE_URL8 = SETTINGS["IMS"]["login_page_url"]
LOGIN_POST_URL8 = SETTINGS["IMS"]["login_post_url"]
AJAX_PATH8 = SETTINGS["IMS"]["ajax_path"]
HTTP_TIMEOUT8 = SETTINGS["IMS"]["timeout"]
CHECK_INTERVAL8 = SETTINGS["IMS"]["check_interval"]

USERNAME9 = get_first_account("Roxy SMS").get("username", "")
PASSWORD9 = get_first_account("Roxy SMS").get("password", "")
BASE_URL9 = SETTINGS["Roxy SMS"]["base_url"]
LOGIN_PAGE_URL9 = SETTINGS["Roxy SMS"]["login_page_url"]
LOGIN_POST_URL9 = SETTINGS["Roxy SMS"]["login_post_url"]
AJAX_PATH9 = SETTINGS["Roxy SMS"]["ajax_path"]
HTTP_TIMEOUT9 = SETTINGS["Roxy SMS"]["timeout"]
CHECK_INTERVAL9 = SETTINGS["Roxy SMS"]["check_interval"]

USERNAME10 = get_first_account("TimeSMS").get("username", "")
PASSWORD10 = get_first_account("TimeSMS").get("password", "")
BASE_URL10 = SETTINGS["TimeSMS"]["base_url"]
LOGIN_PAGE_URL10 = SETTINGS["TimeSMS"]["login_page_url"]
LOGIN_POST_URL10 = SETTINGS["TimeSMS"]["login_post_url"]
AJAX_PATH10 = SETTINGS["TimeSMS"]["ajax_path"]
HTTP_TIMEOUT10 = SETTINGS["TimeSMS"]["timeout"]
CHECK_INTERVAL10 = SETTINGS["TimeSMS"]["check_interval"]

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

def create_session_group():
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })
    return sess

session1 = create_session_group()
session2 = requests.Session()
session3 = requests.Session()
session4 = requests.Session()
session5 = requests.Session()
session5.verify = False
session6 = requests.Session()
session7 = requests.Session()
session8 = requests.Session()
session9 = requests.Session()
session10 = requests.Session()

is_logged_in_site1 = False
is_logged_in_site2 = False
is_logged_in_site3 = False
is_logged_in_site4 = False
is_logged_in_site5 = False
is_logged_in_site6 = False
is_logged_in_site7 = False
is_logged_in_site8 = False
is_logged_in_site9 = False
is_logged_in_site10 = False

last_seen_key = ""
last_seen_key_site2 = ""
last_seen_key_site3 = ""
last_seen_key_site4 = ""
last_seen_key_site5 = ""
last_seen_key_site6 = ""
last_seen_key_site7 = ""
last_seen_key_site8 = ""
last_seen_key_site9 = ""
last_seen_key_site10 = ""
csrf_token_site5 = None

COUNTRIES = {}
CHANNELS = []
USERS = {}
ADMINS = [MAIN_ADMIN_ID, 7325261765, 8598137047]
BANNED = []
OTP_GROUP = -1003852565392
GROUPS = [-1003852565392]
REFERRALS = {}
NUMBERS_ADMINS = []

DEFAULT_REFERRAL_SETTINGS = {
    "codes_required_for_referral": 10,
    "referral_bonus": 0.05,
    "code_bonus": 0.002,
    "min_withdrawal": 5.0,
    "enabled": True,
}

DEFAULT_WELCOME_MESSAGES = {
    "ar": "🌐 <b>مرحباً بك في بوت الأرقام المؤقتة!</b>\n\n📱 احصل على رقم مؤقت فوراً\n🔒 آمن وسريع\n💰 اكسب من الإحالات والأكواد\n\nاختر من القائمة:",
    "en": "🌐 <b>Welcome to Temporary Numbers Bot!</b>\n\n📱 Get a temporary number instantly\n🔒 Secure and fast\n💰 Earn from referrals and codes\n\nChoose from the menu:",
}

DEFAULT_BUTTON_LINKS = {
    "group_link": "https://t.me/alorhawa",
    "channel_link": "https://t.me/alorhawa",
    "developer_link": "https://t.me/alorhawa",
}

DEFAULT_OTP_BUTTONS = [
    {"name": "𝙂𝙍𝙊𝙐𝙋", "url": "https://t.me/alorhawa"},
    {"name": "𝘽𝙊𝙏", "url": "https://t.me/alorhawabot"},
    {"name": "𝙊𝙏𝙋", "url": "https://t.me/alorhawa"},
    {"name": "❍𓏺 𝗨𝗻𝗖𝗹𝗘 | 𝗗𝟕 𓏺 𝗕𝗘𝗣𝗢↬", "url": "https://t.me/alorhawa"},
]

DEFAULT_WITHDRAWAL_METHODS = {
    "vodafone": {"name_ar": "فودافون كاش", "name_en": "Vodafone Cash", "enabled": True, "details_ar": "رقم الهاتف", "details_en": "Phone number"},
    "usdt_trc20": {"name_ar": "USDT (TRC20)", "name_en": "USDT (TRC20)", "enabled": True, "details_ar": "عنوان محفظة TRC20", "details_en": "TRC20 wallet address"},
    "usdt_bep20": {"name_ar": "USDT (BEP20)", "name_en": "USDT (BEP20)", "enabled": True, "details_ar": "عنوان محفظة BEP20", "details_en": "BEP20 wallet address"},
    "binance_id": {"name_ar": "Binance ID", "name_en": "Binance ID", "enabled": True, "details_ar": "Binance Pay ID أو Email", "details_en": "Binance Pay ID or Email"},
}

STATISTICS = {
    "total_codes": 0,
    "codes_today": 0,
    "codes_this_week": 0,
    "codes_this_month": 0,
    "last_reset_day": None,
    "last_reset_week": None,
    "last_reset_month": None,
    "daily_history": {},
}

user_states = {}
broadcast_state = {}

TEXTS = {
    "ar": {
        "welcome": "🌐 <b>مرحباً بك في بوت الأرقام!</b>",
        "banned": "🚫 أنت محظور من استخدام هذا البوت.",
        "choose_country": "📲 𝗚𝗲𝘁 𝗡𝘂𝗺𝗯𝗲𝗿",
        "my_account": "👤 𝗠𝘆 𝗔𝗰𝗰𝗼𝘂𝗻𝘁",
        "back": "🔙 رجوع",
        "change_language": "🌐 تغيير اللغة",
        "referral_success": "🎉 <b>تم تسجيلك بنجاح عبر رابط الإحالة!</b>",
        "group_hello_admin": "👋 مرحباً! أنا بوت OTP.",
        "group_hello": "👋 مرحباً! أنا بوت OTP.",
    },
    "en": {
        "welcome": "🌐 <b>Welcome to Numbers Bot!</b>",
        "banned": "🚫 You are banned from using this bot.",
        "choose_country": "📲 𝗚𝗲𝘁 𝗡𝘂𝗺𝗯𝗲𝗿",
        "my_account": "👤 𝗠𝘆 𝗔𝗰𝗰𝗼𝘂𝗻𝘁",
        "back": "🔙 Back",
        "change_language": "🌐 Change Language",
        "referral_success": "🎉 <b>You've registered successfully via referral link!</b>",
        "group_hello_admin": "👋 Hello! I'm the OTP Bot.",
        "group_hello": "👋 Hello! I'm the OTP Bot.",
    },
}

def load_json_file(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return json.loads(json.dumps(default))

def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_numbers_admins():
    global NUMBERS_ADMINS
    NUMBERS_ADMINS = load_json_file(NUMBERS_ADMINS_FILE, [])
    return NUMBERS_ADMINS

def save_numbers_admins():
    save_json_file(NUMBERS_ADMINS_FILE, NUMBERS_ADMINS)

def load_otp_buttons():
    return load_json_file(OTP_BUTTONS_FILE, DEFAULT_OTP_BUTTONS)

def save_otp_buttons(buttons):
    save_json_file(OTP_BUTTONS_FILE, buttons)

def load_button_links():
    return load_json_file(BUTTON_LINKS_FILE, DEFAULT_BUTTON_LINKS)

def save_button_links(links):
    save_json_file(BUTTON_LINKS_FILE, links)

def load_referrals():
    global REFERRALS
    REFERRALS = load_json_file(REFERRALS_FILE, {})
    return REFERRALS

def save_referrals(data=None):
    global REFERRALS
    if data is not None:
        REFERRALS = data
    save_json_file(REFERRALS_FILE, REFERRALS)

def load_referral_settings():
    return load_json_file(REFERRAL_SETTINGS_FILE, DEFAULT_REFERRAL_SETTINGS)

def save_referral_settings(settings):
    save_json_file(REFERRAL_SETTINGS_FILE, settings)

def load_withdrawal_requests():
    return load_json_file(WITHDRAWAL_REQUESTS_FILE, [])

def save_withdrawal_requests(reqs):
    save_json_file(WITHDRAWAL_REQUESTS_FILE, reqs)

def load_withdrawal_methods():
    return load_json_file(WITHDRAWAL_METHODS_FILE, DEFAULT_WITHDRAWAL_METHODS)

def save_withdrawal_methods(methods):
    save_json_file(WITHDRAWAL_METHODS_FILE, methods)

def load_welcome_messages():
    return load_json_file(WELCOME_MESSAGES_FILE, DEFAULT_WELCOME_MESSAGES)

def save_welcome_messages(messages):
    save_json_file(WELCOME_MESSAGES_FILE, messages)

def load_statistics():
    global STATISTICS
    STATISTICS = load_json_file(STATISTICS_FILE, STATISTICS)

def save_statistics():
    save_json_file(STATISTICS_FILE, STATISTICS)

def save_countries():
    save_json_file(COUNTRIES_FILE, COUNTRIES)

def save_channels():
    save_json_file(CHANNELS_FILE, CHANNELS)

def save_users():
    save_json_file(USERS_FILE, USERS)

def save_admins():
    save_json_file(ADMINS_FILE, ADMINS)

def save_banned():
    save_json_file(BANNED_FILE, BANNED)

def save_otp_group():
    save_json_file(OTP_GROUP_FILE, {"group_id": OTP_GROUP})

def save_groups():
    save_json_file(GROUPS_FILE, GROUPS)

def load_data():
    global COUNTRIES, CHANNELS, USERS, ADMINS, BANNED, OTP_GROUP, GROUPS, REFERRALS
    COUNTRIES = load_json_file(COUNTRIES_FILE, {})
    CHANNELS = load_json_file(CHANNELS_FILE, [])
    USERS = load_json_file(USERS_FILE, {})
    ADMINS = load_json_file(ADMINS_FILE, [MAIN_ADMIN_ID, 7325261765, 8598137047])
    if MAIN_ADMIN_ID not in ADMINS:
        ADMINS.append(MAIN_ADMIN_ID)
        save_admins()
    BANNED = load_json_file(BANNED_FILE, [])
    otp_grp = load_json_file(OTP_GROUP_FILE, {"group_id": OTP_GROUP})
    OTP_GROUP = otp_grp.get("group_id", OTP_GROUP)
    GROUPS = load_json_file(GROUPS_FILE, GROUPS)
    REFERRALS = load_json_file(REFERRALS_FILE, {})
    load_numbers_admins()
    load_statistics()

load_data()

def format_decimal(value):
    if value == 0:
        return "0"
    formatted = f"{value:.10f}".rstrip("0").rstrip(".")
    if "." in formatted:
        integer_part, decimal_part = formatted.split(".")
        return f"{integer_part}.{decimal_part[:5]}"
    return formatted

def get_user_language(user_id):
    return USERS.get(str(user_id), {}).get("language", "ar")

def set_user_language(user_id, lang):
    USERS.setdefault(str(user_id), {})["language"] = lang
    save_users()

def t(user_id, key):
    lang = get_user_language(user_id)
    return TEXTS.get(lang, TEXTS["ar"]).get(key, key)

def is_admin(user_id):
    return user_id in ADMINS

def is_numbers_admin(user_id):
    return user_id in NUMBERS_ADMINS or is_admin(user_id)

def is_banned(user_id):
    return user_id in BANNED

def generate_referral_code(user_id):
    return hashlib.md5(f"{user_id}_{datetime.now().timestamp()}".encode()).hexdigest()[:8].upper()

def get_user_referral_data(user_id):
    refs = load_referrals()
    key = str(user_id)
    if key not in refs:
        refs[key] = {
            "referral_code": generate_referral_code(user_id),
            "referred_by": None,
            "referrals": [],
            "referred_users_codes": {},
            "active_referrals": 0,
            "active_referrals_list": [],
            "codes_received": 0,
            "balance": 0.0,
            "total_earned": 0.0,
            "referral_used": False,
        }
        save_referrals(refs)
    return refs[key]

def process_referral(user_id, referrer_id):
    refs = load_referrals()
    u_key = str(user_id)
    r_key = str(referrer_id)
    if u_key not in refs:
        refs[u_key] = {
            "referred_by": r_key,
            "referrals": [],
            "active_referrals": 0,
            "codes_received": 0,
            "balance": 0.0,
            "total_earned": 0.0,
        }
    else:
        if refs[u_key].get("referred_by"):
            return False
        refs[u_key]["referred_by"] = r_key
    refs.setdefault(r_key, {
        "referred_by": None,
        "referrals": [],
        "active_referrals": 0,
        "codes_received": 0,
        "balance": 0.0,
        "total_earned": 0.0,
    })
    if u_key not in refs[r_key]["referrals"]:
        refs[r_key]["referrals"].append(u_key)
    save_referrals(refs)
    return True

def check_subscription(user_id):
    if not CHANNELS:
        return True
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel["id"], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception:
            continue
    return True

def get_flag(country_code):
    if not country_code:
        return "🌍"
    return "".join([chr(0x1F1E6 + ord(c) - ord("A")) for c in country_code.upper()])

def detect_country_from_number(number, user_id=None):
    try:
        s = str(number).strip()
        if not s.startswith("+"):
            s = "+" + s
        try:
            parsed = phonenumbers.parse(s)
        except phonenumbers.NumberParseException:
            parsed = phonenumbers.parse(s + "00000000")
        region = region_code_for_number(parsed)
        if not region:
            return "Unknown", "🌍", "UN"
        lang = get_user_language(user_id) if user_id else "ar"
        country_name = geocoder.description_for_number(parsed, lang)
        if not country_name or country_name == "Unknown":
            try:
                py_country = pycountry.countries.get(alpha_2=region)
                if py_country:
                    country_name = py_country.name
            except Exception:
                pass
        if not country_name or country_name == "Unknown":
            country_name = geocoder.description_for_number(parsed, "en") or region
        return country_name, get_flag(region), region
    except Exception:
        return "Unknown", "🌍", "UN"

def get_flag_for_country_code(country_code):
    try:
        code_str = str(country_code).replace("+", "").strip()
        if code_str.isdigit():
            region = COUNTRY_CODE_TO_REGION_CODE.get(int(code_str), [None])[0]
            if region and region != "ZZ":
                return get_flag(region)
    except Exception:
        pass
    return "🌍"

def get_platforms_list():
    platform_stats = {}
    for _, info in COUNTRIES.items():
        count = info.get("numbers_count", 0)
        for p in info.get("platforms", []):
            platform_stats[p] = platform_stats.get(p, 0) + count

    platform_icons = {
        "Facebook": "📘 Facebook",
        "WhatsApp": "💬 WhatsApp",
        "Telegram": "✈️ Telegram",
        "Instagram": "📸 Instagram",
        "Twitter": "🐦 Twitter/X",
        "TikTok": "📱 TikTok",
        "Discord": "🎮 Discord",
        "Gmail": "📧 Gmail",
    }
    markup = InlineKeyboardMarkup(row_width=1)
    for platform, count in platform_stats.items():
        if count > 0:
            markup.add(InlineKeyboardButton(f"{platform_icons.get(platform, platform)} ({count})", callback_data=f"select_plt_{platform}"))
    return markup

def get_countries_for_platform(platform, user_id=None):
    lang = get_user_language(user_id)
    markup = InlineKeyboardMarkup(row_width=1)
    for cid, info in COUNTRIES.items():
        if platform in info.get("platforms", []):
            display_name = info.get("display_name", cid)
            flag = info.get("flag", "🌍")
            count = info.get("numbers_count", 0)
            code = info.get("code", "")
            label = f"{flag} {display_name}" + (f" (+{code})" if code else "")
            markup.add(InlineKeyboardButton(f"{label} ({count})", callback_data=f"country_{cid}"))
    markup.add(InlineKeyboardButton("🔙 رجوع" if lang == "ar" else "🔙 Back", callback_data="choose_country"))
    return markup

def get_random_number(country_name):
    if country_name not in COUNTRIES:
        return None
    filename = COUNTRIES[country_name].get("file", "")
    if not filename or not os.path.exists(filename):
        return None
    with open(filename, "r", encoding="utf-8") as f:
        numbers = [line.strip() for line in f if line.strip()]
    return random.choice(numbers) if numbers else None

def get_admin_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚙️ إعدادات المواقع", callback_data="admin_sites_menu"),
        InlineKeyboardButton("👥 إدارة الحسابات", callback_data="admin_accounts_menu"),
    )
    markup.add(
        InlineKeyboardButton("➕ إضافة دولة", callback_data="admin_add_country"),
        InlineKeyboardButton("➖ حذف دولة", callback_data="admin_remove_country"),
    )
    markup.add(
        InlineKeyboardButton("📢 إضافة قناة", callback_data="admin_add_channel"),
        InlineKeyboardButton("🗑 حذف قناة", callback_data="admin_remove_channel"),
    )
    markup.add(
        InlineKeyboardButton("📱 إدارة الجروبات", callback_data="admin_groups_menu"),
        InlineKeyboardButton("📣 إذاعة", callback_data="admin_broadcast_menu"),
    )
    markup.add(
        InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user"),
        InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban_user"),
    )
    markup.add(
        InlineKeyboardButton("💰 نظام الإحالات", callback_data="admin_referral_settings"),
        InlineKeyboardButton("📥 نسخة احتياطية", callback_data="admin_create_backup"),
    )
    return markup

def get_sites_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    for site_key in SETTINGS.keys():
        markup.add(InlineKeyboardButton(SETTINGS[site_key].get("name", site_key), callback_data=f"site_config_{site_key}"))
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    return markup

def get_site_config_menu(site_key, account_id=""):
    short_id = account_id[:8] if account_id else ""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👤 تغيير اليوزر", callback_data=f"site_change_user_{site_key}_{short_id}"),
        InlineKeyboardButton("🔑 تغيير الباسورد", callback_data=f"site_change_pass_{site_key}_{short_id}"),
    )
    markup.add(
        InlineKeyboardButton("🔓 اختبار الدخول", callback_data=f"site_test_login_{site_key}_{short_id}"),
        InlineKeyboardButton("📥 اختبار جلب كود", callback_data=f"site_test_fetch_{site_key}_{short_id}"),
    )
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_sites_menu"))
    return markup

@bot.message_handler(commands=["start"])
def start(msg):
    user_id = msg.from_user.id
    if is_banned(user_id):
        bot.reply_to(msg, t(user_id, "banned"))
        return

    if str(user_id) not in USERS:
        USERS[str(user_id)] = {
            "selected_country": None,
            "selected_number": None,
            "language": "ar",
            "join_date": datetime.now().strftime("%Y-%m-%d"),
            "activations": 0,
        }
        save_users()

    if msg.text and len(msg.text.split()) > 1:
        param = msg.text.split()[1]
        if param.startswith("ref_"):
            try:
                ref_id = int(param.replace("ref_", ""))
                if ref_id != user_id:
                    process_referral(user_id, ref_id)
            except Exception:
                pass

    if is_admin(user_id):
        bot.send_message(
            msg.chat.id,
            "🎛 <b>لوحة الإدارة</b>\n\nالبوت يعمل بثبات على Render.",
            parse_mode="HTML",
            reply_markup=get_admin_menu(),
        )
        return

    markup = get_platforms_list()
    code_bonus = load_referral_settings().get("code_bonus", 0.002)
    bot.send_message(
        msg.chat.id,
        f"🚨 <b>اختر المنصة</b>\n\n💰 ستربح <b>${format_decimal(code_bonus)}</b> عند كل كود تستلمه!",
        parse_mode="HTML",
        reply_markup=markup,
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel_cb(call):
    if not is_admin(call.from_user.id):
        return
    bot.edit_message_text("🎛 <b>لوحة الإدارة</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_admin_menu())

@bot.callback_query_handler(func=lambda call: call.data == "admin_sites_menu")
def admin_sites_menu_cb(call):
    if not is_admin(call.from_user.id):
        return
    bot.edit_message_text("⚙️ <b>إعدادات المواقع</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_sites_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("site_config_"))
def site_config_cb(call):
    if not is_admin(call.from_user.id):
        return
    site_key = call.data.replace("site_config_", "")
    if site_key not in SETTINGS:
        return
    acc = get_first_account(site_key)
    txt = (
        f"⚙️ <b>إعدادات {SETTINGS[site_key].get('name', site_key)}</b>\n\n"
        f"👤 الحساب: <code>{acc.get('username', 'N/A')}</code>\n"
        f"⏱ فترة البحث: {SETTINGS[site_key].get('check_interval', 5)}s"
    )
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_site_config_menu(site_key, acc.get("id", "")))

@bot.callback_query_handler(func=lambda call: call.data.startswith(("site_change_user_", "site_change_pass_", "site_test_login_", "site_test_fetch_")))
def site_actions_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    data = call.data
    for prefix in ("site_change_user_", "site_change_pass_", "site_test_login_", "site_test_fetch_"):
        if data.startswith(prefix):
            rest = data[len(prefix):]
            parts = rest.rsplit("_", 1)
            site_key = parts[0] if parts[0] in SETTINGS else rest
            account_id = parts[1] if len(parts) > 1 else ""
            account = get_account_by_id(site_key, account_id)
            if not account:
                bot.answer_callback_query(call.id, "❌ الحساب غير موجود", show_alert=True)
                return
            if prefix == "site_change_user_":
                user_states[user_id] = {"action": "change_site_username", "site_key": site_key, "account_id": account["id"]}
                bot.send_message(call.message.chat.id, f"👤 أرسل اسم المستخدم الجديد لـ <b>{site_key}</b>:", parse_mode="HTML")
            elif prefix == "site_change_pass_":
                user_states[user_id] = {"action": "change_site_password", "site_key": site_key, "account_id": account["id"]}
                bot.send_message(call.message.chat.id, f"🔑 أرسل كلمة المرور الجديدة لـ <b>{site_key}</b>:", parse_mode="HTML")
            else:
                bot.answer_callback_query(call.id, "✅ تم الفحص")
                bot.send_message(call.message.chat.id, f"✅ الحساب <code>{account.get('username')}</code> جاهز في <b>{site_key}</b>.", parse_mode="HTML")
            return

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_country")
def add_country_cb(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = {"action": "add_country_file"}
    bot.send_message(call.message.chat.id, "📤 أرسل ملف الأرقام (.txt):")

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_country")
def remove_country_cb(call):
    if not is_admin(call.from_user.id):
        return
    if not COUNTRIES:
        bot.answer_callback_query(call.id, "❌ لا توجد دول مضافة", show_alert=True)
        return
    markup = InlineKeyboardMarkup(row_width=1)
    for cid, info in COUNTRIES.items():
        markup.add(InlineKeyboardButton(f"❌ {info.get('display_name', cid)} ({info.get('numbers_count', 0)})", callback_data=f"del_c_{cid}"))
    bot.edit_message_text("🗑 اختر دولة لحذفها:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_c_"))
def del_c_cb(call):
    if not is_admin(call.from_user.id):
        return
    cid = call.data.replace("del_c_", "")
    if cid in COUNTRIES:
        fpath = COUNTRIES[cid].get("file")
        if fpath and os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass
        del COUNTRIES[cid]
        save_countries()
        bot.answer_callback_query(call.id, "✅ تم الحذف", show_alert=True)
        admin_panel_cb(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_channel")
def add_channel_cb(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = {"action": "add_channel"}
    bot.send_message(call.message.chat.id, "📢 أرسل معرف القناة (@channel) أو ID القناة:")

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_channel")
def remove_channel_cb(call):
    if not is_admin(call.from_user.id):
        return
    if not CHANNELS:
        bot.answer_callback_query(call.id, "❌ لا توجد قنوات", show_alert=True)
        return
    removed = CHANNELS.pop()
    save_channels()
    bot.answer_callback_query(call.id, f"✅ تم حذف {removed.get('name', 'القناة')}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_groups_menu")
def groups_menu_cb(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = {"action": "set_otp_group"}
    bot.send_message(call.message.chat.id, f"📱 المجموعة الحالية: <code>{OTP_GROUP}</code>\nأرسل Group ID الجديد:", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_menu")
def broadcast_menu_cb(call):
    if not is_admin(call.from_user.id):
        return
    broadcast_state[call.from_user.id] = {"step": "waiting"}
    bot.send_message(call.message.chat.id, "📣 أرسل الرسالة لإذاعتها لجميع المستخدمين:")

@bot.callback_query_handler(func=lambda call: call.data in ("admin_ban_user", "admin_unban_user"))
def ban_unban_cb(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = {"action": call.data}
    bot.send_message(call.message.chat.id, "🆔 أرسل User ID:")

@bot.callback_query_handler(func=lambda call: call.data == "admin_referral_settings")
def ref_settings_cb(call):
    if not is_admin(call.from_user.id):
        return
    s = load_referral_settings()
    bot.send_message(
        call.message.chat.id,
        f"💰 <b>إعدادات الإحالات</b>\n\nبونص الكود: ${s.get('code_bonus')}\nبونص الإحالة: ${s.get('referral_bonus')}\nالحد الأدنى للسحب: ${s.get('min_withdrawal')}",
        parse_mode="HTML",
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_create_backup")
def backup_cb(call):
    if not is_admin(call.from_user.id):
        return
    zpath = backup_manager.create_backup()
    if zpath and os.path.exists(zpath):
        with open(zpath, "rb") as f:
            bot.send_document(call.message.chat.id, f)
        try:
            os.remove(zpath)
        except Exception:
            pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_plt_"))
def select_plt_cb(call):
    platform = call.data.replace("select_plt_", "")
    bot.edit_message_text(
        f"🌍 اختر الدولة لـ <b>{platform}</b>:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=get_countries_for_platform(platform, call.from_user.id),
    )

@bot.callback_query_handler(func=lambda call: call.data == "choose_country")
def choose_country_cb(call):
    bot.edit_message_text("🚨 اختر المنصة:", call.message.chat.id, call.message.message_id, reply_markup=get_platforms_list())

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def country_cb(call):
    cid = call.data.replace("country_", "")
    num = get_random_number(cid)
    if not num:
        bot.answer_callback_query(call.id, "❌ لا توجد أرقام متاحة", show_alert=True)
        return
    uid = str(call.from_user.id)
    USERS.setdefault(uid, {})["selected_country"] = cid
    USERS[uid]["selected_number"] = num
    save_users()
    bot.send_message(call.message.chat.id, f"✅ رقمك: <code>+{num.lstrip('+')}</code>\n⏳ في انتظار الكود...", parse_mode="HTML")

@bot.message_handler(content_types=["text", "document"])
def handle_all_messages(msg):
    user_id = msg.from_user.id
    if msg.chat.type != "private":
        return

    if user_id in broadcast_state and broadcast_state[user_id].get("step") == "waiting":
        ok, fail = 0, 0
        for uid in list(USERS.keys()):
            try:
                bot.copy_message(int(uid), msg.chat.id, msg.message_id)
                ok += 1
            except Exception:
                fail += 1
        del broadcast_state[user_id]
        bot.reply_to(msg, f"✅ تم الإرسال: {ok} | فشل: {fail}")
        return

    state = user_states.get(user_id)
    if not state:
        return

    action = state.get("action")

    if action == "add_country_file" and msg.content_type == "document":
        finfo = bot.get_file(msg.document.file_id)
        raw = bot.download_file(finfo.file_path).decode("utf-8", errors="ignore")
        nums = [re.sub(r"\D", "", line.split()[0]) for line in raw.splitlines() if line.strip() and re.sub(r"\D", "", line.split()[0])]
        if not nums:
            bot.reply_to(msg, "❌ الملف فارغ أو لا يحتوي على أرقام صحيحة.")
            return
        code = nums[0][:2]
        for ln in (3, 2, 1):
            if len(nums[0]) > ln and int(nums[0][:ln]) in COUNTRY_CODE_TO_REGION_CODE:
                code = nums[0][:ln]
                break
        cname, flag, _ = detect_country_from_number(code, user_id)
        fname = f"numbers_{code}_{uuid.uuid4().hex[:6]}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write("\n".join(nums) + "\n")
        cid = f"{cname}_{uuid.uuid4().hex[:6]}"
        COUNTRIES[cid] = {
            "display_name": cname,
            "file": fname,
            "code": code,
            "flag": flag,
            "platforms": ["WhatsApp", "Telegram", "Facebook", "Instagram", "TikTok", "Gmail"],
            "numbers_count": len(nums),
        }
        save_countries()
        del user_states[user_id]
        bot.reply_to(msg, f"✅ تم إضافة {flag} <b>{cname}</b> بعدد <b>{len(nums)}</b> رقم.", parse_mode="HTML")

    elif action == "add_channel" and msg.content_type == "text":
        ch_in = msg.text.strip()
        try:
            chat = bot.get_chat(int(ch_in) if ch_in.lstrip("-").isdigit() else ch_in)
            CHANNELS.append({"id": chat.id, "name": chat.title or ch_in, "username": chat.username or ""})
            save_channels()
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم إضافة القناة: <b>{chat.title or ch_in}</b>", parse_mode="HTML")
        except Exception as e:
            bot.reply_to(msg, f"❌ خطأ: {e}")

    elif action == "set_otp_group" and msg.content_type == "text":
        global OTP_GROUP
        try:
            OTP_GROUP = int(msg.text.strip())
            save_otp_group()
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم تعيين مجموعة OTP: <code>{OTP_GROUP}</code>", parse_mode="HTML")
        except ValueError:
            bot.reply_to(msg, "❌ أرسل ID صحيح.")

    elif action in ("admin_ban_user", "admin_unban_user") and msg.content_type == "text":
        try:
            tid = int(msg.text.strip())
            if action == "admin_ban_user" and tid not in BANNED:
                BANNED.append(tid)
                save_banned()
                bot.reply_to(msg, f"✅ تم حظر <code>{tid}</code>", parse_mode="HTML")
            elif action == "admin_unban_user" and tid in BANNED:
                BANNED.remove(tid)
                save_banned()
                bot.reply_to(msg, f"✅ تم إلغاء حظر <code>{tid}</code>", parse_mode="HTML")
            del user_states[user_id]
        except ValueError:
            bot.reply_to(msg, "❌ أرسل رقم ID صحيح.")

    elif action in ("change_site_username", "change_site_password") and msg.content_type == "text":
        site_key = state.get("site_key")
        acc_id = state.get("account_id")
        field = "username" if action == "change_site_username" else "password"
        for acc in SETTINGS.get(site_key, {}).get("accounts", []):
            if acc["id"] == acc_id:
                acc[field] = msg.text.strip()
                save_settings(SETTINGS)
                break
        del user_states[user_id]
        bot.reply_to(msg, "✅ تم التحديث بنجاح!")

def run_bot():
    try:
        bot.remove_webhook()
    except Exception:
        pass
    while True:
        try:
            bot.infinity_polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
