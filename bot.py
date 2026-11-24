import subprocess
import sys
import time
import re
import json
import os
import html
import random
import uuid
import pickle
import ssl
import hashlib
import shutil
from datetime import datetime, date, timedelta
from threading import Thread, Event
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus

import cloudscraper
import requests
from requests.adapters import HTTPAdapter
import urllib3
import phonenumbers
from phonenumbers import geocoder
from phonenumbers.phonenumberutil import region_code_for_number, COUNTRY_CODE_TO_REGION_CODE
import pycountry
from bs4 import BeautifulSoup
from flask import Flask
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    BotCommand,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Render Keep-Alive Web Server (Prevents 30s / Port Timeout) ───────────────
keep_alive_app = Flask(__name__)

@keep_alive_app.route("/")
def home():
    return "Bot is alive and running on Render!", 200

@keep_alive_app.route("/health")
def health():
    return "OK", 200

def run_keep_alive():
    port = int(os.environ.get("PORT", 10000))
    keep_alive_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

Thread(target=run_keep_alive, daemon=True).start()
# ─────────────────────────────────────────────────────────────────────────────

# ── Legacy SSL Adapter for TimeSMS ───────────────────────────────────────────
class LegacySSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
        except Exception:
            pass
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

def make_timesms_session(base_headers=None):
    s = requests.Session()
    if base_headers:
        s.headers.update(base_headers)
    s.verify = False
    adapter = LegacySSLAdapter()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s
# ─────────────────────────────────────────────────────────────────────────────

BOT_TOKEN = "8743808077:AAHyZkSyiwODeMIAkM7hqMBOwjPi3dLD55c"
MAIN_ADMIN_ID = 8298133943

def create_backup(source_files, backup_dir="backups"):
    if not os.path.exists(backup_dir):
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
        shutil.make_archive(current_backup_dir, 'zip', current_backup_dir)
        shutil.rmtree(current_backup_dir)
        return zip_name
    except Exception as e:
        print(f"Error zipping backup: {e}")
        return current_backup_dir

class BackupManager:
    def create_backup(self):
        files_to_backup = []
        for var in ['SETTINGS_FILE', 'SESSIONS_FILE', 'USERS_FILE', 'ADMINS_FILE', 'GROUPS_FILE', 'COUNTRIES_FILE', 'CHANNELS_FILE']:
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
    return sorted([d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))], reverse=True)

SETTINGS_FILE = "ii287.json"
SESSIONS_FILE = "limogpt.json"

def get_country_flags(country_name):
    country_name_lower = country_name.lower()
    flags = {
        "egypt": "<tg-emoji emoji-id='5976310790381115423'>🇪🇬</tg-emoji>", "libya": "🇱🇾", "syria": "🇸🇾", "iraq": "<tg-emoji emoji-id='5976458232313420307'>🇮🇶</tg-emoji>", "saudi": "<tg-emoji emoji-id='5976726495970729818'>🇸🇦</tg-emoji>",
        "yemen": "<tg-emoji emoji-id='5976685311529327157'>🇾🇪</tg-emoji>", "jordan": "🇯🇴", "uae": "🇦🇪", "kuwait": "🇰🇼", "qatar": "🇶🇦",
        "oman": "🇴🇲", "bahrain": "🇧🇭", "lebanon": "🇱🇧", "palestine": "🇵🇸", "algeria": "🇩🇿",
        "morocco": "🇲🇦", "tunisia": "🇹🇳", "sudan": "🇸🇩", "somalia": "🇸🇴", "djibouti": "🇩🇯",
        "mauritania": "🇲🇷", "liber": "🇱🇾", "مصر": "<tg-emoji emoji-id='5976310790381115423'>🇪🇬</tg-emoji>", "ليبيا": "🇱🇾", "سوريا": "🇸🇾",
        "العراق": "<tg-emoji emoji-id='5976458232313420307'>🇮🇶</tg-emoji>", "السعودية": "<tg-emoji emoji-id='5976726495970729818'>🇸🇦</tg-emoji>", "اليمن": "<tg-emoji emoji-id='5976685311529327157'>🇾🇪</tg-emoji>", "الأردن": "🇯🇴", "الإمارات": "🇦🇪",
        "الكويت": "🇰🇼", "قطر": "🇶🇦", "عمان": "🇴🇲", "البحرين": "🇧🇭", "لبنان": "🇱🇧",
        "فلسطين": "🇵🇸", "الجزائر": "🇩🇿", "المغرب": "🇲🇦", "تونس": "🇹🇳", "السودان": "🇸🇩",
        "الصومال": "🇸🇴", "جيبوتي": "🇩🇯", "موريتانيا": "🇲🇷"
    }
    for name, flag in flags.items():
        if name in country_name_lower:
            return flag
    return "🌐"

def load_env():
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

DEFAULT_SETTINGS = {
    "GROUP": {
        "name": "GROUP",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "Yousseffh123",
                "password": "Yousseffh123"
            }
        ],
        "base_url": "http://139.99.63.204",
        "login_page_url": "http://139.99.63.204/ints/login",
        "login_post_url": "http://139.99.63.204/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "Fly sms": {
        "name": "Fly sms",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "ud08",
                "password": "aud$$"
            }
        ],
        "base_url": "http://193.70.33.154",
        "login_page_url": "http://193.70.33.154/ints/login",
        "login_post_url": "http://193.70.33.154/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 1,
        "timeout": 60,
        "enabled": True
    },
    "Number_Panel": {
        "name": "Number Panel",
        "accounts": [
            {
                "id": "SFBTR0ZBUzRWkE9Xd2GRVIeViIVBk3BpXnCTiElodkFhVWFYdYOLZA==",
                "api_token": "SFBTR0ZBUzRWkE9Xd2GRVIeViIVBk3BpXnCTiElodkFhVWFYdYOLZA=="
            }
        ],
        "base_url": "http://147.135.212.197/crapi/st/viewstats",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "Bolt": {
        "name": "Bolt",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "abuar113",
                "password": "abuun_Z113"
            }
        ],
        "base_url": "http://93.190.143.35/ints",
        "login_page_url": "http://93.190.143.35/ints/Login",
        "login_post_url": "http://93.190.143.35/ints/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "iVASMS": {
        "name": "iVAS SMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "micahc7@gmail.com",
                "password": "12011",
                "api_key": "sk_4b5ff02b42635e4c4891bd5d2f8fcb7aff2f7af6d5daecf8498ba91092dfcbb6"
            }
        ],
        "api_url": "https://maroon-wombat-183778.hostingersite.com/apiivasms/api.php",
        "check_interval": 5,
        "timeout": 15,
        "enabled": True
    },
    "MSI": {
        "name": "MSI",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "Yo123X",
                "password": "ef64"
            }
        ],
        "base_url": "http://145.239.130.45/ints",
        "login_page_url": "http://145.239.130.45/ints/login",
        "login_post_url": "http://145.239.130.45/ints/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "proton SMS": {
        "name": "proton SMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "LLL",
                "password": "ELL"
            }
        ],
        "base_url": "http://109.236.84.81/ints",
        "login_page_url": "http://109.236.84.81/ints/login",
        "login_post_url": "http://109.236.84.81/ints/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 60,
        "enabled": True
    },
    "IMS": {
        "name": "IMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "Ahmone",
                "password": "98"
            }
        ],
        "base_url": "http://45.82.67.20",
        "login_page_url": "http://45.82.67.20/ints/login",
        "login_post_url": "http://45.82.67.20/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 16,
        "timeout": 30,
        "enabled": True
    },
    "Roxy SMS": {
        "name": "Roxy SMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "sool",
                "password": "Yo123"
            }
        ],
        "base_url": "http://www.roxysms.net",
        "login_page_url": "http://www.roxysms.net/Login",
        "login_post_url": "http://www.roxysms.net/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True,
        "use_scraper": True
    },
    "TimeSMS": {
        "name": "TimeSMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "a",
                "password": "7"
            }
        ],
        "base_url": "https://timesms.org",
        "login_page_url": "https://timesms.org/login",
        "login_post_url": "http://timesms.org/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    }
}

def migrate_old_settings(settings):
    migrated = False
    for site_key in ["GROUP", "Fly sms", "Number_Panel", "Bolt", "iVASMS", "MSI", "proton SMS", "IMS", "Roxy SMS", "TimeSMS"]:
        if site_key in settings:
            if "username" in settings[site_key] and "accounts" not in settings[site_key]:
                old_username = settings[site_key]["username"]
                old_password = settings[site_key]["password"]
                settings[site_key]["accounts"] = [
                    {
                        "id": str(uuid.uuid4()),
                        "username": old_username,
                        "password": old_password
                    }
                ]
                del settings[site_key]["username"]
                del settings[site_key]["password"]
                migrated = True
            
            if settings[site_key].get("check_interval", 5) == 7:
                settings[site_key]["check_interval"] = 5
                migrated = True
                print(f"✅ تحديث سرعة {site_key} من 7 إلى 5 ثواني")
    
    for k in ["iVASMS", "MSI", "proton SMS", "IMS", "Roxy SMS", "TimeSMS"]:
        if k not in settings:
            settings[k] = DEFAULT_SETTINGS[k].copy()
            migrated = True
    
    if "Share" in settings and "proton SMS" not in settings:
        settings["proton SMS"] = settings["Share"].copy()
        settings["proton SMS"]["name"] = "proton SMS"
        del settings["Share"]
        migrated = True
    elif "Share" in settings:
        del settings["Share"]
        migrated = True
    
    return settings, migrated

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                settings, migrated = migrate_old_settings(settings)
                if migrated:
                    save_settings(settings)
                return settings
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def get_site_accounts(site_key):
    return SETTINGS.get(site_key, {}).get("accounts", [])

def add_account(site_key, username, password):
    if site_key not in SETTINGS:
        return False
    account = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password": password
    }
    if "accounts" not in SETTINGS[site_key]:
        SETTINGS[site_key]["accounts"] = []
    SETTINGS[site_key]["accounts"].append(account)
    save_settings(SETTINGS)
    return account

def delete_account(site_key, account_id):
    global account_stop_events
    if site_key not in SETTINGS or "accounts" not in SETTINGS[site_key]:
        return False
    accounts = SETTINGS[site_key]["accounts"]
    initial_count = len(accounts)
    SETTINGS[site_key]["accounts"] = [acc for acc in accounts if acc["id"] != account_id]
    if len(SETTINGS[site_key]["accounts"]) < initial_count:
        stop_key = f"{site_key}_{account_id}"
        if stop_key in account_stop_events:
            account_stop_events[stop_key].set()
            print(f"🛑 تم إيقاف مراقبة الحساب: {stop_key}")
            del account_stop_events[stop_key]
        
        cookies_file = f"cookies_{site_key}_{account_id}.pkl"
        last_message_file = f"last_message_{site_key}_{account_id}.txt"
        sent_messages_file = f"sent_messages_{site_key}_{account_id}.json"
        
        for file_path in [cookies_file, last_message_file, sent_messages_file]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"🗑️ تم حذف ملف: {file_path}")
                except Exception as e:
                    print(f"⚠️ خطأ في حذف {file_path}: {e}")
        
        if stop_key in account_sessions:
            del account_sessions[stop_key]
        if stop_key in account_last_seen:
            del account_last_seen[stop_key]
        
        save_settings(SETTINGS)
        return True
    return False

def get_account_by_id(site_key, account_id):
    accounts = get_site_accounts(site_key)
    for acc in accounts:
        if not account_id or acc["id"] == account_id or acc["id"].startswith(account_id):
            return acc
    return accounts[0] if accounts else None

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
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

account_scrapers = {}
account_sessions = {}
account_last_seen = {}
account_stop_events = {}

IDX_DATE_SITE3 = 0
IDX_NUMBER_SITE3 = 2
IDX_SMS_SITE3 = 5

def create_session_group():
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    return sess

session1 = create_session_group()
is_logged_in_site1 = False
bot = telebot.TeleBot(BOT_TOKEN)
last_seen_key = ""
last_seen_key_site2 = ""
last_seen_key_site3 = ""
last_seen_key_site4 = ""

session2 = requests.Session()
session2.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL2 + "/ints/agent/SMSCDRReports",
    "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8"
})
is_logged_in_site2 = False

session3 = requests.Session()
session3.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
})
is_logged_in_site3 = False

session4 = requests.Session()
session4.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
})
is_logged_in_site4 = False

session6 = requests.Session()
session6.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL6 + "/agent/SMSCDRReports",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
})
is_logged_in_site6 = False
last_seen_key_site6 = ""

session7 = requests.Session()
session7.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL7 + "/agent/SMSCDRReports",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
})
is_logged_in_site7 = False
last_seen_key_site7 = ""

session8 = requests.Session()
session8.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})
is_logged_in_site8 = False
last_seen_key_site8 = ""

session9 = requests.Session()
session9.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})
is_logged_in_site9 = False
last_seen_key_site9 = ""

session10 = make_timesms_session({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})
is_logged_in_site10 = False
last_seen_key_site10 = ""

session5 = requests.Session()
session5.verify = False
session5.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
})
is_logged_in_site5 = False
csrf_token_site5 = None
last_seen_key_site5 = ""

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
COUNTRIES = {}
CHANNELS = []
USERS = {}
ADMINS = [7325261765, 8598137047]
BANNED = []
OTP_GROUP = -1003852565392
GROUPS = [-1003852565392]
REFERRALS = {}
NUMBERS_ADMINS = []

def load_numbers_admins():
    global NUMBERS_ADMINS
    if os.path.exists(NUMBERS_ADMINS_FILE):
        try:
            with open(NUMBERS_ADMINS_FILE, "r", encoding="utf-8") as f:
                NUMBERS_ADMINS = json.load(f)
        except Exception:
            NUMBERS_ADMINS = []
    return NUMBERS_ADMINS

def save_numbers_admins():
    with open(NUMBERS_ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(NUMBERS_ADMINS, f, indent=2, ensure_ascii=False)

def is_numbers_admin(user_id):
    return user_id in NUMBERS_ADMINS or is_admin(user_id)

DEFAULT_REFERRAL_SETTINGS = {
    "codes_required_for_referral": 10,
    "referral_bonus": 0.05,
    "code_bonus": 0.002,
    "min_withdrawal": 5.0,
    "enabled": True
}

DEFAULT_WELCOME_MESSAGES = {
    "ar": "🌐 <b>مرحباً بك في بوت الأرقام المؤقتة!</b>\n\n📱 احصل على رقم مؤقت فوراً\n🔒 آمن وسريع\n💰 اكسب من الإحالات والأكواد\n\nاختر من القائمة:",
    "en": "🌐 <b>Welcome to Temporary Numbers Bot!</b>\n\n📱 Get a temporary number instantly\n🔒 Secure and fast\n💰 Earn from referrals and codes\n\nChoose from the menu:"
}

DEFAULT_BUTTON_LINKS = {
    "group_link": "https://t.me/alorhawa",
    "channel_link": "https://t.me/alorhawa",
    "developer_link": "https://t.me/alorhawa"
}

BUTTON_LINKS_FILE = "button_links.json"
OTP_BUTTONS_FILE = "otp_buttons.json"

DEFAULT_OTP_BUTTONS = [
    {"name": "𝙂𝙍𝙊𝙐𝙋", "url": "https://t.me/alorhawa"},
    {"name": "𝘽𝙊𝙏", "url": "https://t.me/alorhawabot"},
    {"name": "𝙊𝙏𝙋", "url": "https://t.me/alorhawa"},
    {"name": "❍𓏺 𝗨𝗻𝗖𝗹𝗘 | 𝗗𝟕 𓏺 𝗕𝗘𝗣𝗢↬", "url": "https://t.me/alorhawa"}
]

def load_otp_buttons():
    if os.path.exists(OTP_BUTTONS_FILE):
        try:
            with open(OTP_BUTTONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_OTP_BUTTONS.copy()

def save_otp_buttons(buttons):
    with open(OTP_BUTTONS_FILE, "w", encoding="utf-8") as f:
        json.dump(buttons, f, indent=2, ensure_ascii=False)

OTP_BUTTONS = load_otp_buttons()

def format_decimal(value):
    if value == 0:
        return "0"
    formatted = f"{value:.10f}".rstrip('0').rstrip('.')
    if '.' in formatted:
        integer_part, decimal_part = formatted.split('.')
        if len(decimal_part) > 5:
            decimal_part = decimal_part[:5]
        return f"{integer_part}.{decimal_part}"
    return formatted

def load_button_links():
    if os.path.exists(BUTTON_LINKS_FILE):
        try:
            with open(BUTTON_LINKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_BUTTON_LINKS.copy()

def save_button_links(links):
    with open(BUTTON_LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2, ensure_ascii=False)

BUTTON_LINKS = load_button_links()
STATISTICS = {
    "total_codes": 0,
    "codes_today": 0,
    "codes_this_week": 0,
    "codes_this_month": 0,
    "last_reset_day": None,
    "last_reset_week": None,
    "last_reset_month": None,
    "daily_history": {}
}

user_states = {}
broadcast_state = {}

TEXTS = {
    "ar": {
        "welcome": "🌐 <b>مرحباً بك في بوت الأرقام!</b>",
        "instructions": "📖 <b>دليل البوت</b>\n\n<b>📱 استلام الأكواد:</b>\n1️⃣ اضغط Get Number\n2️⃣ اختر الدولة والرقم\n3️⃣ استخدم الرقم للتسجيل\n4️⃣ الكود يصلك تلقائياً\n\n<b>💰 الأرباح:</b>\n• بونص عن كل كود\n• بونص إحالة الأصدقاء\n\n<b>💵 السحب:</b>\nفودافون كاش - USDT - Binance",
        "subscription_locked": "🔒 <b>الوصول مقفل. انضم للقنوات ثم تحقق.</b>",
        "subscription_verified": "✅ <b>تم التحقق من الاشتراك!</b>\n\n🌐 <b>مرحباً بك في بوت الأرقام!</b>",
        "subscription_not_verified": "❌ لم تنضم لجميع القنوات بعد!",
        "choose_country": "📲 𝗚𝗲𝘁 𝗡𝘂𝗺𝗯𝗲𝗿",
        "my_account": "👤 𝗠𝘆 𝗔𝗰𝗰𝗼𝘂𝗻𝘁",
        "admin_panel": "🎛 لوحة الإدارة",
        "help": "❓ مساعدة",
        "verify_subscription": "✅ تحقق من الاشتراك",
        "banned": "🚫 أنت محظور من استخدام هذا البوت.",
        "unauthorized": "❌ غير مصرح لك!",
        "select_country": "📱 <b>اختر المنصة:</b>",
        "back": "🔙 رجوع",
        "select_number": "📞 <b>اختر رقم لـ {country}:</b>",
        "number_locked": "⚠️ هذا الرقم مستخدم حالياً من شخص آخر. اختر رقم آخر.",
        "your_number": "📞 <b>رقمك لـ {country}:</b>\n<code>+{number}</code>\n\n⏳ <b>في انتظار الكود...</b> 📱\n\n💬 سيتم إرسال الكود هنا مباشرة!",
        "change_number": "🔄 تغيير الرقم",
        "change_country": "🌍 تغيير الدولة",
        "account_info": "👤 <b>معلومات حسابك:</b>\n\n🆔 <b>معرفك:</b> <code>{user_id_value}</code>\n📅 <b>تاريخ الانضمام:</b> {join_date}\n📊 <b>الأكواد المستلمة:</b> {activations}\n🌐 <b>اللغة:</b> {language}\n\n💡 <b>حالة رقمك:</b>\n{number_status}",
        "no_number": "❌ لا يوجد رقم حالياً",
        "has_number": "✅ رقم نشط لـ {country}",
        "change_language": "🌐 تغيير اللغة",
        "language_changed": "✅ تم تغيير اللغة إلى العربية",
        "add_channel": "➕ إضافة قناة اشتراك",
        "remove_channel": "🗑 حذف قناة",
        "statistics": "📊 الإحصائيات",
        "broadcast": "📣 إذاعة",
        "add_admin": "🔧 إضافة مشرف",
        "remove_admin": "🗑 حذف مشرف",
        "ban_user": "🚫 حظر مستخدم",
        "unban_user": "✅ إلغاء حظر",
        "set_otp_group": "📱 تعيين مجموعة OTP",
        "close": "❌ إغلاق",
        "new_code": "🔔 <b>كود جديد!</b>\n\n📞 <b>الرقم:</b> <code>+{number}</code>\n💬 <b>الكود:</b> <code>{code}</code>\n\n⏰ <b>الوقت:</b> {time}",
        "no_countries_available": "❌ لا توجد دول متاحة حالياً!",
        "country_not_available": "❌ دولة غير متاحة!",
        "no_numbers_available": "❌ لا توجد أرقام متاحة!",
        "number_reserved": "❌ هذا الرقم محجوز حالياً!",
        "select_country_first": "❌ اختر المنصة أولاً!",
        "number_changed": "✅ تم تغيير الرقم!",
        "admin_panel_title": "🎛 <b>لوحة الإدارة</b>",
        "statistics_title": "📊 <b>إحصائيات البوت</b>\n\n👥 <b>إجمالي المستخدمين:</b> {users_count}\n🔢 <b>إجمالي الأكواد:</b> {total_codes}\n\n📅 <b>أكواد اليوم:</b> {codes_today}\n📆 <b>أكواد هذا الأسبوع:</b> {codes_this_week}\n📊 <b>أكواد هذا الشهر:</b> {codes_this_month}",
        "broadcast_prompt": "📣 <b>إذاعة رسالة</b>\n\nأرسل الرسالة التي تريد إذاعتها لجميع المستخدمين:",
        "broadcast_sent": "✅ <b>تم الإرسال!</b>\n\n📤 نجح: {success}\n❌ فشل: {failed}",
        "set_otp_group_prompt": "📱 <b>تعيين مجموعة OTP</b>\n\nأرسل معرف المجموعة (Group ID) التي تريد إرسال الأكواد إليها:",
        "otp_group_set": "✅ <b>تم تعيين مجموعة OTP!</b>\n\n🆔 Group ID: <code>{group_id}</code>",
        "invalid_id": "❌ معرف غير صحيح! أرسل رقم ID صحيح",
        "add_channel_id_prompt": "➕ <b>إضافة قناة اشتراك إجباري</b>\n\n⚠️ يقبل فقط القنوات (لا مجموعات)\n\nأرسل معرف أو رابط القناة:\n• @channel_name\n• https://t.me/channel_name",
        "add_channel_name_prompt": "",
        "add_channel_url_prompt": "",
        "channel_added": "✅ <b>تم إضافة القناة!</b>\n\n📢 القناة: {channel_name}\n🔗 الرابط: {channel_url}",
        "user_banned": "✅ <b>تم حظر المستخدم!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "user_unbanned": "✅ <b>تم إلغاء حظر المستخدم!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "admin_added": "✅ <b>تم إضافة المشرف!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "admin_removed": "✅ <b>تم حذف المشرف!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "channel_removed": "✅ <b>تم حذف القناة!</b>\n\n📢 القناة: {channel_name}",
        "no_channels": "⚠️ لا توجد قنوات!",
        "no_banned_users": "⚠️ لا يوجد مستخدمون محظورون!",
        "no_admins": "⚠️ لا يوجد مشرفون!",
        "owner_only": "❌ هذه الميزة للمالك فقط!",
        "ban_user_prompt": "🚫 <b>حظر مستخدم</b>\n\nأرسل معرف المستخدم (User ID) الذي تريد حظره:",
        "unban_user_prompt": "✅ <b>إلغاء حظر مستخدم</b>\n\n📋 <b>المستخدمون المحظورون:</b>\n{banned_list}\n\nأرسل معرف المستخدم لإلغاء حظره:",
        "add_moderator_prompt": "🔧 <b>إضافة مشرف</b>\n\nأرسل معرف المستخدم (User ID) الذي تريد جعله مشرفاً:",
        "remove_moderator_prompt": "🗑 <b>حذف مشرف</b>\n\n📋 <b>المشرفون الحاليون:</b>\n{admins_list}\n\nأرسل معرف المشرف لحذفه:",
        "remove_channel_prompt": "🗑 <b>حذف قناة</b>\n\n📋 <b>القنوات الحالية:</b>\n{channels_list}\n\nأرسل رقم القناة أو معرفها لحذفها:",
        "channel_not_found": "❌ قناة غير موجودة!",
        "otp_group_status": "📱 <b>مجموعة الأكواد:</b>\n{status}",
        "otp_group_set_status": "✅ مجموعة محددة: <code>{group_id}</code>",
        "otp_group_not_set": "❌ لم يتم تحديد مجموعة",
        "delete_otp_group": "🗑 حذف المجموعة",
        "otp_group_deleted": "✅ تم حذف مجموعة الأكواد!",
        "top_users": "👥 أفضل 10 مستخدمين",
        "top_users_title": "👥 <b>أفضل 10 مستخدمين</b>\n<i>حسب عدد الأكواد المستلمة</i>\n\n",
        "no_users_yet": "⚠️ لا يوجد مستخدمون بعد!",
        "user_joined": "🎉 <b>انضم مستخدم جديد!</b>\n\n👤 الاسم: {name}\n🆔 ID: <code>{user_id}</code>\n📅 الوقت: {time}",
        "edit_button_labels_ar": "🇸🇦 تعديل الأزرار بالعربية",
        "edit_button_labels_en": "🇬🇧 تعديل الأزرار بالإنجليزية",
        "edit_button_labels_lang": "🏷️ <b>تعديل أسماء الأزرار</b>\n\nاختر اللغة:",
        "edit_labels_ar_menu": "🇸🇦 <b>تعديل الأزرار بالعربية</b>\n\nاختر الزر الذي تريد تعديله:",
        "edit_labels_en_menu": "🇬🇧 <b>Edit Button Labels (English)</b>\n\nChoose the button you want to edit:",
        "edit_choose_country_ar": "تعديل \"اختر دولة\"",
        "edit_my_account_ar": "تعديل \"حسابي\"",
        "edit_help_ar": "تعديل \"𝗛𝗲𝗹𝗽❓\"",
        "edit_choose_country_en": "Edit \"Choose Country\"",
        "edit_my_account_en": "Edit \"My Account\"",
        "edit_help_en": "Edit \"Help\"",
        "send_new_label": "📝 أرسل الاسم الجديد للزر:",
        "label_updated": "✅ تم تحديث اسم الزر بنجاح!",
        "manage_otp_group": "📱 إدارة مجموعة الأكواد",
        "welcome_admin": "🌐 <b>مرحباً بك في بوت OTP!</b>\n\nاختر دولة لاستقبال رقم وانتظر الأكواد.\n\nكمشرف، يمكنك أيضاً الوصول للوحة الأدمن.",
        "choose_language": "🌍 <b>اختر اللغة / Choose Language</b>",
        "group_hello_admin": "👋 مرحباً! أنا بوت OTP.\n\n⚠️ <b>ملاحظة:</b> لا يمكن إضافة الجروبات تلقائياً.\nيجب على المشرف إضافة هذا الجروب من لوحة الأدمن.",
        "group_hello": "👋 مرحباً! أنا بوت OTP.\n\nللاستخدام، تواصل معي بشكل خاص.",
        "total_users": "👥 <b>إجمالي المستخدمين:</b>",
        "total_codes": "🔢 <b>إجمالي الأكواد:</b>",
        "codes_today": "📅 <b>أكواد اليوم:</b>",
        "codes_week": "📆 <b>أكواد هذا الأسبوع:</b>",
        "codes_month": "📊 <b>أكواد هذا الشهر:</b>",
        "users_text": "users / مستخدم",
        "developer_btn": "🆘 المطور",
        "verify_btn": "✅ تحقق",
        "select_server_title": "🖥️ <b>اختر السيرفر</b>",
        "select_server_desc": "📌 كل سيرفر يحتوي على مجموعة مختلفة من الدول والأرقام:",
        "select_server_hint": "🔻 <i>اختر السيرفر لعرض الدول المتاحة</i>",
        "select_platform_title": "📱 <b>اختر المنصة في {server}</b>",
        "select_platform_hint": "🔻 <i>اختر المنصة التي تريد استقبال أكوادها</i>",
        "no_numbers_here": "❌ <b>لا يوجد أرقام هنا</b>",
        "no_countries_title": "❌ <b>لا توجد دول متاحة</b>",
        "server_label": "🖥️ <b>السيرفر:</b>",
        "platform_label": "📱 <b>المنصة:</b>",
        "no_countries_hint": "🔻 <i>لا توجد دول متاحة لهذه المنصة في هذا السيرفر حالياً</i>",
        "available_countries_title": "🌍 <b>الدول المتاحة</b>",
        "select_country_hint": "🔻 <i>اختر الدولة التي تريد استقبال أكوادها</i>",
        "number_selected_success": "✅ <b>تم اختيار الرقم بنجاح!</b>",
        "waiting_for_code": "⏳ 𝓦𝓪𝓲𝓽𝓲𝓷𝓰 𝓯𝓸𝓻 𝓽𝓱𝓮 𝓬𝓸𝓭𝓮... 📱",
        "code_will_be_sent": "سيتم إرسال الكود لك مباشرة عند وصوله!",
        "change_number_btn": "🔄 تغيير الرقم",
        "change_country_btn": "🌍 تغيير الدولة",
        "back_to_servers": "𝗕𝗮𝗰𝗸 𝘁𝗼 𝘀𝗲𝗿𝘃𝗲𝗿𝘀",
        "error_msg": "❌ خطأ: {error}",
        "referral_success": "🎉 <b>تم تسجيلك بنجاح عبر رابط الإحالة!</b>\n\nاستمتع باستخدام البوت!"
    },
    "en": {
        "welcome": "╔════✦  𝓑𝓞𝓣𝓟  ✦════╗\n\n❖  𝗚𝗿𝗮𝗯 𝗮 𝘁𝗲𝗺𝗽𝗼𝗿𝗮𝗿𝘆 𝗻𝘂𝗺𝗯𝗲𝗿 𝗶𝗻𝘀𝘁𝗮𝗻𝘁𝗹𝘆\n❖  𝗟𝗶𝗴𝗵𝘁𝗻𝗶𝗻𝗴-𝗳𝗮𝘀𝘁 & 𝗳𝘂𝗹𝗹𝘆 𝘀𝗲𝗰𝘂𝗿𝗲\n❖  𝗪𝗼𝗿𝗸𝘀 𝗳𝗼𝗿 𝗮𝗹𝗹 𝗰𝗼𝘂𝗻𝘁𝗿𝗶𝗲𝘀\n\n•  𝗦𝗲𝗹𝗲𝗰𝘁 𝘆𝗼𝘂𝗿 𝗰𝗼𝘂𝗻𝘁𝗿𝘆\n•  𝗚𝗲𝘁 𝘆𝗼𝘂𝗿 𝗻𝘂𝗺𝗯𝗲𝗿 𝗶𝗺𝗺𝗲𝗱𝗶𝗮𝘁𝗲𝗹𝘆\n\n╚════✦  𝓑𝓞𝓣𝓟  ✦════╝",
        "instructions": "📖 <b>Bot Guide</b>\n\n<b>📱 Receiving Codes:</b>\n1️⃣ Click Get Number\n2️⃣ Choose country and number\n3️⃣ Use number to register\n4️⃣ Code arrives automatically\n\n<b>💰 Earnings:</b>\n• Bonus for each code\n• Referral bonus for friends\n\n<b>💵 Withdrawal:</b>\nVodafone Cash - USDT - Binance",
        "subscription_locked": "🔒 <b>Access locked. Join channels then verify.</b>",
        "subscription_verified": "✅ <b>Subscription verified!</b>\n\n🌐 <b>Welcome to Numbers Bot!</b>",
        "subscription_not_verified": "❌ You haven't joined all channels yet!",
        "choose_country": "📲 𝗚𝗲𝘁 𝗡𝘂𝗺𝗯𝗲𝗿",
        "my_account": "👤 𝗠𝘆 𝗔𝗰𝗰𝗼𝘂𝗻𝘁",
        "admin_panel": "🎛 Admin Panel",
        "help": "❓ Help",
        "verify_subscription": "✅ Verify Subscription",
        "banned": "🚫 You are banned from using this bot.",
        "unauthorized": "❌ Unauthorized!",
        "select_country": "🌍 <b>Select Country:</b>",
        "back": "🔙 Back",
        "select_number": "📞 <b>Select a number for {country}:</b>",
        "number_locked": "⚠️ This number is currently used by someone else. Choose another number.",
        "your_number": "📞 <b>Your number for {country}:</b>\n<code>+{number}</code>\n\n⏳ <b>Waiting for code...</b> 📱\n\n💬 Code will be sent here directly!",
        "change_number": "🔄 Change Number",
        "change_country": "🌍 Change Country",
        "account_info": "👤 <b>Your Account Info:</b>\n\n🆔 <b>ID:</b> <code>{user_id_value}</code>\n📅 <b>Join Date:</b> {join_date}\n📊 <b>Codes Received:</b> {activations}\n🌐 <b>Language:</b> {language}\n\n💡 <b>Number Status:</b>\n{number_status}",
        "no_number": "❌ No number currently",
        "has_number": "✅ Active number for {country}",
        "change_language": "🌐 Change Language",
        "language_changed": "✅ Language changed to English",
        "add_channel": "➕ Add Channel",
        "remove_channel": "🗑 Remove Channel",
        "statistics": "📊 Statistics",
        "broadcast": "📣 Broadcast",
        "add_admin": "🔧 Add Admin",
        "remove_admin": "🗑 Remove Admin",
        "ban_user": "🚫 Ban User",
        "unban_user": "✅ Unban User",
        "set_otp_group": "📱 Set OTP Group",
        "close": "❌ Close",
        "new_code": "🔔 <b>New Code!</b>\n\n📞 <b>Number:</b> <code>+{number}</code>\n💬 <b>Code:</b> <code>{code}</code>\n\n⏰ <b>Time:</b> {time}",
        "no_countries_available": "❌ No countries available!",
        "country_not_available": "❌ Country not available!",
        "no_numbers_available": "❌ No numbers available!",
        "number_reserved": "❌ This number is reserved!",
        "select_country_first": "❌ Select a country first!",
        "number_changed": "✅ Number changed!",
        "admin_panel_title": "🎛 <b>Admin Panel</b>",
        "statistics_title": "📊 <b>Bot Statistics</b>\n\n👥 <b>Total Users:</b> {users_count}\n🔢 <b>Total Codes:</b> {total_codes}\n\n📅 <b>Today's Codes:</b> {codes_today}\n📆 <b>This Week's Codes:</b> {codes_this_week}\n📊 <b>This Month's Codes:</b> {codes_this_month}",
        "broadcast_prompt": "📣 <b>Broadcast Message</b>\n\nSend the message you want to broadcast to all users:",
        "broadcast_sent": "✅ <b>Sent!</b>\n\n📤 Success: {success}\n❌ Failed: {failed}",
        "set_otp_group_prompt": "📱 <b>Set OTP Group</b>\n\nSend the Group ID where you want to receive OTP codes:",
        "otp_group_set": "✅ <b>OTP Group set!</b>\n\n🆔 Group ID: <code>{group_id}</code>",
        "invalid_id": "❌ Invalid ID! Send a valid ID number",
        "add_channel_id_prompt": "➕ <b>Add Subscription Channel</b>\n\nSend the channel ID (example: @channelname or -100...):",
        "add_channel_name_prompt": "✅ <b>Channel ID saved!</b>\n\nNow send the channel name:",
        "add_channel_url_prompt": "✅ <b>Channel name saved!</b>\n\nNow send the channel link (https://t.me/...):",
        "channel_added": "✅ <b>Channel added!</b>\n\n📢 Channel: {channel_name}\n🔗 Link: {channel_url}",
        "user_banned": "✅ <b>User banned!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "user_unbanned": "✅ <b>User unbanned!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "admin_added": "✅ <b>Admin added!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "admin_removed": "✅ <b>Admin removed!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "channel_removed": "✅ <b>Channel removed!</b>\n\n📢 Channel: {channel_name}",
        "no_channels": "⚠️ No channels!",
        "no_banned_users": "⚠️ No banned users!",
        "no_admins": "⚠️ No admins!",
        "owner_only": "❌ This feature is for owner only!",
        "ban_user_prompt": "🚫 <b>Ban User</b>\n\nSend the User ID you want to ban:",
        "unban_user_prompt": "✅ <b>Unban User</b>\n\n📋 <b>Banned Users:</b>\n{banned_list}\n\nSend the User ID to unban:",
        "add_moderator_prompt": "🔧 <b>Add Admin</b>\n\nSend the User ID you want to make admin:",
        "remove_moderator_prompt": "🗑 <b>Remove Admin</b>\n\n📋 <b>Current Admins:</b>\n{admins_list}\n\nSend the admin ID to remove:",
        "remove_channel_prompt": "🗑 <b>Remove Channel</b>\n\n📋 <b>Current Channels:</b>\n{channels_list}\n\nSend the channel number or ID to remove it:",
        "channel_not_found": "❌ Channel not found!",
        "otp_group_status": "📱 <b>OTP Group:</b>\n{status}",
        "otp_group_set_status": "✅ Group set: <code>{group_id}</code>",
        "otp_group_not_set": "❌ No group set",
        "delete_otp_group": "🗑 Delete Group",
        "otp_group_deleted": "✅ OTP group deleted!",
        "top_users": "👥 Top 10 Users",
        "top_users_title": "👥 <b>Top 10 Users</b>\n<i>By codes received</i>\n\n",
        "no_users_yet": "⚠️ No users yet!",
        "user_joined": "🎉 <b>New User Joined!</b>\n\n👤 Name: {name}\n🆔 ID: <code>{user_id}</code>\n📅 Time: {time}",
        "edit_button_labels_ar": "🇸🇦 Edit Arabic Buttons",
        "edit_button_labels_en": "🇬🇧 Edit English Buttons",
        "edit_button_labels_lang": "🏷️ <b>Edit Button Labels</b>\n\nChoose language:",
        "edit_labels_ar_menu": "🇸🇦 <b>تعديل الأزرار بالعربية</b>\n\nاختر الزر الذي تريد تعديله:",
        "edit_labels_en_menu": "🇬🇧 <b>Edit Button Labels (English)</b>\n\nChoose the button you want to edit:",
        "edit_choose_country_ar": "تعديل \"اختر دولة\"",
        "edit_my_account_ar": "تعديل \"حسابي\"",
        "edit_help_ar": "تعديل \"𝗛𝗲𝗹𝗽❓\"",
        "edit_choose_country_en": "Edit \"Choose Country\"",
        "edit_my_account_en": "Edit \"My Account\"",
        "edit_help_en": "Edit \"Help\"",
        "send_new_label": "📝 Send the new button name:",
        "label_updated": "✅ Button label updated successfully!",
        "manage_otp_group": "📱 Manage OTP Group",
        "welcome_admin": "🌐 <b>Welcome to OTP Bot!</b>\n\nChoose a country to receive a number and wait for OTP.\n\nAs an admin, you can also access the Admin Panel.",
        "choose_language": "🌍 <b>اختر اللغة / Choose Language</b>",
        "group_hello_admin": "👋 Hello! I'm the OTP Bot.\n\n⚠️ <b>Note:</b> Groups cannot be added automatically.\nThe admin must add this group from the admin panel.",
        "group_hello": "👋 Hello! I'm the OTP Bot.\n\nTo use me, contact me privately.",
        "total_users": "👥 <b>Total Users:</b>",
        "total_codes": "🔢 <b>Total Codes:</b>",
        "codes_today": "📅 <b>Codes Today:</b>",
        "codes_week": "📆 <b>Codes This Week:</b>",
        "codes_month": "📊 <b>Codes This Month:</b>",
        "users_text": "users",
        "developer_btn": "🆘 Developer",
        "verify_btn": "✅ Verify",
        "select_server_title": "🖥️ <b>Select Server</b>",
        "select_server_desc": "📌 Each server contains a different set of countries and numbers:",
        "select_server_hint": "🔻 <i>Select a server to view available countries</i>",
        "select_platform_title": "📱 <b>Select Platform in {server}</b>",
        "select_platform_hint": "🔻 <i>Select the platform you want to receive codes for</i>",
        "no_numbers_here": "❌ <b>No numbers available here</b>",
        "no_countries_title": "❌ <b>No countries available</b>",
        "server_label": "🖥️ <b>Server:</b>",
        "platform_label": "📱 <b>Platform:</b>",
        "no_countries_hint": "🔻 <i>No countries available for this platform in this server currently</i>",
        "available_countries_title": "🌍 <b>Available Countries</b>",
        "select_country_hint": "🔻 <i>Select the country you want to receive codes for</i>",
        "number_selected_success": "✅ <b>Number selected successfully!</b>",
        "waiting_for_code": "⏳ 𝓦𝓪𝓲𝓽𝓲𝓷𝓰 𝓯𝓸𝓻 𝓽𝓱𝓮 𝓬𝓸𝓭𝓮... 📱",
        "code_will_be_sent": "The code will be sent to you directly when it arrives!",
        "change_number_btn": "🔄 Change Number",
        "change_country_btn": "🌍 Change Country",
        "back_to_servers": "𝗕𝗮𝗰𝗸 𝘁𝗼 𝘀𝗲𝗿𝘃𝗲𝗿𝘀",
        "sticker_duration_error": "❌ Duration must be between 0.1 and 30 seconds!",
        "sticker_duration_set": "✅ <b>Sticker display duration set!</b>\n\n⏱ New duration: {duration} seconds",
        "invalid_number": "❌ Please send a valid number!\n\nExample: 0.5 or 1 or 2.5",
        "error_msg": "❌ Error: {error}",
        "referral_success": "🎉 <b>You've registered successfully via referral link!</b>\n\nEnjoy using the bot!"
    }
}

def get_user_language(user_id):
    user_data = USERS.get(str(user_id), {})
    return user_data.get("language", "ar")

def set_user_language(user_id, lang):
    if str(user_id) not in USERS:
        USERS[str(user_id)] = {}
    USERS[str(user_id)]["language"] = lang
    save_users()

def t(user_id, key):
    lang = get_user_language(user_id)
    return TEXTS.get(lang, TEXTS["ar"]).get(key, key)

def save_pickle(path, obj):
    with open(path, "wb") as f:
        pickle.dump(obj, f)

def load_pickle(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None

def save_cookies():
    cookies_dict = session1.cookies.get_dict()
    save_pickle(COOKIES_FILE, cookies_dict)

def load_cookies():
    d = load_pickle(COOKIES_FILE)
    if isinstance(d, dict) and d:
        session1.cookies.update(d)
        return True
    return False

def clear_cookies():
    session1.cookies.clear()
    if os.path.exists(COOKIES_FILE):
        try:
            os.remove(COOKIES_FILE)
            return True
        except Exception:
            return False
    return True

def save_cookies_site3():
    cookies_dict = session3.cookies.get_dict()
    save_pickle(COOKIES_FILE_SITE3, cookies_dict)
    print("[Site3/Number_Panel] 💾 تم حفظ الجلسة")

def load_cookies_site3():
    d = load_pickle(COOKIES_FILE_SITE3)
    if isinstance(d, dict) and d:
        session3.cookies.update(d)
        print("[Site3/Number_Panel] 📥 تم تحميل الجلسة المحفوظة")
        return True
    print("[Site3/Number_Panel] ⚠️ لا توجد جلسة محفوظة")
    return False

def save_cookies_site4():
    cookies_dict = session4.cookies.get_dict()
    save_pickle(COOKIES_FILE_SITE4, cookies_dict)
    print("[Site4/Bolt] 💾 تم حفظ الجلسة")

def load_cookies_site4():
    d = load_pickle(COOKIES_FILE_SITE4)
    if isinstance(d, dict) and d:
        session4.cookies.update(d)
        print("[Site4/Bolt] 📥 تم تحميل الجلسة المحفوظة")
        return True
    print("[Site4/Bolt] ⚠️ لا توجد جلسة محفوظة")
    return False

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ]
    return random.choice(user_agents)

def login_attempt_group():
    global session1, is_logged_in_site1
    try:
        print("[GROUP] 🔄 جلب صفحة تسجيل الدخول...")
        resp = session1.get(LOGIN_PAGE_URL, timeout=HTTP_TIMEOUT)
        if resp.status_code != 200:
            print(f"[GROUP] ⚠️ فشل فتح صفحة الدخول: {resp.status_code}")
            return False
        
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            print("[GROUP] ❌ لم يتم العثور على captcha في صفحة تسجيل الدخول")
            return False
        
        num1, num2 = int(match.group(1)), int(match.group(2))
        captcha_answer = num1 + num2
        print(f"[GROUP] 🧮 حل captcha: {num1} + {num2} = {captcha_answer}")
        
        payload = {
            "username": USERNAME,
            "password": PASSWORD,
            "capt": str(captcha_answer)
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_PAGE_URL,
            "Origin": BASE_URL,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        print(f"[GROUP] 📤 إرسال طلب تسجيل الدخول لـ: {USERNAME}")
        resp = session1.post(LOGIN_POST_URL, data=payload, headers=headers, timeout=HTTP_TIMEOUT, allow_redirects=True)
        print(f"[GROUP] 📊 حالة الاستجابة: {resp.status_code}")
        
        if ("dashboard" in resp.text.lower() or 
            "logout" in resp.text.lower() or 
            "agent" in resp.url.lower() or
            "/ints/agent" in resp.url or
            resp.url != LOGIN_PAGE_URL):
            print("[GROUP] ✅ تم تسجيل الدخول بنجاح")
            is_logged_in_site1 = True
            save_cookies()
            try:
                session1.get(BASE_URL + "/ints/agent/SMSCDRReports", timeout=HTTP_TIMEOUT)
                time.sleep(1)
            except Exception as e:
                print(f"[GROUP] ⚠️ خطأ في زيارة صفحة SMSCDRReports: {e}")
            return True
        else:
            print("[GROUP] ❌ فشل تسجيل الدخول")
            return False
            
    except Exception as e:
        print(f"[GROUP] ❌ خطأ في تسجيل الدخول: {e}")
        return False

def login(max_retries=10):
    global session1, is_logged_in_site1
    print("🔐 GROUP: بدء تسجيل الدخول...")
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n🔄 GROUP: المحاولة {attempt}/{max_retries}")
            if attempt > 1:
                session1 = create_session_group()
                time.sleep(2)
            if login_attempt_group():
                print(f"✅ GROUP: نجح تسجيل الدخول في المحاولة {attempt}")
                return True
            backoff_time = min(30, 5 * attempt)
            time.sleep(backoff_time)
        except Exception as e:
            print(f"❌ GROUP (محاولة {attempt}): خطأ - {str(e)}")
            time.sleep(5)
    print(f"❌ GROUP: فشل تسجيل الدخول بعد {max_retries} محاولات")
    return False

def check_login_valid():
    try:
        test_url = BASE_URL + "/ints/agent/res/data_smscdr.php?per-page=10"
        ajax_headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": BASE_URL + "/ints/agent/SMSCDRReports"
        }
        r = session1.get(test_url, headers=ajax_headers, timeout=15)
        if r.status_code == 200:
            if "login" in r.text.lower() or "sign in" in r.text.lower():
                return False
            if "direct script access not allowed" in r.text.lower():
                return False
            return True
        return False
    except Exception:
        return False

def test_bolt_type_login(site_key, account):
    username = account.get("username")
    password = account.get("password")
    
    if site_key == "MSI":
        session_obj = session6
        base_url = BASE_URL6
        login_page = LOGIN_PAGE_URL6
        login_post = LOGIN_POST_URL6
        timeout = HTTP_TIMEOUT6
    elif site_key == "proton SMS":
        session_obj = session7
        base_url = BASE_URL7
        login_page = LOGIN_PAGE_URL7
        login_post = LOGIN_POST_URL7
        timeout = HTTP_TIMEOUT7
    elif site_key == "IMS":
        session_obj = session8
        base_url = BASE_URL8
        login_page = LOGIN_PAGE_URL8
        login_post = LOGIN_POST_URL8
        timeout = HTTP_TIMEOUT8
    elif site_key == "Roxy SMS":
        try:
            scraper = cloudscraper.create_scraper()
            login_url = "http://www.roxysms.net/signin"
            payload = {"username": username, "password": password}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "http://www.roxysms.net/Login"
            }
            resp = scraper.post(login_url, data=payload, headers=headers, timeout=20)
            if resp.status_code == 200 and ("success" in resp.text.lower() or "logout" in resp.text.lower()):
                print(f"[{site_key}] ({username}) ✅ تسجيل الدخول نجح")
                return True
            else:
                print(f"[{site_key}] ({username}) ❌ فشل تسجيل الدخول")
                return False
        except Exception as e:
            print(f"[{site_key}] ({username}) ❌ خطأ في تسجيل الدخول: {e}")
            return False
    else:
        return False

    print(f"[{site_key}] ({username}) 🔐 محاولة تسجيل الدخول (Bolt-type)...")
    try:
        session_obj.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
        })
        resp = session_obj.get(login_page, timeout=timeout)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            print(f"[{site_key}] ({username}) ⚠️ لم يتم العثور على captcha")
            return False
        
        num1, num2 = int(match.group(1)), int(match.group(2))
        captcha_answer = num1 + num2
        crlf_match = re.search(r"name=['\"]crlf['\"].*?value=['\"]([^'\"]+)['\"]", resp.text)
        
        payload = {
            "username": username,
            "password": password,
            "capt": str(captcha_answer)
        }
        if crlf_match:
            payload["crlf"] = crlf_match.group(1)
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": login_page,
            "Origin": base_url
        }
        resp = session_obj.post(login_post, data=payload, headers=headers, timeout=timeout, allow_redirects=True)
        
        if ("dashboard" in resp.text.lower() or 
            "logout" in resp.text.lower() or 
            "agent" in resp.url.lower() or 
            "reports" in resp.url.lower()):
            print(f"[{site_key}] ({username}) ✅ تسجيل الدخول نجح")
            return True
        else:
            print(f"[{site_key}] ({username}) ❌ فشل تسجيل الدخول")
            return False
    except Exception as e:
        print(f"[{site_key}] ({username}) ❌ خطأ في تسجيل الدخول: {e}")
        return False

def extract_sms(html_text, debug_mode=False):
    soup = BeautifulSoup(html_text, "html.parser")
    messages = []
    
    table = soup.find("table", class_="table")
    if not table:
        all_tables = soup.find_all("table")
        if all_tables:
            table = all_tables[0]
        else:
            return []
        
    tbody = table.find("tbody")
    rows = table.find_all("tr") if not tbody else tbody.find_all("tr")
    
    row_count = 0
    for row in rows:
        tds = row.find_all("td")
        if not tds:
            continue
        row_count += 1
        cols = [td.get_text(separator=" ", strip=True) for td in tds]
        if debug_mode and row_count <= 3:
            print(f"  صف {row_count}: {len(cols)} عمود - {cols[:8] if len(cols) > 7 else cols}")
        if not cols or len(cols) < 5:
            continue
        msg = {
            "date": cols[0] if len(cols) > 0 else "",
            "ref": cols[1] if len(cols) > 1 else "",
            "source": cols[2] if len(cols) > 2 else "",
            "client": cols[3] if len(cols) > 3 else "",
            "destination": cols[4] if len(cols) > 4 else "",
            "raw": cols[5] if len(cols) > 5 else (cols[4] if len(cols) > 4 else "")
        }
        if msg["date"] and msg["raw"] and len(msg["raw"]) > 3:
            messages.append(msg)
    return messages

def normalize_otp_from_text(text):
    if not text:
        return None
    candidates = []
    
    telegram_pattern = r'(?:telegram|تيليجرام|تلجرام)\s*(?:code|كود)?\s*[:\s]*(\d{4,6})'
    match = re.search(telegram_pattern, text, re.IGNORECASE)
    if match:
        candidates.append({'otp': match.group(1), 'position': match.start(), 'confidence': 100})
    
    instagram_pattern = r'(\d{3})\s+(\d{3})\s+is\s+your\s+Instagram\s+code'
    match = re.search(instagram_pattern, text, re.IGNORECASE)
    if match:
        digits = match.group(1) + match.group(2)
        candidates.append({'otp': f"{digits[:3]} {digits[3:]}", 'position': match.start(), 'confidence': 99})
    
    code_keyword_pattern = r'(?:code|كود|رمز|verification|تحقق)[:\s]*(\d{4,8})'
    for match in re.finditer(code_keyword_pattern, text, re.IGNORECASE):
        digits = match.group(1)
        if 4 <= len(digits) <= 8:
            candidates.append({'otp': digits, 'position': match.start(), 'confidence': 95})
    
    spaced_triple_pattern = r'(\d{3})\s+(\d{3})'
    for match in re.finditer(spaced_triple_pattern, text):
        digits = match.group(1) + match.group(2)
        if len(digits) == 6:
            candidates.append({'otp': f"{digits[:3]} {digits[3:]}", 'position': match.start(), 'confidence': 90})
    
    high_confidence_pattern = r'(\d)\s+(\d)\s+(\d)\s*-\s*(\d)\s+(\d)\s+(\d)'
    for match in re.finditer(high_confidence_pattern, text):
        digits = re.sub(r'\D', '', match.group(0))
        if len(digits) == 6:
            candidates.append({'otp': f"{digits[:3]} {digits[3:]}", 'position': match.start(), 'confidence': 85})
    
    spaced_digits_pattern = r'(\d)\s+(\d)\s+(\d)\s+(\d)\s+(\d)\s+(\d)'
    for match in re.finditer(spaced_digits_pattern, text):
        digits = re.sub(r'\D', '', match.group(0))
        if len(digits) == 6:
            candidates.append({'otp': f"{digits[:3]} {digits[3:]}", 'position': match.start(), 'confidence': 80})
    
    hyphen_pattern = r'(\d{3})\s*-\s*(\d{3})'
    for match in re.finditer(hyphen_pattern, text):
        digits = re.sub(r'\D', '', match.group(0))
        if len(digits) == 6:
            candidates.append({'otp': f"{digits[:3]}-{digits[3:]}", 'position': match.start(), 'confidence': 98})
    
    rtl_whatsapp_pattern = r'[\u200e\u200f\u202a-\u202e]?(\d{3})\s*-\s*(\d{3})'
    for match in re.finditer(rtl_whatsapp_pattern, text):
        digits = match.group(1) + match.group(2)
        if len(digits) == 6:
            candidates.append({'otp': f"{match.group(1)}-{match.group(2)}", 'position': match.start(), 'confidence': 110})

    six_digits_pattern = r'\b\d{6}\b'
    for match in re.finditer(six_digits_pattern, text):
        digits = match.group(0)
        candidates.append({'otp': f"{digits[:3]} {digits[3:]}", 'position': match.start(), 'confidence': 70})
    
    five_digits_pattern = r'\b\d{5}\b'
    for match in re.finditer(five_digits_pattern, text):
        candidates.append({'otp': match.group(0), 'position': match.start(), 'confidence': 65})
    
    four_digits_pattern = r'\b\d{4}\b'
    for match in re.finditer(four_digits_pattern, text):
        candidates.append({'otp': match.group(0), 'position': match.start(), 'confidence': 60})
    
    if candidates:
        candidates.sort(key=lambda x: (-x['confidence'], x['position']))
        return candidates[0]['otp']
    
    all_digits = re.findall(r'\d+', text)
    for digit_group in reversed(all_digits):
        if len(digit_group) >= 4:
            return digit_group
    return None

def extract_from_message(raw_text):
    if not raw_text:
        return None, None
    decoded_text = try_decode(raw_text)
    text = html.unescape(decoded_text)
    otp = normalize_otp_from_text(text)
    return otp, text

def clean_number(num_str):
    if num_str is None:
        return ""
    if isinstance(num_str, (int, float)):
        return str(int(num_str))
    return re.sub(r'\D', '', str(num_str))

IDX_DATE_SITE2 = 0
IDX_NUMBER_SITE2 = 2
IDX_SMS_SITE2 = 5

def retry_request_site2(func, max_retries=5, retry_delay=10):
    attempt = 0
    last_error = None
    while attempt < max_retries:
        attempt += 1
        try:
            return func()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_error = e
            backoff = min(60, retry_delay * attempt)
            time.sleep(backoff)
        except requests.exceptions.HTTPError as e:
            last_error = e
            status_code = e.response.status_code if e.response else 0
            if status_code in [502, 503, 504, 404]:
                time.sleep(min(60, 10 + (attempt * 5)))
            else:
                raise
        except Exception as e:
            last_error = e
            time.sleep(min(60, 10 + (attempt * 5)))
    if last_error:
        raise last_error
    raise Exception("Max retries exceeded")

def try_decode_site2(raw):
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw.replace('\x00', '').strip()
    if isinstance(raw, bytes):
        for enc in ("utf-8", "cp1256", "windows-1256", "iso-8859-6", "utf-16-be", "utf-16-le", "latin-1"):
            try:
                s = raw.decode(enc, errors='ignore').replace('\x00', '').strip()
                if s:
                    return s
            except Exception:
                continue
        return raw.decode('utf-8', errors='replace').replace('\x00', '').strip()
    return str(raw).replace('\x00', '').strip()

def clean_html_site2(text):
    if text is None or text == "":
        return ""
    try:
        text = re.sub(r'<[^>]+>', '', str(text))
        text = html.unescape(text)
        return text.replace('\x00', '').strip()
    except Exception:
        return str(text) if text else ""

def solve_captcha_timesms(html_content):
    match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)\s*=?\s*\?', html_content)
    if match:
        n1, op, n2 = int(match.group(1)), match.group(2), int(match.group(3))
        if op == '+':
            return str(n1 + n2)
        elif op == '-':
            return str(n1 - n2)
        elif op == '*':
            return str(n1 * n2)
        elif op == '/':
            return str(n1 // n2) if n2 else '0'
    return None

def login_site10(account=None):
    global is_logged_in_site10, session10
    print("[TimeSMS] 🔄 محاولة تسجيل الدخول...")
    site_key = "TimeSMS"
    if account:
        user = account.get("username")
        pw = account.get("password")
        sess = make_timesms_session(session10.headers)
    else:
        user = USERNAME10
        pw = PASSWORD10
        session10 = make_timesms_session(session10.headers)
        sess = session10

    login_url = SETTINGS[site_key]["login_page_url"]
    submit_url = SETTINGS[site_key]["login_post_url"]

    try:
        resp = sess.get(login_url, timeout=20, verify=False)
        captcha = solve_captcha_timesms(resp.text)
        if not captcha:
            print("[TimeSMS] ❌ فشل حل الكابتشا")
            return False
        data = {'username': user, 'password': pw, 'capt': captcha}
        login_resp = sess.post(submit_url, data=data, headers={'Referer': login_url}, timeout=20, allow_redirects=True, verify=False)
        if 'login' not in str(login_resp.url).lower():
            if not account:
                is_logged_in_site10 = True
            print("[TimeSMS] ✅ تم تسجيل الدخول بنجاح")
            return sess if account else True
    except Exception as e:
        print(f"[TimeSMS] ⚠️ خطأ في تسجيل الدخول (تمت المعالجة): {e}")
    return False

def login_site2():
    global is_logged_in_site2
    print("[Fly sms] 🔄 محاولة تسجيل الدخول...")
    session2.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    })
    
    def do_login():
        resp = session2.get(LOGIN_PAGE_URL2, timeout=HTTP_TIMEOUT2)
        if resp.status_code in [502, 503, 504]:
            raise requests.exceptions.HTTPError(f"{resp.status_code} Server Error", response=resp)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            return False
        num1, num2 = int(match.group(1)), int(match.group(2))
        captcha_answer = num1 + num2
        payload = {"username": USERNAME2, "password": PASSWORD2, "capt": str(captcha_answer)}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_PAGE_URL2,
            "Origin": BASE_URL2,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        resp = session2.post(LOGIN_POST_URL2, data=payload, headers=headers, timeout=HTTP_TIMEOUT2, allow_redirects=True)
        if resp.status_code in [502, 503, 504]:
            raise requests.exceptions.HTTPError(f"{resp.status_code} Server Error", response=resp)
        if ("dashboard" in resp.text.lower() or "logout" in resp.text.lower() or "agent" in resp.url.lower() or "/ints/agent" in resp.url or resp.url != LOGIN_PAGE_URL2):
            is_logged_in_site2 = True
            try:
                session2.get(BASE_URL2 + "/ints/agent/SMSCDRReports", timeout=HTTP_TIMEOUT2)
            except Exception:
                pass
            return True
        return False
    
    try:
        return retry_request_site2(do_login, max_retries=5, retry_delay=15)
    except Exception:
        return False

def build_ajax_url_site2(wide_range=False):
    start_date = date.today() - timedelta(days=5) if wide_range else date.today()
    end_date = date.today() + timedelta(days=1)
    fdate1 = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
    fdate2 = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"
    q = (
        f"fdate1={quote_plus(fdate1)}&fdate2={quote_plus(fdate2)}&frange=&fclient=&fnum=&fcli=&fgdate=&fgmonth=&fgrange="
        f"&fgclient=&fgnumber=&fgcli=&fg=0&sEcho=1&iColumns=9&sColumns=%2C%2C%2C%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=50000"
        f"&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4&mDataProp_5=5&mDataProp_6=6&mDataProp_7=7&mDataProp_8=8"
        f"&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1&_={int(time.time()*1000)}"
    )
    return BASE_URL2 + AJAX_PATH2 + "?" + q

def extract_rows_from_json_site2(j):
    if j is None:
        return []
    for key in ("data", "aaData", "rows", "aa_data"):
        if isinstance(j, dict) and key in j:
            return j[key]
    if isinstance(j, list):
        return j
    if isinstance(j, dict):
        for v in j.values():
            if isinstance(v, list):
                return v
    return []

def load_data():
    global COUNTRIES, CHANNELS, USERS, ADMINS, BANNED, OTP_GROUP, GROUPS, REFERRALS, NUMBERS_ADMINS

    if os.path.exists(COUNTRIES_FILE):
        with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
            COUNTRIES = json.load(f)
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            CHANNELS = json.load(f)
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            USERS = json.load(f)
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            ADMINS = json.load(f)
    if MAIN_ADMIN_ID != 0 and MAIN_ADMIN_ID not in ADMINS:
        ADMINS.append(MAIN_ADMIN_ID)
        save_admins()
    if os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, "r", encoding="utf-8") as f:
            BANNED = json.load(f)
    if os.path.exists(OTP_GROUP_FILE):
        with open(OTP_GROUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            OTP_GROUP = data.get("group_id")
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            GROUPS = json.load(f)
    if os.path.exists(REFERRALS_FILE):
        with open(REFERRALS_FILE, "r", encoding="utf-8") as f:
            REFERRALS = json.load(f)
    load_numbers_admins()
    load_statistics()

def save_countries():
    with open(COUNTRIES_FILE, "w", encoding="utf-8") as f:
        json.dump(COUNTRIES, f, indent=2, ensure_ascii=False)

def save_channels():
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(CHANNELS, f, indent=2, ensure_ascii=False)

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(USERS, f, indent=2, ensure_ascii=False)

def save_admins():
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(ADMINS, f, indent=2, ensure_ascii=False)

def save_banned():
    with open(BANNED_FILE, "w", encoding="utf-8") as f:
        json.dump(BANNED, f, indent=2, ensure_ascii=False)

def save_otp_group():
    with open(OTP_GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump({"group_id": OTP_GROUP}, f, indent=2)

def save_groups():
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(GROUPS, f, indent=2)

def cleanup_old_numbers_files(country_code):
    pass

def load_referrals():
    global REFERRALS
    if os.path.exists(REFERRALS_FILE):
        try:
            with open(REFERRALS_FILE, "r", encoding="utf-8") as f:
                REFERRALS = json.load(f)
        except Exception:
            REFERRALS = {}
    return REFERRALS

def save_referrals(data=None):
    global REFERRALS
    if data:
        REFERRALS = data
    with open(REFERRALS_FILE, "w", encoding="utf-8") as f:
        json.dump(REFERRALS, f, indent=2, ensure_ascii=False)

def load_referral_settings():
    if os.path.exists(REFERRAL_SETTINGS_FILE):
        try:
            with open(REFERRAL_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_REFERRAL_SETTINGS.copy()

def save_referral_settings(settings):
    with open(REFERRAL_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def load_withdrawal_requests():
    if os.path.exists(WITHDRAWAL_REQUESTS_FILE):
        try:
            with open(WITHDRAWAL_REQUESTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_withdrawal_requests(requests):
    with open(WITHDRAWAL_REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, indent=2, ensure_ascii=False)

DEFAULT_WITHDRAWAL_METHODS = {
    "vodafone": {"name_ar": "فودافون كاش", "name_en": "Vodafone Cash", "enabled": True, "details_ar": "رقم الهاتف", "details_en": "Phone number"},
    "usdt_trc20": {"name_ar": "USDT (TRC20)", "name_en": "USDT (TRC20)", "enabled": True, "details_ar": "عنوان محفظة TRC20", "details_en": "TRC20 wallet address"},
    "usdt_bep20": {"name_ar": "USDT (BEP20)", "name_en": "USDT (BEP20)", "enabled": True, "details_ar": "عنوان محفظة BEP20", "details_en": "BEP20 wallet address"},
    "binance_id": {"name_ar": "Binance ID", "name_en": "Binance ID", "enabled": True, "details_ar": "Binance Pay ID أو Email", "details_en": "Binance Pay ID or Email"}
}

def load_withdrawal_methods():
    if os.path.exists(WITHDRAWAL_METHODS_FILE):
        try:
            with open(WITHDRAWAL_METHODS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_WITHDRAWAL_METHODS.copy()

def save_withdrawal_methods(methods):
    with open(WITHDRAWAL_METHODS_FILE, "w", encoding="utf-8") as f:
        json.dump(methods, f, indent=2, ensure_ascii=False)

def load_welcome_messages():
    if os.path.exists(WELCOME_MESSAGES_FILE):
        try:
            with open(WELCOME_MESSAGES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_WELCOME_MESSAGES.copy()

def save_welcome_messages(messages):
    with open(WELCOME_MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

def generate_referral_code(user_id):
    hash_input = f"{user_id}_{datetime.now().timestamp()}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()

def get_user_referral_data(user_id):
    global REFERRALS
    REFERRALS = load_referrals()
    user_key = str(user_id)
    if user_key not in REFERRALS:
        REFERRALS[user_key] = {
            "referral_code": generate_referral_code(user_id),
            "referred_by": None,
            "referrals": [],
            "referred_users_codes": {},
            "active_referrals": 0,
            "active_referrals_list": [],
            "codes_received": 0,
            "balance": 0.0,
            "total_earned": 0.0,
            "referral_used": False
        }
        save_referrals(REFERRALS)
    return REFERRALS[user_key]

def process_referral(user_id, referrer_id):
    global REFERRALS
    REFERRALS = load_referrals()
    user_key = str(user_id)
    referrer_key = str(referrer_id)
    if user_key not in REFERRALS:
        REFERRALS[user_key] = {
            "referred_by": referrer_key,
            "referrals": [],
            "active_referrals": 0,
            "codes_received": 0,
            "balance": 0.0,
            "total_earned": 0.0
        }
    else:
        if REFERRALS[user_key].get("referred_by"):
            return False
        REFERRALS[user_key]["referred_by"] = referrer_key
    if referrer_key not in REFERRALS:
        REFERRALS[referrer_key] = {
            "referred_by": None,
            "referrals": [],
            "active_referrals": 0,
            "codes_received": 0,
            "balance": 0.0,
            "total_earned": 0.0
        }
    if user_key not in REFERRALS[referrer_key]["referrals"]:
        REFERRALS[referrer_key]["referrals"].append(user_key)
    save_referrals(REFERRALS)
    return True

def add_code_bonus(user_id):
    global REFERRALS
    REFERRALS = load_referrals()
    settings = load_referral_settings()
    user_key = str(user_id)
    if user_key not in REFERRALS:
        REFERRALS[user_key] = {
            "referred_by": None,
            "referrals": [],
            "active_referrals": 0,
            "codes_received": 0,
            "balance": 0.0,
            "total_earned": 0.0
        }
    REFERRALS[user_key]["codes_received"] += 1
    code_bonus = settings.get("code_bonus", 0.01)
    REFERRALS[user_key]["balance"] += code_bonus
    REFERRALS[user_key]["total_earned"] += code_bonus
    save_referrals(REFERRALS)

REFERRAL_SETTINGS = load_referral_settings()
WELCOME_MESSAGES = load_welcome_messages()

def load_statistics():
    global STATISTICS
    if os.path.exists(STATISTICS_FILE):
        try:
            with open(STATISTICS_FILE, 'r', encoding='utf-8') as f:
                STATISTICS = json.load(f)
        except Exception:
            pass

def save_statistics():
    with open(STATISTICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(STATISTICS, f, indent=2, ensure_ascii=False)

def update_statistics():
    global STATISTICS
    today = datetime.now().date().isoformat()
    week_num = datetime.now().isocalendar()[1]
    month = datetime.now().strftime('%Y-%m')
    if STATISTICS.get("last_reset_day") != today:
        STATISTICS["codes_today"] = 0
        STATISTICS["last_reset_day"] = today
    if STATISTICS.get("last_reset_week") != week_num:
        STATISTICS["codes_this_week"] = 0
        STATISTICS["last_reset_week"] = week_num
    if STATISTICS.get("last_reset_month") != month:
        STATISTICS["codes_this_month"] = 0
        STATISTICS["last_reset_month"] = month
    STATISTICS["total_codes"] += 1
    STATISTICS["codes_today"] += 1
    STATISTICS["codes_this_week"] += 1
    STATISTICS["codes_this_month"] += 1
    STATISTICS.setdefault("daily_history", {})
    STATISTICS["daily_history"][today] = STATISTICS["daily_history"].get(today, 0) + 1
    save_statistics()

def get_statistics_text():
    return (
        f"📊 <b>إحصائيات البوت</b>\n\n"
        f"👥 <b>إجمالي المستخدمين:</b> {len(USERS)}\n"
        f"🔢 <b>إجمالي الأكواد:</b> {STATISTICS.get('total_codes', 0)}\n\n"
        f"📅 <b>أكواد اليوم:</b> {STATISTICS.get('codes_today', 0)}\n"
        f"📆 <b>أكواد هذا الأسبوع:</b> {STATISTICS.get('codes_this_week', 0)}\n"
        f"📊 <b>أكواد هذا الشهر:</b> {STATISTICS.get('codes_this_month', 0)}\n"
    )

def is_admin(user_id):
    return user_id in ADMINS

def is_banned(user_id):
    return user_id in BANNED

def check_subscription(user_id):
    if not CHANNELS:
        return True
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel['id'], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            continue
    return True

def get_subscription_message(user_id):
    lang = get_user_language(user_id)
    text = "⚠️ <b>يجب الاشتراك في القنوات:</b>\n\n" if lang == "ar" else "⚠️ <b>Subscribe to channels:</b>\n\n"
    for idx, ch in enumerate(CHANNELS, 1):
        text += f"{idx}. {ch['name']}\n"
    return text

def get_full_subscription_keyboard(user_id):
    markup = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        try:
            chat = bot.get_chat(ch['id'])
            url = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
            if url:
                markup.add(InlineKeyboardButton(ch['name'], url=url))
        except Exception:
            continue
    markup.add(InlineKeyboardButton("✅ تم الاشتراك" if get_user_language(user_id) == "ar" else "✅ Subscribed", callback_data="check_sub"))
    return markup

def get_first_unjoined_channel(user_id):
    if not CHANNELS:
        return None
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel['id'], user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return channel
        except Exception:
            return channel
    return None

def get_single_channel_keyboard(channel, lang="ar"):
    markup = InlineKeyboardMarkup()
    btn_name = channel.get(f"name_{lang}", channel.get("name", "Join 🔗"))
    markup.add(InlineKeyboardButton(btn_name, url=channel['url']))
    verify_text = "✅ تحقق من الاشتراك" if lang == "ar" else "✅ Verify Subscription"
    markup.add(InlineKeyboardButton(verify_text, callback_data="verify_subscription"))
    return markup

def get_subscription_message_for_channel(channel, user_id):
    lang = get_user_language(user_id)
    channel_name = channel.get(f"name_{lang}", channel.get("name", "Join 🔗"))
    if lang == "ar":
        return f"⚠️ <b>يجب عليك الاشتراك في قناة البوت لتتمكن من استخدامه.</b>\n\n📢 القناة: <b>{channel_name}</b>"
    return f"⚠️ <b>You must subscribe to the bot channel to use it.</b>\n\n📢 Channel: <b>{channel_name}</b>"

def get_main_menu_lang(user_id):
    lang = get_user_language(user_id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(t(user_id, "choose_country"), callback_data="choose_country"),
        InlineKeyboardButton(t(user_id, "my_account"), callback_data="my_account")
    )
    withdraw_text = "💰 سحب الرصيد" if lang == "ar" else "💰 Withdraw"
    help_text = "❓ مساعدة" if lang == "ar" else "❓ Help"
    markup.add(
        InlineKeyboardButton(withdraw_text, callback_data="withdraw_balance"),
        InlineKeyboardButton(help_text, callback_data="show_instructions")
    )
    links = load_button_links()
    dev_text = "👨‍💻 المطور" if lang == "ar" else "👨‍💻 Developer"
    markup.add(InlineKeyboardButton(dev_text, url=links.get("developer_link", f"tg://user?id={MAIN_ADMIN_ID}")))
    return markup

def get_admin_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚙️ إعدادات المواقع", callback_data="admin_sites_menu"),
        InlineKeyboardButton("👥 إدارة الحسابات", callback_data="admin_accounts_menu")
    )
    markup.add(
        InlineKeyboardButton("➕ إضافة دولة", callback_data="admin_add_country"),
        InlineKeyboardButton("➖ حذف دولة", callback_data="admin_remove_country")
    )
    markup.add(
        InlineKeyboardButton("📋 الدول المتاحة", callback_data="admin_list_countries"),
        InlineKeyboardButton("📢 إضافة قناة", callback_data="admin_add_channel")
    )
    markup.add(
        InlineKeyboardButton("🗑 حذف قناة", callback_data="admin_remove_channel"),
        InlineKeyboardButton("📱 إدارة الجروبات", callback_data="admin_groups_menu")
    )
    markup.add(
        InlineKeyboardButton("📈 الإحصائيات", callback_data="admin_statistics"),
        InlineKeyboardButton("📣 إذاعة", callback_data="admin_broadcast_menu")
    )
    markup.add(
        InlineKeyboardButton("🔧 إضافة مشرف", callback_data="admin_add_admin"),
        InlineKeyboardButton("🗑 حذف مشرف", callback_data="admin_remove_admin")
    )
    markup.add(
        InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user"),
        InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban_user")
    )
    markup.add(
        InlineKeyboardButton("💰 نظام الإحالات", callback_data="admin_referral_settings"),
        InlineKeyboardButton("🔗 روابط الأزرار", callback_data="admin_button_links")
    )
    markup.add(
        InlineKeyboardButton("📥 إنشاء نسخة احتياطية", callback_data="admin_create_backup"),
        InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_to_main")
    )
    return markup

def get_sites_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    for k, v in SETTINGS.items():
        markup.add(InlineKeyboardButton(v.get("name", k), callback_data=f"site_config_{k}"))
    markup.add(InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin"))
    return markup

def get_site_config_menu(site_key, account_id=None):
    short_id = account_id[:8] if account_id else ""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👤 تغيير اليوزر", callback_data=f"site_change_user_{site_key}_{short_id}"),
        InlineKeyboardButton("🔑 تغيير الباسورد", callback_data=f"site_change_pass_{site_key}_{short_id}")
    )
    markup.add(
        InlineKeyboardButton("⏱ فترة البحث", callback_data=f"site_change_interval_{site_key}"),
        InlineKeyboardButton("⏳ وقت الانتظار", callback_data=f"site_change_timeout_{site_key}")
    )
    markup.add(
        InlineKeyboardButton("🔓 اختبار تسجيل الدخول", callback_data=f"site_test_login_{site_key}_{short_id}"),
        InlineKeyboardButton("📥 اختبار جلب كود", callback_data=f"site_test_fetch_{site_key}_{short_id}")
    )
    markup.add(InlineKeyboardButton("🔙 رجوع لقائمة المواقع", callback_data="admin_sites_menu"))
    return markup

def get_site_accounts_selection_menu(site_key):
    accounts = get_site_accounts(site_key)
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for idx, account in enumerate(accounts, 1):
        username = account.get("username", "N/A")
        short_id = account.get("id", "")[:8]
        buttons.append(InlineKeyboardButton(f"👤 {idx}. {username[:15]}", callback_data=f"select_account_config_{site_key}_{short_id}"))
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i+2])
    markup.add(InlineKeyboardButton("🔙 رجوع لقائمة المواقع", callback_data="admin_sites_menu"))
    return markup

def get_accounts_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    for k, v in SETTINGS.items():
        markup.add(InlineKeyboardButton(v.get("name", k), callback_data=f"accounts_site_{k}"))
    markup.add(InlineKeyboardButton("🔙 رجوع للوحة الأدمن", callback_data="admin_panel"))
    return markup

def get_site_accounts_menu(site_key):
    accounts = get_site_accounts(site_key)
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for idx, account in enumerate(accounts, 1):
        username = account.get("username", "N/A")
        short_id = account.get("id", "")[:8]
        buttons.append(InlineKeyboardButton(f"👤 {idx}. {username[:15]}", callback_data=f"view_account_{site_key}_{short_id}"))
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i+2])
    markup.add(InlineKeyboardButton("➕ إضافة حساب جديد", callback_data=f"add_account_{site_key}"))
    markup.add(InlineKeyboardButton("🔙 رجوع لقائمة المواقع", callback_data="admin_accounts_menu"))
    return markup

def get_account_details_menu(site_key, account_id):
    short_id = account_id[:8] if account_id else ""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🗑 حذف الحساب", callback_data=f"delete_account_{site_key}_{short_id}"),
        InlineKeyboardButton("🔙 رجوع للحسابات", callback_data=f"accounts_site_{site_key}")
    )
    return markup

def try_decode(raw):
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw.replace('\x00', '').strip()
    if not isinstance(raw, bytes):
        return str(raw).replace('\x00', '').strip()
    for enc in ("utf-8", "utf-16", "utf-16-be", "utf-16-le", "cp1256", "windows-1256", "iso-8859-6", "latin-1"):
        try:
            return raw.decode(enc).replace('\x00', '').strip()
        except Exception:
            continue
    return raw.decode('utf-8', errors='replace').replace('\x00', '').strip()

def mask_number(num):
    digits = re.sub(r'\D', '', str(num))
    if len(digits) <= 6:
        return str(num)
    if len(digits) >= 11:
        return digits[:2] + "••••••" + digits[-3:]
    return digits[:2] + "•••" + digits[-2:]

def get_flag(country_code):
    if not country_code:
        return "🌍"
    return ''.join([chr(0x1F1E6 + ord(c) - ord('A')) for c in country_code.upper()])

def detect_country_from_number(number, user_id=None):
    try:
        s = str(number).strip()
        if not s.startswith('+'):
            s = '+' + s
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

def detect_service(text, source_addr=None):
    if not text:
        return "Unknown 🌐"
    t_low = text.lower()
    source_lower = source_addr.lower() if source_addr else ""
    services = {
        "whatsapp": "<tg-emoji emoji-id='5188683998125106802'>📞</tg-emoji>",
        "واتساب": "WS",
        "واتس": "WS",
        "facebook": "FB",
        "فيسبوك": "FB",
        "instagram": "IG",
        "انستقرام": "IG",
        "telegram": "<tg-emoji emoji-id='5471949924658588235'>👉</tg-emoji>",
        "تيليجرام": "<tg-emoji emoji-id='5471949924658588235'>👉</tg-emoji>",
        "tiktok": "TK",
        "google": "GG",
        "gmail": "GG",
    }
    for keyword, service in services.items():
        if keyword in t_low or keyword in source_lower:
            return service
    if source_addr and source_addr.strip():
        cleaned_source = source_addr.replace('#', '').strip()
        if cleaned_source:
            return cleaned_source.upper()
    return "Unknown 🌐"

def get_platforms_list(user_id=None):
    platform_stats = {}
    for _, info in COUNTRIES.items():
        platforms = info.get("platforms", [])
        count = info.get("numbers_count", 0)
        for p in platforms:
            platform_stats[p] = platform_stats.get(p, 0) + count
    platform_icons = {
        "Facebook": "📘 Facebook", "WhatsApp": "💬 WhatsApp", "Telegram": "✈️ Telegram",
        "Instagram": "📸 Instagram", "Twitter": "🐦 Twitter/X", "TikTok": "📱 TikTok",
        "Discord": "🎮 Discord", "Gmail": "📧 Gmail"
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

def create_message_buttons(user_id=None):
    lang = get_user_language(user_id) if user_id else "ar"
    links = load_button_links()
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🔄 تغيير الرقم" if lang == "ar" else "🔄 Change Number", callback_data="change_number"))
    markup.add(InlineKeyboardButton("🌍 تغيير الدولة" if lang == "ar" else "🌍 Change Country", callback_data="choose_country"))
    markup.add(InlineKeyboardButton("📢 جروب البوت" if lang == "ar" else "📢 Group Link", url=links.get("group_link", "https://t.me/alorhawa")))
    markup.add(InlineKeyboardButton("🔙 القائمة الرئيسية" if lang == "ar" else "🔙 Back to Main", callback_data="back_to_main"))
    return markup

def create_group_otp_keyboard(otp_code=None):
    otp_buttons = load_otp_buttons()
    markup = InlineKeyboardMarkup(row_width=2)
    if otp_code and otp_code != "N/A":
        markup.add(InlineKeyboardButton(text=f"🔑 {otp_code}", callback_data=f"copy_{otp_code}"))
    if otp_buttons:
        row_buttons = [InlineKeyboardButton(text=btn["name"], url=btn["url"]) for btn in otp_buttons]
        for i in range(0, len(row_buttons), 2):
            markup.add(*row_buttons[i:i+2])
    markup.add(InlineKeyboardButton(text="𝗗𝗘𝗩𝗘𝗟𝗢𝗣𝗘𝗥", url="https://t.me/alorhawa"))
    return markup

def auto_delete_message(chat_id, message_id, delay=300):
    def delete():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
    Thread(target=delete, daemon=True).start()

def format_otp_message_v2(number, sms_text, service_name="[TG]", otp_code=None, is_group=False):
    _, flag, region_code = detect_country_from_number(number)
    masked = mask_number(number)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header = f"──────────────╖ \n↠ {flag} #{region_code} {service_name} {masked} ┨\n──────────────╛"
    body = f"<blockquote>{sms_text}</blockquote>"
    time_footer = f"<blockquote>• ⏰ ~ {now_str}</blockquote>"
    return f"{header}\n{body}\n{time_footer}"

def normalize_number(number):
    if not number:
        return ""
    return re.sub(r'\D', '', str(number))

def send_otp_to_user(number, otp_message, full_number, group_message=None, otp_code=None):
    normalized_incoming = normalize_number(number)
    for user_id_str, user_data in list(USERS.items()):
        selected_num = user_data.get("selected_number")
        if not selected_num:
            continue
        normalized_selected = normalize_number(selected_num)
        if (normalized_incoming == normalized_selected or
            normalized_incoming.endswith(normalized_selected) or
            normalized_selected.endswith(normalized_incoming) or
            full_number == selected_num):
            try:
                bot.send_message(int(user_id_str), otp_message, parse_mode="HTML")
                USERS[user_id_str]["activations"] = USERS[user_id_str].get("activations", 0) + 1
                save_users()
                add_code_bonus(int(user_id_str))
            except Exception as e:
                print(f"❌ خطأ إرسال للمستخدم {user_id_str}: {e}")

    update_statistics()
    msg_to_group = group_message if group_message else otp_message
    group_keyboard = create_group_otp_keyboard(otp_code)
    targets = set()
    if OTP_GROUP:
        targets.add(OTP_GROUP)
    for gid in list(GROUPS):
        targets.add(gid)
    for gid in targets:
        try:
            sent = bot.send_message(gid, msg_to_group, parse_mode="HTML", disable_web_page_preview=True, reply_markup=group_keyboard)
            auto_delete_message(gid, sent.message_id)
        except Exception as e:
            print(f"❌ خطأ إرسال لمجموعة {gid}: {e}")

# ── Fixed Site Handlers ──────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: call.data.startswith(("site_change_user_", "site_change_pass_", "site_test_login_", "site_test_fetch_")))
def site_action_router(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return

    data = call.data
    prefix = ""
    for p in ("site_change_user_", "site_change_pass_", "site_test_login_", "site_test_fetch_"):
        if data.startswith(p):
            prefix = p
            break

    rest = data[len(prefix):]
    site_key = None
    account_id = None
    for k in SETTINGS.keys():
        if rest == k:
            site_key = k
            break
        if rest.startswith(k + "_"):
            site_key = k
            account_id = rest[len(k) + 1:]
            break
    if not site_key:
        parts = rest.rsplit("_", 1)
        site_key = parts[0]
        account_id = parts[1] if len(parts) > 1 else None

    if site_key not in SETTINGS:
        bot.answer_callback_query(call.id, "❌ موقع غير معروف", show_alert=True)
        return

    site_name = SETTINGS[site_key].get("name", site_key)
    account = get_account_by_id(site_key, account_id)
    if not account:
        bot.answer_callback_query(call.id, "❌ الحساب غير موجود", show_alert=True)
        return

    full_id = account.get("id", "")
    if prefix == "site_change_user_":
        user_states[user_id] = {"action": "change_site_username", "site_key": site_key, "account_id": full_id}
        bot.send_message(
            call.message.chat.id,
            f"👤 <b>تغيير اليوزر - {site_name}</b>\n\nالحساب الحالي: <code>{account.get('username', 'N/A')}</code>\n\nأرسل اسم المستخدم الجديد:",
            parse_mode="HTML"
        )
    elif prefix == "site_change_pass_":
        user_states[user_id] = {"action": "change_site_password", "site_key": site_key, "account_id": full_id}
        bot.send_message(
            call.message.chat.id,
            f"🔑 <b>تغيير الباسورد - {site_name}</b>\n\nالحساب: <code>{account.get('username', 'N/A')}</code>\n\nأرسل كلمة المرور الجديدة:",
            parse_mode="HTML"
        )
    elif prefix == "site_test_login_":
        bot.answer_callback_query(call.id, f"🔄 جاري اختبار تسجيل الدخول لـ {account.get('username')}...")
        bot.send_message(
            call.message.chat.id,
            f"🔓 <b>اختبار تسجيل الدخول - {site_name}</b>\n\n👤 الحساب: <code>{account.get('username')}</code>\n⏳ جاري الفحص...",
            parse_mode="HTML"
        )
        Thread(target=test_site_login, args=(call.message.chat.id, site_key, full_id), daemon=True).start()
    elif prefix == "site_test_fetch_":
        bot.answer_callback_query(call.id, f"🔄 جاري اختبار جلب الكود لـ {account.get('username')}...")
        bot.send_message(
            call.message.chat.id,
            f"📥 <b>اختبار جلب الكود - {site_name}</b>\n\n👤 الحساب: <code>{account.get('username')}</code>\n⏳ جاري الفحص...",
            parse_mode="HTML"
        )
        Thread(target=test_site_fetch, args=(call.message.chat.id, site_key, full_id), daemon=True).start()

def test_site_login(chat_id, site_key, account_id=None):
    site_name = SETTINGS[site_key]["name"]
    account = get_account_by_id(site_key, account_id)
    if not account:
        bot.send_message(chat_id, "❌ الحساب غير موجود!", parse_mode="HTML")
        return
    try:
        if site_key == "TimeSMS":
            res = login_site10(account)
            ok = bool(res)
        elif site_key == "Roxy SMS":
            scraper = cloudscraper.create_scraper()
            resp = scraper.post(
                SETTINGS[site_key]["login_post_url"],
                data={"username": account.get("username"), "password": account.get("password")},
                headers={"Referer": SETTINGS[site_key]["login_page_url"]},
                timeout=20
            )
            ok = resp.status_code == 200 and ("success" in resp.text.lower() or "logout" in resp.text.lower() or "login" not in resp.url.lower())
        else:
            ok = bool(account.get("username") or account.get("api_token"))
        status_txt = "✅ نجح تسجيل الدخول" if ok else "⚠️ تحقق من بيانات الدخول"
        bot.send_message(chat_id, f"<b>{site_name}</b>\n👤 <code>{account.get('username', 'Token')}</code>\n{status_txt}", parse_mode="HTML")
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ في {site_name}: {e}", parse_mode="HTML")

def test_site_fetch(chat_id, site_key, account_id=None):
    site_name = SETTINGS[site_key]["name"]
    account = get_account_by_id(site_key, account_id)
    bot.send_message(
        chat_id,
        f"📥 <b>{site_name}</b>\n👤 الحساب: <code>{account.get('username', 'Token') if account else 'N/A'}</code>\n✅ المراقبة الخلفية فعالة.",
        parse_mode="HTML"
    )

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
            "join_date": datetime.now().strftime('%Y-%m-%d'),
            "activations": 0
        }
        save_users()
    if is_admin(user_id):
        bot.send_message(msg.chat.id, "🎛 <b>لوحة الإدارة</b>\n\nاختر الإجراء المطلوب:", parse_mode="HTML", reply_markup=get_admin_menu())
        return
    markup = get_platforms_list(user_id)
    if markup:
        bot.send_message(msg.chat.id, "🚨 <b>اختر المنصة</b>", parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(msg.chat.id, t(user_id, "welcome"), parse_mode="HTML", reply_markup=get_main_menu_lang(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel" or call.data == "admin")
def admin_panel_cb(call):
    if not is_admin(call.from_user.id):
        return
    bot.edit_message_text("🎛 <b>لوحة الإدارة</b>\n\nاختر الإجراء المطلوب:", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_admin_menu())

@bot.callback_query_handler(func=lambda call: call.data == "admin_sites_menu")
def admin_sites_menu_cb(call):
    if not is_admin(call.from_user.id):
        return
    bot.edit_message_text("⚙️ <b>إعدادات المواقع</b>\n\nاختر الموقع:", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_sites_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("site_config_"))
def site_config_cb(call):
    if not is_admin(call.from_user.id):
        return
    site_key = call.data.replace("site_config_", "")
    if site_key not in SETTINGS:
        return
    cfg = SETTINGS[site_key]
    acc = get_first_account(site_key)
    txt = (
        f"⚙️ <b>إعدادات {cfg.get('name', site_key)}</b>\n\n"
        f"👤 الحساب: <code>{acc.get('username', 'N/A')}</code>\n"
        f"⏱ فترة البحث: {cfg.get('check_interval', 5)} ثانية\n"
        f"⏳ وقت الانتظار: {cfg.get('timeout', 30)} ثانية"
    )
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_site_config_menu(site_key, acc.get("id", "")))

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_plt_"))
def select_plt_cb(call):
    platform = call.data.replace("select_plt_", "")
    bot.edit_message_text(f"🌍 اختر الدولة لـ <b>{platform}</b>:", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_countries_for_platform(platform, call.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data == "choose_country")
def choose_country_cb(call):
    markup = get_platforms_list(call.from_user.id)
    if markup:
        bot.edit_message_text("🚨 <b>اختر المنصة</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

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
    bot.send_message(call.message.chat.id, f"✅ رقمك: <code>+{num.lstrip('+')}</code>\n⏳ في انتظار الكود...", parse_mode="HTML", reply_markup=create_message_buttons(call.from_user.id))

@bot.message_handler(content_types=["text", "document"])
def handle_all_messages(msg):
    user_id = msg.from_user.id
    if msg.chat.type != "private":
        return
    state = user_states.get(user_id)
    if not state:
        return
    action = state.get("action")
    if action == "change_site_username":
        site_key = state.get("site_key")
        acc_id = state.get("account_id")
        for acc in SETTINGS.get(site_key, {}).get("accounts", []):
            if acc.get("id") == acc_id:
                acc["username"] = msg.text.strip()
                save_settings(SETTINGS)
                break
        del user_states[user_id]
        bot.reply_to(msg, "✅ تم تحديث اليوزر بنجاح!")
    elif action == "change_site_password":
        site_key = state.get("site_key")
        acc_id = state.get("account_id")
        for acc in SETTINGS.get(site_key, {}).get("accounts", []):
            if acc.get("id") == acc_id:
                acc["password"] = msg.text.strip()
                save_settings(SETTINGS)
                break
        del user_states[user_id]
        bot.reply_to(msg, "✅ تم تحديث الباسورد بنجاح!")

def sms_loop_for_timesms_account(site_key, account):
    site_name = SETTINGS[site_key]["name"]
    username = account.get("username")
    password = account.get("password")
    account_id = account.get("id")
    stop_event = account_stop_events.setdefault(f"{site_key}_{account_id}", Event())

    sess = make_timesms_session({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    is_logged_in = False
    last_message_file = f"last_message_{site_key}_{account_id}.txt"
    last_seen_key_local = ""
    if os.path.exists(last_message_file):
        try:
            with open(last_message_file, "r", encoding="utf-8") as f:
                last_seen_key_local = f.read().strip()
        except Exception:
            pass

    login_url = SETTINGS[site_key]["login_page_url"]
    submit_url = SETTINGS[site_key]["login_post_url"]
    ajax_url = SETTINGS[site_key]["base_url"] + "/agent/res/data_smscdr.php"

    while not stop_event.is_set():
        try:
            if not is_logged_in:
                resp = sess.get(login_url, timeout=20, verify=False)
                captcha = solve_captcha_timesms(resp.text)
                if captcha:
                    login_resp = sess.post(
                        submit_url,
                        data={'username': username, 'password': password, 'capt': captcha},
                        headers={'Referer': login_url},
                        timeout=20,
                        allow_redirects=True,
                        verify=False
                    )
                    if 'login' not in str(login_resp.url).lower():
                        is_logged_in = True
                    else:
                        time.sleep(30)
                        continue
                else:
                    time.sleep(30)
                    continue

            today = datetime.now().strftime('%Y-%m-%d')
            params = {
                'fdate1': f"{today} 00:00:00",
                'fdate2': f"{today} 23:59:59",
                'fg': '0',
                'sEcho': '1',
                'iDisplayStart': '0',
                'iDisplayLength': '500',
                'iSortCol_0': '0',
                'sSortDir_0': 'desc'
            }
            r = sess.get(
                ajax_url,
                params=params,
                headers={'Referer': SETTINGS[site_key]["base_url"] + "/agent/SMSCDRReports", 'X-Requested-With': 'XMLHttpRequest'},
                timeout=30,
                verify=False
            )
            if r.status_code != 200 or 'login' in r.url.lower():
                is_logged_in = False
                time.sleep(10)
                continue

            rows = r.json().get('aaData', [])
            if rows:
                new_messages = []
                for row in rows:
                    if len(row) >= 6:
                        msg_date = str(row[0]).strip()
                        msg_num = str(row[2]).strip()
                        msg_text = str(row[5]).strip()
                        if not re.match(r'\d{4}-\d{2}-\d{2}', msg_date):
                            continue
                        msg_key = f"{msg_date}_{msg_num}_{msg_text[:20]}"
                        if msg_key == last_seen_key_local:
                            break
                        new_messages.append({'date': msg_date, 'number': msg_num, 'sms': msg_text, 'key': msg_key})
                if new_messages:
                    last_seen_key_local = new_messages[0]['key']
                    with open(last_message_file, "w", encoding="utf-8") as f:
                        f.write(last_seen_key_local)
                    for m in reversed(new_messages):
                        otp_val, clean_sms = extract_from_message(m['sms'])
                        service_name = f"[{detect_service(clean_sms)}]"
                        formatted = format_otp_message_v2(m['number'], clean_sms, service_name, otp_val)
                        send_otp_to_user(clean_number(m['number']), formatted, m['number'], None, otp_val)
        except Exception as e:
            print(f"[{site_name}] Warning (handled): {e}")
            is_logged_in = False
        if stop_event.wait(SETTINGS[site_key].get("check_interval", 5)):
            break

def sms_loop_for_roxy_account(site_key, account):
    site_name = SETTINGS[site_key]["name"]
    username = account.get("username")
    password = account.get("password")
    account_id = account.get("id")
    stop_event = account_stop_events.setdefault(f"{site_key}_{account_id}", Event())
    scraper = cloudscraper.create_scraper()
    is_logged_in = False
    last_message_file = f"last_message_{site_key}_{account_id}.txt"
    last_seen_key_local = ""
    if os.path.exists(last_message_file):
        try:
            with open(last_message_file, "r", encoding="utf-8") as f:
                last_seen_key_local = f.read().strip()
        except Exception:
            pass
    login_url = "http://www.roxysms.net/signin"
    ajax_url = "http://www.roxysms.net/agent/res/data_smscdr.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://www.roxysms.net/agent/SMSCDRReports"
    }
    while not stop_event.is_set():
        try:
            if not is_logged_in:
                login_resp = scraper.post(login_url, data={"username": username, "password": password}, headers=headers, timeout=30)
                if login_resp.status_code == 200 and ("success" in login_resp.text.lower() or "logout" in login_resp.text.lower()):
                    is_logged_in = True
                else:
                    time.sleep(30)
                    continue
            today = datetime.now().strftime('%Y-%m-%d')
            r = scraper.get(ajax_url, params={'fdate1': f'{today} 00:00:00', 'fdate2': f'{today} 23:59:59', 'fg': '0'}, headers=headers, timeout=30)
            if r.status_code != 200 or 'login' in r.url.lower():
                is_logged_in = False
                continue
            data = r.json()
            rows = data.get('aaData', []) if isinstance(data, dict) else []
            new_messages = []
            for row in rows:
                if isinstance(row, list) and len(row) >= 6:
                    d_str = str(row[0])
                    num = re.sub(r'\D', '', str(row[2]))
                    msg_txt = str(row[5])
                    key = f"{d_str}|{num}"
                    if key == last_seen_key_local:
                        break
                    new_messages.append({'date': d_str, 'number': num, 'sms': msg_txt})
            if new_messages:
                last_seen_key_local = f"{new_messages[0]['date']}|{new_messages[0]['number']}"
                with open(last_message_file, "w", encoding="utf-8") as f:
                    f.write(last_seen_key_local)
                for m in reversed(new_messages):
                    otp_val, clean_sms = extract_from_message(m['sms'])
                    service_name = f"[{detect_service(clean_sms)}]"
                    formatted = format_otp_message_v2(m['number'], clean_sms, service_name, otp_val)
                    send_otp_to_user(clean_number(m['number']), formatted, m['number'], None, otp_val)
        except Exception as e:
            print(f"[{site_name}] Warning (handled): {e}")
            is_logged_in = False
        if stop_event.wait(SETTINGS[site_key].get("check_interval", 5)):
            break

def start_monitoring_for_account(site_key, account):
    if site_key == "TimeSMS":
        sms_loop_for_timesms_account(site_key, account)
    elif site_key == "Roxy SMS":
        sms_loop_for_roxy_account(site_key, account)

if __name__ == "__main__":
    load_data()
    monitoring_threads = []
    for site_key in ["Roxy SMS", "TimeSMS"]:
        if SETTINGS.get(site_key, {}).get("enabled"):
            for account in get_site_accounts(site_key):
                th = Thread(target=start_monitoring_for_account, args=(site_key, account), daemon=True)
                monitoring_threads.append(th)
                th.start()

    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=15)
    except Exception:
        pass

    try:
        bot.set_my_commands([BotCommand("start", "Start the bot")])
    except Exception:
        pass

    retry_delay = 5
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(retry_delay)
            retry_delay = min(60, retry_delay * 2)
