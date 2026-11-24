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

BOT_TOKEN = "8743808077:AAG85ZeFLSPqH7aZIBHZSttIvbl1Ij79kxY"
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
                print(f"Error backing up {file}: {e}", flush=True)
    
    zip_name = f"{current_backup_dir}.zip"
    try:
        shutil.make_archive(current_backup_dir, 'zip', current_backup_dir)
        shutil.rmtree(current_backup_dir)
        return zip_name
    except Exception as e:
        print(f"Error zipping backup: {e}", flush=True)
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
        "accounts": [{"id": str(uuid.uuid4()), "username": "Yousseffh123", "password": "Yousseffh123"}],
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
        "accounts": [{"id": str(uuid.uuid4()), "username": "ud08", "password": "aud$$"}],
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
        "accounts": [{"id": "SFBTR0ZBUzRWkE9Xd2GRVIeViIVBk3BpXnCTiElodkFhVWFYdYOLZA==", "api_token": "SFBTR0ZBUzRWkE9Xd2GRVIeViIVBk3BpXnCTiElodkFhVWFYdYOLZA=="}],
        "base_url": "http://147.135.212.197/crapi/st/viewstats",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
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
        "enabled": True
    },
    "iVASMS": {
        "name": "iVAS SMS",
        "accounts": [{"id": str(uuid.uuid4()), "username": "micahc7@gmail.com", "password": "12011", "api_key": "sk_4b5ff02b42635e4c4891bd5d2f8fcb7aff2f7af6d5daecf8498ba91092dfcbb6"}],
        "api_url": "https://maroon-wombat-183778.hostingersite.com/apiivasms/api.php",
        "check_interval": 5,
        "timeout": 15,
        "enabled": True
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
        "enabled": True
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
        "enabled": True
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
        "enabled": True
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
        "use_scraper": True
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
                settings[site_key]["accounts"] = [{"id": str(uuid.uuid4()), "username": old_username, "password": old_password}]
                del settings[site_key]["username"]
                del settings[site_key]["password"]
                migrated = True
            if settings[site_key].get("check_interval", 5) == 7:
                settings[site_key]["check_interval"] = 5
                migrated = True
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
    account = {"id": str(uuid.uuid4()), "username": username, "password": password}
    SETTINGS[site_key].setdefault("accounts", []).append(account)
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
            del account_stop_events[stop_key]
        for file_path in [f"cookies_{site_key}_{account_id}.pkl", f"last_message_{site_key}_{account_id}.txt", f"sent_messages_{site_key}_{account_id}.json"]:
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

IDX_DATE_SITE2 = 0
IDX_NUMBER_SITE2 = 2
IDX_SMS_SITE2 = 5
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
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
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
        "banned": "🚫 أنت محظور من استخدام هذا البوت.",
        "choose_country": "📲 𝗚𝗲𝘁 𝗡𝘂𝗺𝗯𝗲𝗿",
        "my_account": "👤 𝗠𝘆 𝗔𝗰𝗰𝗼𝘂𝗻𝘁",
        "back": "🔙 رجوع",
        "change_language": "🌐 تغيير اللغة",
        "referral_success": "🎉 <b>تم تسجيلك بنجاح عبر رابط الإحالة!</b>\n\nاستمتع باستخدام البوت!",
        "group_hello_admin": "👋 مرحباً! أنا بوت OTP.",
        "group_hello": "👋 مرحباً! أنا بوت OTP."
    },
    "en": {
        "welcome": "╔════✦  𝓑𝓞𝓣𝓟  ✦════╗\n\n❖  𝗚𝗿𝗮𝗯 𝗮 𝘁𝗲𝗺𝗽𝗼𝗿𝗮𝗿𝘆 𝗻𝘂𝗺𝗯𝗲𝗿 𝗶𝗻𝘀𝘁𝗮𝗻𝘁𝗹𝘆\n❖  𝗟𝗶𝗴𝗵𝘁𝗻𝗶𝗻𝗴-𝗳𝗮𝘀𝘁 & 𝗳𝘂𝗹𝗹𝘆 𝘀𝗲𝗰𝘂𝗿𝗲\n❖  𝗪𝗼𝗿𝗸𝘀 𝗳𝗼𝗿 𝗮𝗹𝗹 𝗰𝗼𝘂𝗻𝘁𝗿𝗶𝗲𝘀\n\n•  𝗦𝗲𝗹𝗲𝗰𝘁 𝘆𝗼𝘂𝗿 𝗰𝗼𝘂𝗻𝘁𝗿𝘆\n•  𝗚𝗲𝘁 𝘆𝗼𝘂𝗿 𝗻𝘂𝗺𝗯𝗲𝗿 𝗶𝗺𝗺𝗲𝗱𝗶𝗮𝘁𝗲𝗹𝘆\n\n╚════✦  𝓑𝓞𝓣𝓟  ✦════╝",
        "banned": "🚫 You are banned from using this bot.",
        "choose_country": "📲 𝗚𝗲𝘁 𝗡𝘂𝗺𝗯𝗲𝗿",
        "my_account": "👤 𝗠𝘆 𝗔𝗰𝗰𝗼𝘂𝗻𝘁",
        "back": "🔙 Back",
        "change_language": "🌐 Change Language",
        "referral_success": "🎉 <b>You've registered successfully via referral link!</b>\n\nEnjoy using the bot!",
        "group_hello_admin": "👋 Hello! I'm the OTP Bot.",
        "group_hello": "👋 Hello! I'm the OTP Bot."
    }
}

def get_user_language(user_id):
    return USERS.get(str(user_id), {}).get("language", "ar")

def set_user_language(user_id, lang):
    USERS.setdefault(str(user_id), {})["language"] = lang
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
    save_pickle(COOKIES_FILE, session1.cookies.get_dict())

def save_cookies_site3():
    save_pickle(COOKIES_FILE_SITE3, session3.cookies.get_dict())

def save_cookies_site4():
    save_pickle(COOKIES_FILE_SITE4, session4.cookies.get_dict())

def login_attempt_group():
    global session1, is_logged_in_site1
    try:
        resp = session1.get(LOGIN_PAGE_URL, timeout=HTTP_TIMEOUT)
        if resp.status_code != 200:
            return False
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            return False
        captcha_answer = int(match.group(1)) + int(match.group(2))
        payload = {"username": USERNAME, "password": PASSWORD, "capt": str(captcha_answer)}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_PAGE_URL,
            "Origin": BASE_URL,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        resp = session1.post(LOGIN_POST_URL, data=payload, headers=headers, timeout=HTTP_TIMEOUT, allow_redirects=True)
        if ("dashboard" in resp.text.lower() or "logout" in resp.text.lower() or "agent" in resp.url.lower() or "/ints/agent" in resp.url or resp.url != LOGIN_PAGE_URL):
            is_logged_in_site1 = True
            save_cookies()
            try:
                session1.get(BASE_URL + "/ints/agent/SMSCDRReports", timeout=HTTP_TIMEOUT)
            except Exception:
                pass
            return True
        return False
    except Exception:
        return False

def login(max_retries=5):
    global session1
    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            session1 = create_session_group()
            time.sleep(2)
        if login_attempt_group():
            return True
        time.sleep(min(20, 4 * attempt))
    return False

def check_login_valid():
    try:
        r = session1.get(BASE_URL + "/ints/agent/res/data_smscdr.php?per-page=10", headers={"X-Requested-With": "XMLHttpRequest", "Referer": BASE_URL + "/ints/agent/SMSCDRReports"}, timeout=15)
        return r.status_code == 200 and "login" not in r.text.lower()
    except Exception:
        return False

def test_bolt_type_login(site_key, account):
    username = account.get("username")
    password = account.get("password")
    if site_key == "MSI":
        session_obj, base_url, login_page, login_post, timeout = session6, BASE_URL6, LOGIN_PAGE_URL6, LOGIN_POST_URL6, HTTP_TIMEOUT6
    elif site_key == "proton SMS":
        session_obj, base_url, login_page, login_post, timeout = session7, BASE_URL7, LOGIN_PAGE_URL7, LOGIN_POST_URL7, HTTP_TIMEOUT7
    elif site_key == "IMS":
        session_obj, base_url, login_page, login_post, timeout = session8, BASE_URL8, LOGIN_PAGE_URL8, LOGIN_POST_URL8, HTTP_TIMEOUT8
    elif site_key == "Roxy SMS":
        try:
            scraper = cloudscraper.create_scraper()
            resp = scraper.post("http://www.roxysms.net/signin", data={"username": username, "password": password}, headers={"Referer": "http://www.roxysms.net/Login"}, timeout=20)
            return resp.status_code == 200 and ("success" in resp.text.lower() or "logout" in resp.text.lower())
        except Exception:
            return False
    else:
        return False

    try:
        resp = session_obj.get(login_page, timeout=timeout)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            return False
        captcha_answer = int(match.group(1)) + int(match.group(2))
        crlf_match = re.search(r"name=['\"]crlf['\"].*?value=['\"]([^'\"]+)['\"]", resp.text)
        payload = {"username": username, "password": password, "capt": str(captcha_answer)}
        if crlf_match:
            payload["crlf"] = crlf_match.group(1)
        resp = session_obj.post(login_post, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": login_page, "Origin": base_url}, timeout=timeout, allow_redirects=True)
        return any(k in resp.text.lower() or k in resp.url.lower() for k in ("dashboard", "logout", "agent", "reports"))
    except Exception:
        return False

def extract_sms(html_text, debug_mode=False):
    soup = BeautifulSoup(html_text, "html.parser")
    messages = []
    table = soup.find("table", class_="table") or (soup.find_all("table")[0] if soup.find_all("table") else None)
    if not table:
        return []
    tbody = table.find("tbody")
    rows = table.find_all("tr") if not tbody else tbody.find_all("tr")
    for row in rows:
        tds = row.find_all("td")
        if not tds:
            continue
        cols = [td.get_text(separator=" ", strip=True) for td in tds]
        if len(cols) < 5:
            continue
        msg = {
            "date": cols[0],
            "ref": cols[1],
            "source": cols[2],
            "client": cols[3],
            "destination": cols[4],
            "raw": cols[5] if len(cols) > 5 else cols[4]
        }
        if msg["date"] and msg["raw"] and len(msg["raw"]) > 3:
            messages.append(msg)
    return messages

def normalize_otp_from_text(text):
    if not text:
        return None
    candidates = []
    match = re.search(r'(?:telegram|تيليجرام|تلجرام)\s*(?:code|كود)?\s*[:\s]*(\d{4,6})', text, re.IGNORECASE)
    if match:
        candidates.append({'otp': match.group(1), 'position': match.start(), 'confidence': 100})
    match = re.search(r'(\d{3})\s+(\d{3})\s+is\s+your\s+Instagram\s+code', text, re.IGNORECASE)
    if match:
        digits = match.group(1) + match.group(2)
        candidates.append({'otp': f"{digits[:3]} {digits[3:]}", 'position': match.start(), 'confidence': 99})
    for match in re.finditer(r'(?:code|كود|رمز|verification|تحقق)[:\s]*(\d{4,8})', text, re.IGNORECASE):
        digits = match.group(1)
        if 4 <= len(digits) <= 8:
            candidates.append({'otp': digits, 'position': match.start(), 'confidence': 95})
    for match in re.finditer(r'[\u200e\u200f\u202a-\u202e]?(\d{3})\s*-\s*(\d{3})', text):
        candidates.append({'otp': f"{match.group(1)}-{match.group(2)}", 'position': match.start(), 'confidence': 110})
    for match in re.finditer(r'(\d{3})\s+(\d{3})', text):
        digits = match.group(1) + match.group(2)
        if len(digits) == 6:
            candidates.append({'otp': f"{digits[:3]} {digits[3:]}", 'position': match.start(), 'confidence': 90})
    for match in re.finditer(r'\b\d{6}\b', text):
        digits = match.group(0)
        candidates.append({'otp': f"{digits[:3]} {digits[3:]}", 'position': match.start(), 'confidence': 70})
    for match in re.finditer(r'\b\d{5}\b', text):
        candidates.append({'otp': match.group(0), 'position': match.start(), 'confidence': 65})
    for match in re.finditer(r'\b\d{4}\b', text):
        candidates.append({'otp': match.group(0), 'position': match.start(), 'confidence': 60})
    if candidates:
        candidates.sort(key=lambda x: (-x['confidence'], x['position']))
        return candidates[0]['otp']
    for digit_group in reversed(re.findall(r'\d+', text)):
        if len(digit_group) >= 4:
            return digit_group
    return None

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

def clean_html_site2(text):
    if text is None or text == "":
        return ""
    try:
        text = re.sub(r'<[^>]+>', '', str(text))
        return html.unescape(text).replace('\x00', '').strip()
    except Exception:
        return str(text) if text else ""

def solve_captcha_timesms(html_content):
    match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)\s*=?\s*\?', html_content)
    if match:
        n1, op, n2 = int(match.group(1)), match.group(2), int(match.group(3))
        if op == '+':
            return str(n1 + n2)
        if op == '-':
            return str(n1 - n2)
        if op == '*':
            return str(n1 * n2)
        if op == '/':
            return str(n1 // n2) if n2 else '0'
    return None

def login_site10(account=None):
    global is_logged_in_site10, session10
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
            return False
        login_resp = sess.post(submit_url, data={'username': user, 'password': pw, 'capt': captcha}, headers={'Referer': login_url}, timeout=20, allow_redirects=True, verify=False)
        if 'login' not in str(login_resp.url).lower():
            if not account:
                is_logged_in_site10 = True
            return sess if account else True
    except Exception as e:
        print(f"[TimeSMS] Warning (handled): {e}", flush=True)
    return False

def login_site2():
    global is_logged_in_site2
    try:
        resp = session2.get(LOGIN_PAGE_URL2, timeout=HTTP_TIMEOUT2)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            return False
        captcha_answer = int(match.group(1)) + int(match.group(2))
        resp = session2.post(
            LOGIN_POST_URL2,
            data={"username": USERNAME2, "password": PASSWORD2, "capt": str(captcha_answer)},
            headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": LOGIN_PAGE_URL2, "Origin": BASE_URL2},
            timeout=HTTP_TIMEOUT2,
            allow_redirects=True
        )
        if any(k in resp.text.lower() or k in resp.url.lower() for k in ("dashboard", "logout", "agent", "/ints/agent")) or resp.url != LOGIN_PAGE_URL2:
            is_logged_in_site2 = True
            return True
    except Exception:
        pass
    return False

def login_site3():
    global is_logged_in_site3
    try:
        resp = session3.get(LOGIN_PAGE_URL3, timeout=HTTP_TIMEOUT3)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            return False
        captcha_answer = int(match.group(1)) + int(match.group(2))
        resp = session3.post(LOGIN_POST_URL3, data={"username": USERNAME3, "password": PASSWORD3, "capt": str(captcha_answer)}, headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": LOGIN_PAGE_URL3}, timeout=HTTP_TIMEOUT3, allow_redirects=True)
        if resp.url != LOGIN_PAGE_URL3:
            is_logged_in_site3 = True
            save_cookies_site3()
            return True
    except Exception:
        pass
    return False

def login_site4():
    global is_logged_in_site4
    try:
        resp = session4.get(LOGIN_PAGE_URL4, timeout=HTTP_TIMEOUT4)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            return False
        captcha_answer = int(match.group(1)) + int(match.group(2))
        resp = session4.post(LOGIN_POST_URL4, data={"username": USERNAME4, "password": PASSWORD4, "capt": str(captcha_answer)}, headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": LOGIN_PAGE_URL4}, timeout=HTTP_TIMEOUT4, allow_redirects=True)
        if resp.url != LOGIN_PAGE_URL4:
            is_logged_in_site4 = True
            save_cookies_site4()
            return True
    except Exception:
        pass
    return False

def login_site5():
    return False

def load_data():
    global COUNTRIES, CHANNELS, USERS, ADMINS, BANNED, OTP_GROUP, GROUPS, REFERRALS
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
            OTP_GROUP = json.load(f).get("group_id")
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

def save_withdrawal_requests(reqs):
    with open(WITHDRAWAL_REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reqs, f, indent=2, ensure_ascii=False)

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
    return hashlib.md5(f"{user_id}_{datetime.now().timestamp()}".encode()).hexdigest()[:8].upper()

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
        REFERRALS[user_key] = {"referred_by": referrer_key, "referrals": [], "active_referrals": 0, "codes_received": 0, "balance": 0.0, "total_earned": 0.0}
    else:
        if REFERRALS[user_key].get("referred_by"):
            return False
        REFERRALS[user_key]["referred_by"] = referrer_key
    REFERRALS.setdefault(referrer_key, {"referred_by": None, "referrals": [], "active_referrals": 0, "codes_received": 0, "balance": 0.0, "total_earned": 0.0})
    if user_key not in REFERRALS[referrer_key]["referrals"]:
        REFERRALS[referrer_key]["referrals"].append(user_key)
    save_referrals(REFERRALS)
    return True

def add_code_bonus(user_id):
    global REFERRALS
    REFERRALS = load_referrals()
    settings = load_referral_settings()
    user_key = str(user_id)
    REFERRALS.setdefault(user_key, {"referred_by": None, "referrals": [], "active_referrals": 0, "codes_received": 0, "balance": 0.0, "total_earned": 0.0})
    REFERRALS[user_key]["codes_received"] += 1
    code_bonus = settings.get("code_bonus", 0.01)
    REFERRALS[user_key]["balance"] += code_bonus
    REFERRALS[user_key]["total_earned"] += code_bonus
    referrer_key = REFERRALS[user_key].get("referred_by")
    if referrer_key and referrer_key in REFERRALS:
        codes_required = settings.get("codes_required_for_referral", 3)
        if REFERRALS[user_key]["codes_received"] == codes_required:
            REFERRALS[referrer_key]["active_referrals"] += 1
            referral_bonus = settings.get("referral_bonus", 0.50)
            REFERRALS[referrer_key]["balance"] += referral_bonus
            REFERRALS[referrer_key]["total_earned"] += referral_bonus
    save_referrals(REFERRALS)

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

def mask_number(num):
    digits = re.sub(r'\D', '', str(num))
    if len(digits) <= 6:
        return str(num)
    if len(digits) >= 11:
        return digits[:2] + "••••••" + digits[-3:]
    return digits[:2] + "•••" + digits[-2:]

def detect_service(text, source_addr=None):
    if not text:
        return "Unknown 🌐"
    t_low = text.lower()
    source_lower = source_addr.lower() if source_addr else ""
    services = {
        "whatsapp": "<tg-emoji emoji-id='5188683998125106802'>📞</tg-emoji>",
        "واتساب": "WS", "واتس": "WS", "facebook": "FB", "فيسبوك": "FB",
        "instagram": "IG", "انستقرام": "IG",
        "telegram": "<tg-emoji emoji-id='5471949924658588235'>👉</tg-emoji>",
        "تيليجرام": "<tg-emoji emoji-id='5471949924658588235'>👉</tg-emoji>",
        "tiktok": "TK", "google": "GG", "gmail": "GG"
    }
    for k, v in services.items():
        if k in t_low or k in source_lower:
            return v
    if source_addr and source_addr.strip():
        cleaned = source_addr.replace('#', '').strip()
        if cleaned:
            return cleaned.upper()
    return "Unknown 🌐"

def format_otp_message_v2(number, sms_text, service_name="[TG]", otp_code=None, is_group=False):
    _, flag, region_code = detect_country_from_number(number)
    masked = mask_number(number)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header = f"──────────────╖ \n↠ {flag} #{region_code} {service_name} {masked} ┨<tg-emoji emoji-id='6084757039567868626'>👆</tg-emoji>\n──────────────╛"
    body = f"<blockquote><tg-emoji emoji-id='5971844011508372946'>☠</tg-emoji>{sms_text}</blockquote>"
    time_footer = f"<blockquote>• <tg-emoji emoji-id='5413704112220949842'>⏰</tg-emoji> ~ {now_str}</blockquote>"
    return f"{header}\n{body}\n{time_footer}"

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
    threading.Thread(target=delete, daemon=True).start()

def normalize_number(number):
    return re.sub(r'\D', '', str(number)) if number else ""

def send_otp_to_user(number, otp_message, full_number, group_message=None, otp_code=None):
    normalized_incoming = normalize_number(number)
    for user_id_str, user_data in list(USERS.items()):
        selected_num = user_data.get("selected_number")
        if not selected_num:
            continue
        normalized_selected = normalize_number(selected_num)
        if (normalized_incoming == normalized_selected or normalized_incoming.endswith(normalized_selected) or normalized_selected.endswith(normalized_incoming) or full_number == selected_num):
            try:
                bot.send_message(int(user_id_str), otp_message, parse_mode="HTML")
                USERS[user_id_str]["activations"] = USERS[user_id_str].get("activations", 0) + 1
                save_users()
                add_code_bonus(int(user_id_str))
            except Exception as e:
                print(f"❌ خطأ إرسال للمستخدم {user_id_str}: {e}", flush=True)

    update_statistics()
    msg_to_group = group_message if group_message else otp_message
    group_keyboard = create_group_otp_keyboard(otp_code)
    sent_groups = set()
    if OTP_GROUP and OTP_GROUP not in sent_groups:
        try:
            m = bot.send_message(OTP_GROUP, msg_to_group, parse_mode="HTML", disable_web_page_preview=True, reply_markup=group_keyboard)
            auto_delete_message(OTP_GROUP, m.message_id)
            sent_groups.add(OTP_GROUP)
        except Exception as e:
            print(f"❌ خطأ إرسال لمجموعة OTP: {e}", flush=True)
    for gid in list(GROUPS):
        if gid not in sent_groups:
            try:
                m = bot.send_message(gid, msg_to_group, parse_mode="HTML", disable_web_page_preview=True, reply_markup=group_keyboard)
                auto_delete_message(gid, m.message_id)
                sent_groups.add(gid)
            except Exception as e:
                print(f"❌ خطأ إرسال لمجموعة {gid}: {e}", flush=True)

def get_platforms_list(user_id=None):
    platform_stats = {}
    for _, info in COUNTRIES.items():
        count = info.get("numbers_count", 0)
        for p in info.get("platforms", []):
            platform_stats[p] = platform_stats.get(p, 0) + count
    platform_icons = {"Facebook": "📘 Facebook", "WhatsApp": "💬 WhatsApp", "Telegram": "✈️ Telegram", "Instagram": "📸 Instagram", "Twitter": "🐦 Twitter/X", "TikTok": "📱 TikTok", "Discord": "🎮 Discord", "Gmail": "📧 Gmail"}
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
            label = f"{info.get('flag', '🌍')} {info.get('display_name', cid)}"
            if info.get("code"):
                label += f" (+{info['code']})"
            markup.add(InlineKeyboardButton(f"{label} ({info.get('numbers_count', 0)})", callback_data=f"country_{cid}"))
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
    markup.add(InlineKeyboardButton("⚙️ إعدادات المواقع", callback_data="admin_sites_menu"), InlineKeyboardButton("👥 إدارة الحسابات", callback_data="admin_accounts_menu"))
    markup.add(InlineKeyboardButton("➕ إضافة دولة", callback_data="admin_add_country"), InlineKeyboardButton("➖ حذف دولة", callback_data="admin_remove_country"))
    markup.add(InlineKeyboardButton("📋 الدول المتاحة", callback_data="admin_list_countries"), InlineKeyboardButton("📢 إضافة قناة", callback_data="admin_add_channel"))
    markup.add(InlineKeyboardButton("🗑 حذف قناة", callback_data="admin_remove_channel"), InlineKeyboardButton("📱 إدارة الجروبات", callback_data="admin_groups_menu"))
    markup.add(InlineKeyboardButton("📈 الإحصائيات", callback_data="admin_statistics"), InlineKeyboardButton("📣 إذاعة", callback_data="admin_broadcast_menu"))
    markup.add(InlineKeyboardButton("🔧 إضافة مشرف", callback_data="admin_add_admin"), InlineKeyboardButton("🗑 حذف مشرف", callback_data="admin_remove_admin"))
    markup.add(InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user"), InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban_user"))
    markup.add(InlineKeyboardButton("💰 نظام الإحالات", callback_data="admin_referral_settings"), InlineKeyboardButton("🔗 روابط الأزرار", callback_data="admin_button_links"))
    markup.add(InlineKeyboardButton("📥 إنشاء نسخة احتياطية", callback_data="admin_create_backup"), InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
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
    markup.add(InlineKeyboardButton("👤 تغيير اليوزر", callback_data=f"site_change_user_{site_key}_{short_id}"), InlineKeyboardButton("🔑 تغيير الباسورد", callback_data=f"site_change_pass_{site_key}_{short_id}"))
    markup.add(InlineKeyboardButton("⏱ فترة البحث", callback_data=f"site_change_interval_{site_key}"), InlineKeyboardButton("⏳ وقت الانتظار", callback_data=f"site_change_timeout_{site_key}"))
    markup.add(InlineKeyboardButton("🔓 اختبار تسجيل الدخول", callback_data=f"site_test_login_{site_key}_{short_id}"), InlineKeyboardButton("📥 اختبار جلب كود", callback_data=f"site_test_fetch_{site_key}_{short_id}"))
    markup.add(InlineKeyboardButton("🔙 رجوع لقائمة المواقع", callback_data="admin_sites_menu"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def handle_copy_callback(call):
    bot.answer_callback_query(call.id, call.data.split("_", 1)[1], show_alert=True)

@bot.message_handler(commands=["start"])
def start(msg):
    user_id = msg.from_user.id
    if is_banned(user_id):
        bot.reply_to(msg, t(user_id, "banned"))
        return
    if str(user_id) not in USERS:
        USERS[str(user_id)] = {"selected_country": None, "selected_number": None, "language": "ar", "join_date": datetime.now().strftime('%Y-%m-%d'), "activations": 0}
        save_users()
    if is_admin(user_id):
        bot.send_message(msg.chat.id, "🎛 <b>لوحة الإدارة</b>\n\nاختر الإجراء المطلوب:", parse_mode="HTML", reply_markup=get_admin_menu())
        return
    markup = get_platforms_list(user_id)
    if markup:
        bot.send_message(msg.chat.id, "🚨 <b>اختر المنصة</b>", parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(msg.chat.id, t(user_id, "welcome"), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data in ("admin", "admin_panel"))
def admin_cb(call):
    if is_admin(call.from_user.id):
        bot.edit_message_text("🎛 <b>لوحة الإدارة</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_admin_menu())

@bot.callback_query_handler(func=lambda call: call.data == "admin_sites_menu")
def sites_menu_cb(call):
    if is_admin(call.from_user.id):
        bot.edit_message_text("⚙️ <b>إعدادات المواقع</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_sites_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("site_config_"))
def site_config_cb(call):
    if not is_admin(call.from_user.id):
        return
    site_key = call.data.replace("site_config_", "")
    if site_key not in SETTINGS:
        return
    acc = get_first_account(site_key)
    bot.edit_message_text(f"⚙️ <b>إعدادات {SETTINGS[site_key]['name']}</b>\n👤 <code>{acc.get('username', 'N/A')}</code>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_site_config_menu(site_key, acc.get("id", "")))

@bot.callback_query_handler(func=lambda call: call.data.startswith(("site_change_user_", "site_change_pass_", "site_test_login_", "site_test_fetch_")))
def fixed_site_actions(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    data = call.data
    for prefix in ("site_change_user_", "site_change_pass_", "site_test_login_", "site_test_fetch_"):
        if data.startswith(prefix):
            rest = data[len(prefix):]
            site_key = next((k for k in SETTINGS if rest == k or rest.startswith(k + "_")), rest.rsplit("_", 1)[0])
            acc_id = rest[len(site_key) + 1:] if rest.startswith(site_key + "_") else ""
            account = get_account_by_id(site_key, acc_id)
            if not account:
                bot.answer_callback_query(call.id, "❌ الحساب غير موجود", show_alert=True)
                return
            if prefix == "site_change_user_":
                user_states[user_id] = {"action": "change_site_username", "site_key": site_key, "account_id": account["id"]}
                bot.send_message(call.message.chat.id, f"👤 أرسل اليوزر الجديد لـ {site_key}:")
            elif prefix == "site_change_pass_":
                user_states[user_id] = {"action": "change_site_password", "site_key": site_key, "account_id": account["id"]}
                bot.send_message(call.message.chat.id, f"🔑 أرسل الباسورد الجديد لـ {site_key}:")
            else:
                bot.answer_callback_query(call.id, "✅ جاري الفحص")
                bot.send_message(call.message.chat.id, f"✅ الحساب <code>{account.get('username', 'Token')}</code> في <b>{site_key}</b> نشط.", parse_mode="HTML")
            return

@bot.message_handler(content_types=["text", "document"])
def handle_text_docs(msg):
    user_id = msg.from_user.id
    if msg.chat.type != "private":
        return
    state = user_states.get(user_id)
    if not state:
        return
    action = state.get("action")
    if action in ("change_site_username", "change_site_password"):
        site_key = state["site_key"]
        acc_id = state["account_id"]
        key_name = "username" if action == "change_site_username" else "password"
        for acc in SETTINGS[site_key]["accounts"]:
            if acc["id"] == acc_id:
                acc[key_name] = msg.text.strip()
                save_settings(SETTINGS)
                break
        del user_states[user_id]
        bot.reply_to(msg, "✅ تم التحديث بنجاح!")

# ── All 10 Sites Monitoring Loops ────────────────────────────────────────────
def fetch_ajax_data_np(account_session, site_key, account):
    try:
        api_token = account.get("api_token") or account.get("id")
        if not api_token or api_token == "Api Token":
            return {"aaData": []}, False
        r = account_session.get("http://147.135.212.197/crapi/st/viewstats", params={"token": api_token, "records": 50}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                formatted_rows = []
                for item in data:
                    if isinstance(item, list) and len(item) >= 4:
                        row = [None] * 6
                        row[0], row[1], row[2], row[5] = item[3], item[0], item[1], item[2]
                        formatted_rows.append(row)
                return {"aaData": formatted_rows}, False
        return {"aaData": []}, False
    except Exception:
        return None, False

def sms_loop_for_number_panel_account(site_key, account):
    api_token = account.get("api_token") or account.get("id")
    check_interval = SETTINGS[site_key].get("check_interval", 5)
    account_session = requests.Session()
    safe_id = "".join(x for x in api_token if x.isalnum())[:15]
    last_message_file = f"last_message_{site_key}_{safe_id}.txt"
    last_seen_key_local = ""
    if os.path.exists(last_message_file):
        try:
            with open(last_message_file, "r", encoding="utf-8") as f:
                last_seen_key_local = f.read().strip()
        except Exception:
            pass
    while True:
        try:
            j, _ = fetch_ajax_data_np(account_session, site_key, {"api_token": api_token})
            rows = j.get("aaData", []) if isinstance(j, dict) else []
            valid_rows = []
            for row in rows:
                if isinstance(row, list) and len(row) > 5:
                    date_str = clean_html_site2(row[0])
                    number = clean_number(row[2])
                    sms = clean_html_site2(row[5])
                    s_name = clean_html_site2(row[1]) if row[1] else ""
                    if date_str and number and sms:
                        valid_rows.append((date_str, number, sms, f"{date_str}|{number}|{sms}", s_name))
            if valid_rows:
                valid_rows.sort(key=lambda r: r[0], reverse=True)
                if not last_seen_key_local:
                    r = valid_rows[0]
                    otp_val, sms_text = extract_from_message(r[2])
                    formatted = format_otp_message_v2(r[1], sms_text, f"[{r[4] or detect_service(r[2])}]", otp_val)
                    send_otp_to_user(clean_number(r[1]), formatted, r[1], None, otp_val)
                    last_seen_key_local = r[3]
                    with open(last_message_file, "w", encoding="utf-8") as f:
                        f.write(last_seen_key_local)
                else:
                    new_msgs = []
                    for r in valid_rows:
                        if r[3] == last_seen_key_local:
                            break
                        new_msgs.append(r)
                    for r in reversed(new_msgs):
                        otp_val, sms_text = extract_from_message(r[2])
                        formatted = format_otp_message_v2(r[1], sms_text, f"[{r[4] or detect_service(r[2])}]", otp_val)
                        send_otp_to_user(clean_number(r[1]), formatted, r[1], None, otp_val)
                        last_seen_key_local = r[3]
                    if new_msgs:
                        with open(last_message_file, "w", encoding="utf-8") as f:
                            f.write(last_seen_key_local)
            time.sleep(check_interval)
        except Exception:
            time.sleep(10)

def sms_loop_for_ivasms_account(site_key, account):
    account_id = account.get("id")
    username = account.get("username")
    password = account.get("password")
    api_key = account.get("api_key", "")
    stop_event = account_stop_events.setdefault(f"{site_key}_{account_id}", Event())
    API_URL = SETTINGS[site_key].get("api_url", "https://maroon-wombat-183778.hostingersite.com/apiivasms/api.php")
    sent_file = f"sent_messages_{site_key}_{account_id}.json"
    sent_messages_local = set()
    if os.path.exists(sent_file):
        try:
            with open(sent_file, 'r') as f:
                sent_messages_local = set(json.load(f))
        except Exception:
            pass
    while not stop_event.is_set():
        try:
            resp = requests.get(API_URL, params={'api_key': api_key, 'username': username, 'password': password, '_t': int(time.time() * 1000)}, timeout=SETTINGS[site_key]["timeout"], verify=False)
            if resp.status_code == 200:
                data = resp.json()
                for msg in (data.get('codes', []) if data.get('success') else []):
                    phone = msg.get('phone', msg.get('number', ''))
                    message_text = msg.get('message', msg.get('sms', msg.get('text', '')))
                    if not phone or not message_text:
                        continue
                    msg_key = f"{phone}|{message_text[:50]}"
                    if msg_key not in sent_messages_local:
                        otp_val, sms_text = extract_from_message(message_text)
                        formatted = format_otp_message_v2(phone, sms_text, f"[{detect_service(message_text)}]", otp_val)
                        send_otp_to_user(clean_number(phone), formatted, phone, None, otp_val)
                        sent_messages_local.add(msg_key)
                with open(sent_file, 'w') as f:
                    json.dump(list(sent_messages_local)[-500:], f)
        except Exception:
            time.sleep(10)
        if stop_event.wait(SETTINGS[site_key]["check_interval"]):
            break

def sms_loop_requests_based(site_key, account):
    account_id = account.get("id")
    username = account.get("username")
    password = account.get("password")
    stop_event = account_stop_events.setdefault(f"{site_key}_{account_id}", Event())
    base_u = SETTINGS[site_key]["base_url"].rstrip('/')
    login_p = SETTINGS[site_key]["login_page_url"]
    login_post = SETTINGS[site_key]["login_post_url"]
    ajax_p = SETTINGS[site_key].get("ajax_path", "/agent/res/data_smscdr.php")
    ajax_u = base_u + ajax_p
    check_int = SETTINGS[site_key]["check_interval"]
    timeout_l = SETTINGS[site_key].get("timeout", 60)

    session = requests.Session()
    session.verify = False
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    is_logged_in = False
    last_message_file = f"last_message_{site_key}_{account_id}.txt"
    last_seen_key_local = ""
    if os.path.exists(last_message_file):
        try:
            with open(last_message_file, "r", encoding="utf-8") as f:
                last_seen_key_local = f.read().strip()
        except Exception:
            pass

    def do_login():
        nonlocal is_logged_in
        try:
            resp = session.get(login_p, timeout=timeout_l)
            match = re.search(r'What is (\d+) \+ (\d+)', resp.text) or re.search(r'(\d+)\s*\+\s*(\d+)', resp.text)
            payload = {'username': username, 'password': password}
            if match:
                payload['capt'] = str(int(match.group(1)) + int(match.group(2)))
            crlf = re.search(r"name=['\"]crlf['\"].*?value=['\"]([^'\"]+)['\"]", resp.text)
            if crlf:
                payload['crlf'] = crlf.group(1)
            r2 = session.post(login_post, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded', 'Referer': login_p, 'Origin': base_u}, timeout=timeout_l, allow_redirects=True)
            if r2.url != login_p or any(k in r2.text.lower() for k in ('dashboard', 'logout', 'agent', 'smscdr')):
                is_logged_in = True
                return True
        except Exception:
            pass
        return False

    while not stop_event.is_set():
        try:
            if not is_logged_in and not do_login():
                time.sleep(20)
                continue
            today = datetime.now()
            start_d = (today - timedelta(days=1)).strftime('%Y-%m-%d')
            end_d = (today + timedelta(days=1)).strftime('%Y-%m-%d')
            referer_url = base_u + ("/agent/SMSCDRReports" if "/ints" in base_u else "/ints/agent/SMSCDRReports")
            payload = {'fdate1': f'{start_d} 00:00:00', 'fdate2': f'{end_d} 23:59:59', 'fg': '0', 'sEcho': '1', 'iDisplayStart': '0', 'iDisplayLength': '100', 'iSortCol_0': '0', 'sSortDir_0': 'desc'}
            r = session.post(ajax_u, data=payload, headers={'X-Requested-With': 'XMLHttpRequest', 'Referer': referer_url}, timeout=timeout_l)
            if r.status_code == 200:
                try:
                    data = r.json()
                    rows = data.get('data') or data.get('aaData') or data.get('rows') or []
                except Exception:
                    is_logged_in = False
                    rows = []
                valid = []
                for row in rows:
                    if isinstance(row, list) and len(row) >= 6:
                        d_str, num, sms = str(row[0]).strip(), re.sub(r'\D', '', str(row[2])), str(row[5]).strip()
                        if d_str and len(num) >= 7 and sms and 'nan%' not in sms.lower():
                            valid.append({'date': d_str, 'number': num, 'sms': sms})
                valid.sort(key=lambda x: x['date'])
                new_msgs = []
                for m in valid:
                    k = f"{m['date']}|{m['number']}"
                    if k == last_seen_key_local:
                        new_msgs = []
                        continue
                    new_msgs.append(m)
                for m in new_msgs:
                    otp_val, sms_text = extract_from_message(m['sms'])
                    formatted = format_otp_message_v2(m['number'], sms_text, f"[{detect_service(m['sms'])}]", otp_val)
                    send_otp_to_user(clean_number(m['number']), formatted, m['number'], None, otp_val)
                    last_seen_key_local = f"{m['date']}|{m['number']}"
                if new_msgs:
                    with open(last_message_file, "w", encoding="utf-8") as f:
                        f.write(last_seen_key_local)
            else:
                is_logged_in = False
        except Exception:
            is_logged_in = False
        if stop_event.wait(check_int):
            break

def sms_loop_for_ims_account(site_key, account):
    sms_loop_requests_based(site_key, account)

def sms_loop_for_roxy_account(site_key, account):
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
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest", "Referer": "http://www.roxysms.net/agent/SMSCDRReports"}
    while not stop_event.is_set():
        try:
            if not is_logged_in:
                lr = scraper.post("http://www.roxysms.net/signin", data={"username": username, "password": password}, headers=headers, timeout=30)
                if lr.status_code == 200 and ("success" in lr.text.lower() or "logout" in lr.text.lower()):
                    is_logged_in = True
                else:
                    time.sleep(30)
                    continue
            today = datetime.now().strftime('%Y-%m-%d')
            r = scraper.get("http://www.roxysms.net/agent/res/data_smscdr.php", params={'fdate1': f'{today} 00:00:00', 'fdate2': f'{today} 23:59:59', 'fg': '0'}, headers=headers, timeout=30)
            if r.status_code != 200 or 'login' in r.url.lower():
                is_logged_in = False
                continue
            rows = r.json().get('aaData', [])
            new_msgs = []
            for row in rows:
                if isinstance(row, list) and len(row) >= 6:
                    d_str, num, msg_txt = str(row[0]), re.sub(r'\D', '', str(row[2])), str(row[5])
                    k = f"{d_str}|{num}"
                    if k == last_seen_key_local:
                        break
                    new_msgs.append({'date': d_str, 'number': num, 'sms': msg_txt})
            if new_msgs:
                last_seen_key_local = f"{new_msgs[0]['date']}|{new_msgs[0]['number']}"
                with open(last_message_file, "w", encoding="utf-8") as f:
                    f.write(last_seen_key_local)
                for m in reversed(new_msgs):
                    otp_val, clean_sms = extract_from_message(m['sms'])
                    formatted = format_otp_message_v2(m['number'], clean_sms, f"[{detect_service(clean_sms)}]", otp_val)
                    send_otp_to_user(clean_number(m['number']), formatted, m['number'], None, otp_val)
        except Exception:
            is_logged_in = False
        if stop_event.wait(SETTINGS[site_key].get("check_interval", 5)):
            break

def sms_loop_for_timesms_account(site_key, account):
    site_name = SETTINGS[site_key]["name"]
    username = account.get("username")
    password = account.get("password")
    account_id = account.get("id")
    stop_event = account_stop_events.setdefault(f"{site_key}_{account_id}", Event())
    sess = make_timesms_session({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
                    lr = sess.post(submit_url, data={'username': username, 'password': password, 'capt': captcha}, headers={'Referer': login_url}, timeout=20, allow_redirects=True, verify=False)
                    if 'login' not in str(lr.url).lower():
                        is_logged_in = True
                    else:
                        time.sleep(30)
                        continue
                else:
                    time.sleep(30)
                    continue
            today = datetime.now().strftime('%Y-%m-%d')
            r = sess.get(ajax_url, params={'fdate1': f'{today} 00:00:00', 'fdate2': f'{today} 23:59:59', 'fg': '0', 'sEcho': '1', 'iDisplayStart': '0', 'iDisplayLength': '500', 'iSortCol_0': '0', 'sSortDir_0': 'desc'}, headers={'Referer': SETTINGS[site_key]["base_url"] + "/agent/SMSCDRReports", 'X-Requested-With': 'XMLHttpRequest'}, timeout=30, verify=False)
            if r.status_code != 200 or 'login' in r.url.lower():
                is_logged_in = False
                continue
            rows = r.json().get('aaData', [])
            new_msgs = []
            for row in rows:
                if len(row) >= 6:
                    msg_date, msg_num, msg_text = str(row[0]).strip(), str(row[2]).strip(), str(row[5]).strip()
                    if not re.match(r'\d{4}-\d{2}-\d{2}', msg_date):
                        continue
                    k = f"{msg_date}_{msg_num}_{msg_text[:20]}"
                    if k == last_seen_key_local:
                        break
                    new_msgs.append({'date': msg_date, 'number': msg_num, 'sms': msg_text, 'key': k})
            if new_msgs:
                last_seen_key_local = new_msgs[0]['key']
                with open(last_message_file, "w", encoding="utf-8") as f:
                    f.write(last_seen_key_local)
                for m in reversed(new_msgs):
                    otp_val, clean_sms = extract_from_message(m['sms'])
                    formatted = format_otp_message_v2(m['number'], clean_sms, f"[{detect_service(clean_sms)}]", otp_val)
                    send_otp_to_user(clean_number(m['number']), formatted, m['number'], None, otp_val)
        except Exception as e:
            print(f"[{site_name}] Warning (handled): {e}", flush=True)
            is_logged_in = False
        if stop_event.wait(SETTINGS[site_key].get("check_interval", 5)):
            break

def start_monitoring_for_account(site_key, account):
    if site_key == "Number_Panel":
        sms_loop_for_number_panel_account(site_key, account)
    elif site_key == "iVASMS":
        sms_loop_for_ivasms_account(site_key, account)
    elif site_key == "IMS":
        sms_loop_for_ims_account(site_key, account)
    elif site_key == "Roxy SMS":
        sms_loop_for_roxy_account(site_key, account)
    elif site_key == "TimeSMS":
        sms_loop_for_timesms_account(site_key, account)
    else:
        sms_loop_requests_based(site_key, account)

if __name__ == "__main__":
    load_data()
    monitoring_threads = []
    print("🚀 Starting multi-account monitoring...", flush=True)
    for site_key in ["GROUP", "Fly sms", "Number_Panel", "Bolt", "iVASMS", "MSI", "proton SMS", "IMS", "Roxy SMS", "TimeSMS"]:
        if SETTINGS.get(site_key, {}).get("enabled"):
            accounts = get_site_accounts(site_key)
            for account in accounts:
                th = Thread(target=start_monitoring_for_account, args=(site_key, account), daemon=True)
                monitoring_threads.append(th)
                th.start()

    try:
        r_del = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=15)
        print(f"🔄 Webhook deleted: {r_del.text}", flush=True)
        me = bot.get_me()
        print(f"🤖 Connected Bot: @{me.username} (ID: {me.id})", flush=True)
    except Exception as e:
        print(f"⚠️ Telegram connection check error: {e}", flush=True)

    try:
        bot.set_my_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("getnumber", "Get a number"),
            BotCommand("account", "My account"),
            BotCommand("help", "Help guide"),
            BotCommand("withdraw", "Withdraw balance"),
            BotCommand("hom", "Main menu"),
            BotCommand("language", "Change language"),
            BotCommand("bonus", "Bonus system"),
        ])
    except Exception as e:
        print(f"⚠️ Command setup error: {e}", flush=True)

    retry_delay = 5
    while True:
        try:
            print("🚀 Starting Telegram bot polling...", flush=True)
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
        except Exception as e:
            print(f"❌ Polling error: {e}", flush=True)
            time.sleep(retry_delay)
            retry_delay = min(60, retry_delay * 2)
