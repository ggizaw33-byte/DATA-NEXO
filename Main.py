# ɴᴇXᴏ SᴛᴏƦᴇ V11 FIXED
# ɴᴇXᴏ SᴛᴏƦᴇ VERSION V11
# ============================================================
# ɴᴇXᴏ SᴛᴏƦᴇ - Native Python Telegram Bot | VERSION 10
# Converted from NEXO_STORE_TPY_FIXED_5000PLUS.txt
#
# Library: pyTelegramBotAPI (telebot)
# Storage: SQLite
#
# Install:
#   pip install pyTelegramBotAPI
#
# Run:
#   export BOT_TOKEN="YOUR_BOT_TOKEN"
#   python NEXO_STORE_PYTHON_FULL.py
#
# Windows:
#   set BOT_TOKEN=YOUR_BOT_TOKEN
#   python NEXO_STORE_PYTHON_FULL.py
# ============================================================

import os
import html
import psycopg2
from psycopg2.extras import RealDictCursor
import secrets
import time
import logging
from urllib.parse import quote
import json
from urllib.parse import urlparse
from datetime import datetime, timezone
from threading import Lock

import telebot
from telebot import types

# ---------------- CONFIG ----------------

BOT_TOKEN = os.getenv("BOT_TOKEN", "8971587718:AAHNjr96A88iiIU5iFxhyDFWEIwBV9rZ56M").strip()

MASTER_ADMIN = "7712522579"
BOT_USERNAME = "Nexo_store_bot"
BOT_URL = "http://t.me/Nexo_store_bot"

# =========================
# V11 SETTINGS
# =========================
FORCE_JOIN_KEY = "force_join_enabled"
FORCE_JOIN_CHANNELS_KEY = "force_join_channels"
FORCE_JOIN_STYLE_KEY = "force_join_style"
WELCOME_MESSAGE_KEY = "welcome_message"

DEFAULT_WELCOME_MESSAGE = (
    "👑 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ɴᴇXᴏ SᴛᴏƦᴇ!\n\n"
    "🛍️ ʏᴏᴜʀ ᴅɪɢɪᴛᴀʟ sʜᴏᴘ, ᴍᴀᴅᴇ sɪᴍᴘʟᴇ.\n\n"
    "💎 ǫᴜᴀʟɪᴛʏ\n"
    "⚡ ғᴀsᴛ sᴇʀᴠɪᴄᴇ\n"
    "🔒 sᴇᴄᴜʀᴇ ᴛʀᴀɴsᴀᴄᴛɪᴏɴs\n"
    "🕹ᴛʀᴜsᴛᴇᴅ | ᴠᴇʀɪғʏᴅ sᴛᴏʀᴇ\n\n"
    "👇 ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ."
)


STORE_NAME = "ɴᴇXᴏ SᴛᴏƦᴇ"
SUPPORT = "https://t.me/IRORE0"
SUPPORT_ACCOUNT = "@IRORE0"
MAIN_GROUP = "@iron_sold"
WELCOME_IMAGE = "https://n.uguu.se/EibgDrGy.jpg"

DB_FILE = os.getenv("NEXO_STORE_DB", "nexo_store.db")

# V10 features:
# - Bot identity: @Nexo_store_bot
# - Support: @IRORE0
# - Group product/sold BUY buttons use exact product deep-links.
# - /start product_<id> opens the exact product page.
# - Contextual Telegram inline button colors: blue/green/red.


if not BOT_TOKEN:
    raise SystemExit(
        "BOT_TOKEN is not set.\n"
        "Linux/macOS: export BOT_TOKEN='YOUR_TOKEN'\n"
        "Windows: set BOT_TOKEN=YOUR_TOKEN"
    )

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
db_lock = Lock()

# Telegram Bot API supports real inline-button styles: primary (blue),
# success (green), and danger (red). Gold is mapped to primary because it is
# not an official Bot API button style.
def Button(text, **kwargs):
    theme = str(get_setting("button_theme", "primary")).lower() if "get_setting" in globals() else "primary"
    style = {
        "blue": "primary", "primary": "primary",
        "green": "success", "success": "success",
        "red": "danger", "danger": "danger",
        "gold": "primary",
    }.get(theme, "primary")
    kwargs.setdefault("style", style)
    try:
        return types.InlineKeyboardButton(str(text), **kwargs)
    except TypeError:
        # Compatibility with older pyTelegramBotAPI versions.
        kwargs.pop("style", None)
        btn = types.InlineKeyboardButton(str(text), **kwargs)
        try:
            setattr(btn, "style", style)
        except Exception:
            pass
        return btn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ---------------- DATABASE ----------------
# Supabase PostgreSQL connection.
# Set SUPABASE_DB_URL in the hosting environment. The old SQLite file is no
# longer used; all bot data is stored in the Supabase project.

SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "").strip()


def db():
    if not SUPABASE_DB_URL:
        raise SystemExit(
            "SUPABASE_DB_URL is not set.\n"
            "Set it to your Supabase PostgreSQL connection string."
        )
    conn = psycopg2.connect(SUPABASE_DB_URL, sslmode="require")
    return _PostgresConnection(conn)


class _PostgresConnection:
    """Small compatibility wrapper so the existing bot SQL can keep using
    conn.execute(...), fetchone(), fetchall(), and '?' placeholders.
    """

    def __init__(self, conn):
        self._conn = conn

    @staticmethod
    def _sql(sql):
        # Existing Main.py uses SQLite-style '?' placeholders.
        return sql.replace("?", "%s")

    def execute(self, sql, params=None):
        cur = self._conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(self._sql(sql), params or ())
        return cur

    def cursor(self):
        return self._conn.cursor(cursor_factory=RealDictCursor)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def init_db():
    """Initialize/verify the Supabase schema and seed application defaults.

    The schema is created in Supabase, so this function deliberately does not
    recreate or migrate the old local SQLite database.
    """
    with db_lock:
        conn = db()
        try:
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    first_name TEXT DEFAULT '',
                    username TEXT DEFAULT '',
                    registered_at TEXT,
                    balance NUMERIC DEFAULT 0,
                    order_count INTEGER DEFAULT 0,
                    deposit_count INTEGER DEFAULT 0,
                    withdrawal_count INTEGER DEFAULT 0,
                    referral_count INTEGER DEFAULT 0,
                    referrer TEXT DEFAULT '',
                    ban TEXT DEFAULT ''
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id TEXT PRIMARY KEY
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT DEFAULT ''
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    price NUMERIC NOT NULL,
                    currency TEXT DEFAULT 'ETB',
                    added_stock INTEGER DEFAULT 0,
                    available_stock INTEGER DEFAULT 0,
                    total_stock INTEGER DEFAULT 0,
                    info TEXT DEFAULT '',
                    color TEXT DEFAULT 'blue',
                    status TEXT DEFAULT 'active',
                    created_by TEXT DEFAULT '',
                    created_at TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS product_stock (
                    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    product_id TEXT NOT NULL,
                    item TEXT NOT NULL,
                    sold INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT,
                    price NUMERIC DEFAULT 0,
                    quantity INTEGER DEFAULT 1,
                    total NUMERIC DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    delivery TEXT DEFAULT '',
                    created_at TEXT,
                    completed_at TEXT DEFAULT ''
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS deposits (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT DEFAULT '',
                    amount NUMERIC DEFAULT 0,
                    transaction_id TEXT DEFAULT '',
                    screenshot TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    approved_by TEXT DEFAULT '',
                    rejected_by TEXT DEFAULT '',
                    rejection_reason TEXT DEFAULT '',
                    redeem_code TEXT DEFAULT '',
                    product_id TEXT DEFAULT '',
                    product_name TEXT DEFAULT ''
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS withdrawals (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT DEFAULT '',
                    amount NUMERIC DEFAULT 0,
                    account TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    approved_by TEXT DEFAULT '',
                    rejected_by TEXT DEFAULT ''
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    type TEXT,
                    amount NUMERIC DEFAULT 0,
                    rate NUMERIC DEFAULT 0,
                    total NUMERIC DEFAULT 0,
                    payment_information TEXT DEFAULT '',
                    receiving_account TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    approved_by TEXT DEFAULT '',
                    rejected_by TEXT DEFAULT ''
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS redeem_codes (
                    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    amount NUMERIC NOT NULL DEFAULT 0,
                    max_claims INTEGER NOT NULL DEFAULT 1,
                    claims_count INTEGER NOT NULL DEFAULT 0,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_by TEXT DEFAULT '',
                    created_at TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS redeem_claims (
                    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    code_id BIGINT NOT NULL,
                    user_id TEXT NOT NULL,
                    deposit_id TEXT DEFAULT '',
                    bonus NUMERIC NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'reserved',
                    created_at TEXT,
                    approved_at TEXT DEFAULT '',
                    UNIQUE(code_id, user_id)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS states (
                    user_id TEXT PRIMARY KEY,
                    state TEXT DEFAULT '',
                    data TEXT DEFAULT ''
                )
            """)

            cur.execute(
                "INSERT INTO admins(user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING",
                (MASTER_ADMIN,)
            )

            defaults = {
                "telebirr_number": "",
                "account_manager": "",
                "usdt_buy_rate": "0",
                "usdt_sell_rate": "0",
                "referral_reward": "0",
                "usdt_sell_address": "",
                "group_log_enabled": "1",
                "group_log_photo": "",
                "button_theme": "primary",
                FORCE_JOIN_KEY: "0",
                FORCE_JOIN_CHANNELS_KEY: "[]",
                FORCE_JOIN_STYLE_KEY: "blue",
                WELCOME_MESSAGE_KEY: DEFAULT_WELCOME_MESSAGE,
            }
            for k, v in defaults.items():
                cur.execute(
                    "INSERT INTO settings(key,value) VALUES (%s,%s) "
                    "ON CONFLICT(key) DO NOTHING",
                    (k, v)
                )

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

# ---------------- HELPERS ----------------

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def money(value):
    try:
        n = float(value)
        return str(int(n)) if n == int(n) else f"{n:.2f}"
    except Exception:
        return "0"

def product_currency(product):
    try:
        value = str(product["currency"] or "ETB").strip().upper()
    except Exception:
        value = "ETB"
    return value or "ETB"

def product_money(product_or_price, currency=None):
    if currency is None and hasattr(product_or_price, "keys"):
        currency = product_currency(product_or_price)
        price = product_or_price["price"]
    else:
        price = product_or_price
        currency = str(currency or "ETB").strip().upper() or "ETB"
    return f"{money(price)} {esc(currency)}"

def safe_float(value, default=0.0):
    try:
        return float(str(value).strip())
    except Exception:
        return default

def safe_int(value, default=0):
    try:
        return int(str(value).strip())
    except Exception:
        return default

def new_id(prefix):
    return f"{prefix}_{secrets.token_hex(6)}"

def esc(value):
    return html.escape(str(value or ""))

def uname(user):
    return user.username or ""

def is_admin(user_id):
    uid = str(user_id)
    if uid == str(MASTER_ADMIN):
        return True
    with db_lock:
        conn = db()
        row = conn.execute(
            "SELECT 1 FROM admins WHERE user_id=?",
            (uid,)
        ).fetchone()
        conn.close()
    return row is not None

def admin_ids():
    with db_lock:
        conn = db()
        rows = conn.execute("SELECT user_id FROM admins").fetchall()
        conn.close()
    return [str(r["user_id"]) for r in rows]

def get_setting(key, default=""):
    with db_lock:
        conn = db()
        row = conn.execute(
            "SELECT value FROM settings WHERE key=?",
            (key,)
        ).fetchone()
        conn.close()
    return row["value"] if row else default

def set_setting(key, value):
    with db_lock:
        conn = db()
        conn.execute(
            "INSERT INTO settings(key,value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value))
        )
        conn.commit()
        conn.close()

def ensure_user(user):
    uid = str(user.id)
    with db_lock:
        conn = db()
        row = conn.execute(
            "SELECT id FROM users WHERE id=?",
            (uid,)
        ).fetchone()

        if not row:
            conn.execute("""
                INSERT INTO users(
                    id, first_name, username, registered_at
                ) VALUES(?,?,?,?)
            """, (
                uid,
                user.first_name or "",
                user.username or "",
                now()
            ))
        else:
            conn.execute("""
                UPDATE users
                SET first_name=?, username=?
                WHERE id=?
            """, (
                user.first_name or "",
                user.username or "",
                uid
            ))
        conn.commit()
        conn.close()
    return uid

def get_user(user_id):
    with db_lock:
        conn = db()
        row = conn.execute(
            "SELECT * FROM users WHERE id=?",
            (str(user_id),)
        ).fetchone()
        conn.close()
    return dict(row) if row else None

def change_balance(user_id, amount):
    with db_lock:
        conn = db()
        conn.execute(
            "UPDATE users SET balance=balance+? WHERE id=?",
            (float(amount), str(user_id))
        )
        conn.commit()
        conn.close()

def set_state(user_id, state, data=""):
    with db_lock:
        conn = db()
        conn.execute("""
            INSERT INTO states(user_id,state,data)
            VALUES(?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                state=excluded.state,
                data=excluded.data
        """, (str(user_id), state, data))
        conn.commit()
        conn.close()

def get_state(user_id):
    with db_lock:
        conn = db()
        row = conn.execute(
            "SELECT state,data FROM states WHERE user_id=?",
            (str(user_id),)
        ).fetchone()
        conn.close()
    if not row:
        return "", ""
    return row["state"], row["data"]

def clear_state(user_id):
    with db_lock:
        conn = db()
        conn.execute("DELETE FROM states WHERE user_id=?", (str(user_id),))
        conn.commit()
        conn.close()

def banned(user_id):
    if is_admin(user_id):
        return False
    row = get_user(user_id)
    return bool(row and row["ban"] == "ok")

def require_user(message):
    ensure_user(message.from_user)
    if banned(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "🚫 <b>Your account is currently banned.</b>\n\n"
            "Please contact: @IRORE0"
        )
        return False
    return True

def user_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("👤 PROFILE", callback_data="profile"),
        Button("🛍️ SHOP", callback_data="shop")
    )
    kb.row(
        Button("💳 WALLET", callback_data="wallet"),
        Button("📦 ORDERS", callback_data="orders")
    )
    kb.row(
        Button("💵 USDT BUY SELL", callback_data="usdt"),
        Button("🆘 SUPPORT", url=SUPPORT)
    )
    return kb

def home_text():
    return v11_welcome_message()

def home_keyboard(user_id):
    kb = user_keyboard()
    if is_admin(user_id):
        kb.add(Button(
            "🛠️ ADMIN PANEL", callback_data="admin"
        ))
    return kb

def send_home(chat_id, user_id):
    try:
        bot.send_photo(
            chat_id,
            WELCOME_IMAGE,
            caption=home_text(),
            reply_markup=home_keyboard(user_id)
        )
    except Exception:
        bot.send_message(
            chat_id,
            home_text(),
            reply_markup=home_keyboard(user_id)
        )

def back_home():
    return types.InlineKeyboardMarkup(
        [[Button("🏠 HOME", callback_data="home", style="primary")]]
    )

def back_admin():
    return types.InlineKeyboardMarkup(
        [[Button("🔙 ADMIN", callback_data="admin")]]
    )

def admin_only(user_id):
    return is_admin(user_id)


def mask_account(value):
    value = str(value or "").strip()
    if len(value) <= 6:
        return value
    if len(value) <= 12:
        return value[:3] + "****" + value[-3:]
    return value[:6] + "****" + value[-4:]


def button_theme_prefix(theme):
    return {
        "blue": "🔵",
        "green": "🟢",
        "red": "🔴",
        "gold": "🟡",
    }.get(str(theme).lower(), "🔵")


def build_url_button(text, url):
    kb = types.InlineKeyboardMarkup()
    theme = get_setting("button_theme", "primary")
    style = {"blue":"primary", "primary":"primary", "green":"success", "success":"success", "red":"danger", "danger":"danger", "gold":"primary"}.get(theme, "primary")
    kb.add(Button(text, url=url, style=style))
    return kb


def product_deep_link(product_id):
    """Return a Telegram deep-link that opens the exact product page."""
    return f"{BOT_URL}?start=product_{product_id}"


def product_url_button(text, product_id, style="success"):
    """Colored BUY button that opens the exact product in the bot."""
    kb = types.InlineKeyboardMarkup()
    try:
        kb.add(Button(text, url=product_deep_link(product_id), style=style))
    except Exception:
        kb.add(Button(text, url=product_deep_link(product_id)))
    return kb


def group_log_keyboard():
    return build_url_button("🏪 OPEN STORE", BOT_URL)


def check_group_permissions():
    """Verify that the bot can post in the configured group."""
    try:
        me = bot.get_me()
        member = bot.get_chat_member(MAIN_GROUP, me.id)
        status = str(getattr(member, "status", ""))
        if status in ("creator", "administrator"):
            can_post = getattr(member, "can_post_messages", None)
            if can_post is False:
                return False, "Bot is an admin but does not have permission to post messages."
            return True, "OK"
        if status in ("member", "restricted"):
            can_send = getattr(member, "can_send_messages", None)
            if can_send is False:
                return False, "Bot is not allowed to send messages in the group."
            return True, "OK"
        return False, f"Bot membership status is {status or 'unknown'}. Add the bot to the group and make it an admin."
    except Exception as e:
        return False, str(e)

def post_to_main_group(text, reply_markup=None, photo=None):
    """Post text/photo to MAIN_GROUP after checking bot permissions."""
    ready, reason = check_group_permissions()
    if not ready:
        logging.error("MAIN_GROUP posting unavailable: %s", reason)
        notify_admins(
            "⚠️ <b>GROUP MESSAGE FAILED</b>\n\n"
            f"📢 Group: <code>{esc(MAIN_GROUP)}</code>\n"
            f"❌ Reason: <code>{esc(reason)}</code>\n\n"
            "Make the bot an administrator and allow it to send messages.",
            back_admin()
        )
        return False
    try:
        if photo:
            bot.send_photo(MAIN_GROUP, photo, caption=text, reply_markup=reply_markup)
        else:
            bot.send_message(MAIN_GROUP, text, reply_markup=reply_markup)
        return True
    except Exception as e:
        logging.warning("MAIN_GROUP post failed: %s", e)
        notify_admins(
            "⚠️ <b>GROUP MESSAGE ERROR</b>\n\n"
            f"📢 Group: <code>{esc(MAIN_GROUP)}</code>\n"
            f"❌ Error: <code>{esc(e)}</code>",
            back_admin()
        )
        return False

def send_group_log(text, photo_url=""):
    if get_setting("group_log_enabled", "1") != "1":
        return True
    photo_url = photo_url or get_setting("group_log_photo", "").strip()
    return post_to_main_group(text, reply_markup=group_log_keyboard(), photo=photo_url or None)


def send_broadcast_content(target, content, button_text="", button_url="", button_style=None):
    markup = None
    if button_text and button_url:
        markup = _broadcast_markup(button_text, button_url, button_style)

    ctype = content.get("type")
    value = content.get("file_id", "")
    caption = content.get("caption", "") or ""

    if target == "group":
        destinations = [MAIN_GROUP]
    else:
        with db_lock:
            conn = db()
            rows = conn.execute(
                "SELECT id FROM users WHERE ban!='ok'"
            ).fetchall()
            conn.close()
        destinations = [int(r["id"]) for r in rows]

    sent = failed = 0
    for dest in destinations:
        try:
            if ctype == "text":
                bot.send_message(dest, caption, reply_markup=markup)
            elif ctype == "photo":
                bot.send_photo(dest, value, caption=caption, reply_markup=markup)
            elif ctype == "video":
                bot.send_video(dest, value, caption=caption, reply_markup=markup)
            elif ctype == "document":
                bot.send_document(dest, value, caption=caption, reply_markup=markup)
            elif ctype == "audio":
                bot.send_audio(dest, value, caption=caption, reply_markup=markup)
            elif ctype == "animation":
                bot.send_animation(dest, value, caption=caption, reply_markup=markup)
            else:
                raise ValueError("Unsupported broadcast type")
            sent += 1
        except Exception as e:
            failed += 1
            logging.warning("Broadcast delivery failed to %s: %s", dest, e)

    return sent, failed


def broadcast_menu(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("👤 ALL BOT USERS", callback_data="broadcast_target_users"),
        Button("👥 GROUP ONLY", callback_data="broadcast_target_group"),
    )
    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    bot.send_message(
        chat_id,
        "📢 <b>BROADCAST SYSTEM</b>\n\n"
        "Choose where to publish:\n"
        "👤 <b>ALL BOT USERS</b> — sends to every registered user\n"
        "👥 <b>GROUP ONLY</b> — publishes only to the main group",
        reply_markup=kb
    )


def broadcast_content_prompt(chat_id, user_id, target):
    set_state(user_id, "broadcast_content", target)
    kb = types.InlineKeyboardMarkup()
    kb.add(Button("❌ CANCEL", callback_data="admin"))
    bot.send_message(
        chat_id,
        "📨 <b>BROADCAST CONTENT</b>\n\n"
        "Send one of these methods:\n"
        "📝 Text\n"
        "🖼️ Photo\n"
        "🎬 Video\n"
        "📄 Document\n"
        "🎵 Audio\n"
        "🎞️ Animation\n\n"
        "After receiving it, I will ask whether to add a button.",
        reply_markup=kb
    )


def broadcast_button_prompt(chat_id, user_id, content, target):
    set_state(
        user_id,
        "broadcast_button",
        json.dumps({"target": target, "content": content}, ensure_ascii=False)
    )
    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("✅ YES, ADD BUTTON", callback_data="broadcast_button_yes"),
        Button("❌ NO BUTTON", callback_data="broadcast_button_no"),
    )
    bot.send_message(
        chat_id,
        "🔘 <b>ADD BUTTON?</b>\n\n"
        "Do you want an inline button on the broadcast?",
        reply_markup=kb
    )


def _broadcast_markup(button_text="", button_url="", button_style=None):
    if not button_text or not button_url:
        return None
    kb = types.InlineKeyboardMarkup()
    style = button_style or get_setting("button_theme", "primary")
    # Build directly with the requested official style.
    style = {"blue":"primary", "green":"success", "red":"danger", "gold":"primary"}.get(style, style)
    try:
        kb.add(types.InlineKeyboardButton(button_text, url=button_url, style=style))
    except TypeError:
        btn = types.InlineKeyboardButton(button_text, url=button_url)
        try: setattr(btn, "style", style)
        except Exception: pass
        kb.add(btn)
    return kb


def send_broadcast_preview(chat_id, obj):
    content = obj.get("content", {})
    markup = _broadcast_markup(obj.get("button_text", ""), obj.get("button_url", ""), obj.get("button_style"))
    ctype = content.get("type")
    value = content.get("file_id", "")
    caption = content.get("caption", "") or ""
    try:
        if ctype == "text":
            bot.send_message(chat_id, "👁️ <b>BROADCAST PREVIEW</b>\n\n" + caption, reply_markup=markup)
        elif ctype == "photo":
            bot.send_photo(chat_id, value, caption="👁️ <b>BROADCAST PREVIEW</b>\n\n" + caption, reply_markup=markup)
        elif ctype == "video":
            bot.send_video(chat_id, value, caption="👁️ <b>BROADCAST PREVIEW</b>\n\n" + caption, reply_markup=markup)
        elif ctype == "document":
            bot.send_document(chat_id, value, caption="👁️ <b>BROADCAST PREVIEW</b>\n\n" + caption, reply_markup=markup)
        elif ctype == "audio":
            bot.send_audio(chat_id, value, caption="👁️ <b>BROADCAST PREVIEW</b>\n\n" + caption, reply_markup=markup)
        elif ctype == "animation":
            bot.send_animation(chat_id, value, caption="👁️ <b>BROADCAST PREVIEW</b>\n\n" + caption, reply_markup=markup)
        else:
            raise ValueError("Unsupported preview type")

        kb = types.InlineKeyboardMarkup()
        kb.row(
            Button("📤 SHARE / SEND NOW", callback_data="broadcast_share"),
            Button("✏️ EDIT", callback_data="broadcast_edit")
        )
        kb.add(Button("❌ CANCEL", callback_data="broadcast_cancel"))
        bot.send_message(chat_id, "<b>Preview ready.</b>\nChoose an action below:", reply_markup=kb)
    except Exception as e:
        clear_state(chat_id)
        bot.send_message(chat_id, f"❌ Preview failed.\n\n{esc(e)}", reply_markup=back_admin())


def broadcast_finish(chat_id, user_id, target, content, button_text="", button_url="", button_style=None):
    sent, failed = send_broadcast_content(
        target, content, button_text, button_url, button_style
    )
    clear_state(user_id)
    target_name = "ALL BOT USERS" if target == "users" else "GROUP ONLY"
    bot.send_message(
        chat_id,
        "📢 <b>BROADCAST FINISHED</b>\n\n"
        f"🎯 Target: <b>{target_name}</b>\n"
        f"📨 Method: <b>{content.get('type','').upper()}</b>\n"
        f"🔘 Button: <b>{'YES' if button_text and button_url else 'NO'}</b>\n"
        f"✅ Sent: <b>{sent}</b>\n"
        f"❌ Failed: <b>{failed}</b>",
        reply_markup=back_admin()
    )


def notify_admins(text, markup=None):
    """Send admin notification to every registered admin and always include master."""
    sent = 0
    ids = admin_ids()
    if str(MASTER_ADMIN) not in ids:
        ids.append(str(MASTER_ADMIN))
    for aid in dict.fromkeys(ids):
        try:
            bot.send_message(int(aid), text, reply_markup=markup)
            sent += 1
        except Exception as e:
            logging.warning("Admin notify failed for %s: %s", aid, e)
    return sent

def notify_admins_photo(photo_file_id, caption, markup=None):
    """Send a photo (such as a deposit screenshot) to every admin."""
    sent = 0
    ids = admin_ids()
    if str(MASTER_ADMIN) not in ids:
        ids.append(str(MASTER_ADMIN))
    for aid in dict.fromkeys(ids):
        try:
            bot.send_photo(int(aid), photo_file_id, caption=caption, reply_markup=markup)
            sent += 1
        except Exception as e:
            logging.warning("Admin photo notify failed for %s: %s", aid, e)
    return sent

# ---------------- HOME / START ----------------
# ---------------- HOME / START ----------------



# =========================
# V11 FORCE JOIN + WELCOME HELPERS
# =========================

def v11_force_join_channels():
    value = get_setting(FORCE_JOIN_CHANNELS_KEY, "[]")
    if isinstance(value, list):
        items = value
    else:
        raw = str(value or "").strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            items = parsed if isinstance(parsed, list) else []
        except Exception:
            items = [x.strip().strip("'").strip('"') for x in raw.strip("[]").split(",") if x.strip()]
    return [str(x).strip() for x in items if str(x).strip()]

def v11_force_join_enabled():
    value = str(get_setting(FORCE_JOIN_KEY, "0")).strip().lower()
    return value in ("1", "true", "yes", "on", "enabled")

def v11_force_join_style():
    value = str(get_setting(FORCE_JOIN_STYLE_KEY, "primary")).lower()
    return {"blue": "primary", "green": "success", "red": "danger"}.get(value, "primary")

def v11_channel_join_url(channel):
    channel = str(channel).strip()
    if channel.startswith("https://t.me/") or channel.startswith("http://t.me/"):
        return channel
    if channel.startswith("@"):
        return "https://t.me/" + channel[1:]
    return "https://t.me/" + channel

def v11_channel_label(channel):
    channel = str(channel).strip()
    if channel.startswith("@"):
        return channel
    if "t.me/" in channel:
        return "@" + channel.rstrip("/").split("/")[-1]
    return channel

def v11_check_member(user_id, channel):
    try:
        target = channel
        member = bot.get_chat_member(target, int(user_id))
        status = getattr(member, "status", "")
        return status in ("creator", "administrator", "member") or (
            status == "restricted" and bool(getattr(member, "is_member", False))
        )
    except Exception:
        return False

def v11_all_channels_joined(user_id):
    channels = v11_force_join_channels()
    if not channels:
        return True
    return all(v11_check_member(user_id, ch) for ch in channels)

def v11_force_join_keyboard():
    kb = types.InlineKeyboardMarkup()
    style = v11_force_join_style()
    for ch in v11_force_join_channels():
        kb.add(Button("📢 JOIN " + v11_channel_label(ch), url=v11_channel_join_url(ch), style=style))
    kb.add(Button("✅ CHECK JOIN", callback_data="v11_check_join", style="success"))
    return kb

def v11_welcome_message():
    msg = get_setting(WELCOME_MESSAGE_KEY, DEFAULT_WELCOME_MESSAGE)
    return str(msg) if msg else DEFAULT_WELCOME_MESSAGE

def v11_show_start_gate(message):
    if not v11_force_join_enabled() or v11_all_channels_joined(message.from_user.id):
        return False
    bot.send_message(
        message.chat.id,
        "🔒 <b>CHANNEL JOIN REQUIRED</b>\n\n"
        "Please join all required channels below, then press <b>CHECK JOIN</b>.",
        parse_mode="HTML",
        reply_markup=v11_force_join_keyboard(),
    )
    return True

def v11_settings_keyboard():
    kb = types.InlineKeyboardMarkup()
    enabled = "🟢 ON" if v11_force_join_enabled() else "🔴 OFF"
    kb.add(Button("🔐 Force Join: " + enabled, callback_data="v11_force_join_menu", style="primary"))
    kb.add(Button("➕ Add Channel", callback_data="v11_force_join_add", style="success"))
    kb.add(Button("🗑 Remove Channel", callback_data="v11_force_join_remove", style="danger"))
    kb.add(Button("🎨 Join Button Color", callback_data="v11_force_join_style", style="primary"))
    kb.add(Button("✏️ Welcome Message", callback_data="v11_welcome_edit", style="primary"))
    kb.add(Button("⬅️ Back", callback_data="admin_settings", style="primary"))
    return kb

def v11_send_settings(chat_id):
    channels = v11_force_join_channels()
    channel_text = "\n".join("• " + v11_channel_label(x) for x in channels) or "• No channels added"
    text = (
        "⚙️ <b>V11 SETTINGS</b>\n\n"
        f"🔐 Force Join: <b>{'ON' if v11_force_join_enabled() else 'OFF'}</b>\n"
        f"🎨 Join Button: <b>{v11_force_join_style()}</b>\n\n"
        "📢 <b>Required Channels</b>\n"
        + channel_text
        + "\n\n"
        "✏️ <b>Welcome Message</b>\n"
        + v11_welcome_message()
    )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=v11_settings_keyboard())




# =========================
# V11 TEXT STATES
# =========================

def v11_handle_text_state(message):
    uid = message.from_user.id
    state, state_data = get_state(uid)
    if state not in ("v11_add_channel", "v11_welcome"):
        return False

    if not is_admin(uid):
        clear_state(uid)
        return True

    if state == "v11_add_channel":
        raw = str(message.text or "").strip()
        if not raw:
            bot.reply_to(message, "❌ Invalid channel.")
            return True
        if not (raw.startswith("@") or "t.me/" in raw):
            bot.reply_to(message, "❌ Send @username or a public t.me link for a Channel, Group, or Supergroup.")
            return True
        normalized = raw.rstrip("/")
        try:
            chat = bot.get_chat(normalized)
            chat_type = str(getattr(chat, "type", ""))
            if chat_type not in ("channel", "group", "supergroup"):
                bot.reply_to(message, "❌ This is not a Telegram Channel, Group, or Supergroup.")
                return True
        except Exception:
            bot.reply_to(message, "❌ Chat not found. Make sure the bot can access the public Channel/Group/Supergroup.")
            return True
        channels = v11_force_join_channels()
        if normalized not in channels:
            channels.append(normalized)
            set_setting(FORCE_JOIN_CHANNELS_KEY, json.dumps(channels, ensure_ascii=False))
            bot.send_message(message.chat.id, "✅ Channel/Group/Supergroup added successfully.")
        else:
            bot.send_message(message.chat.id, "ℹ️ This chat is already added.")
        clear_state(uid)
        v11_send_settings(message.chat.id)
        return True

    if state == "v11_welcome":
        raw = str(message.text or "").strip()
        if not raw:
            bot.reply_to(message, "❌ Welcome message cannot be empty.")
            return True
        set_setting(WELCOME_MESSAGE_KEY, raw)
        clear_state(uid)
        bot.send_message(message.chat.id, "✅ Welcome message updated.")
        v11_send_settings(message.chat.id)
        return True

    return False



@bot.message_handler(content_types=["text"], func=lambda m: bool(get_state(m.from_user.id) in ("v11_add_channel", "v11_welcome")))
def v11_text_state_router(message):
    v11_handle_text_state(message)


@bot.message_handler(commands=["start"])
def start(message):
    ensure_user(message.from_user)
    clear_state(message.from_user.id)

    if not is_admin(message.from_user.id) and v11_force_join_enabled() and not v11_all_channels_joined(message.from_user.id):
        v11_show_start_gate(message)
        return

    # Deep-link support:
    # http://t.me/Nexo_store_bot?start=product_<PRODUCT_ID>
    # Opens the selected product directly instead of only opening Home.
    parts = (message.text or "").split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else ""
    if payload.startswith("product_"):
        product_id = payload[len("product_"):].strip()
        if product_id:
            try:
                show_product(message.chat.id, message.from_user.id, product_id)
                return
            except Exception:
                logging.exception("Product deep-link failed for %s", product_id)

    send_home(message.chat.id, message.from_user.id)

# Native command aliases from the TPY project
@bot.message_handler(commands=[
    "profile", "shop", "product", "wallet", "orders",
    "deposit", "withdraw", "transactions", "usdt",
    "usdt_buy", "usdt_sell", "usdt_requests",
    "admin", "admin_products", "admin_add_product",
    "admin_add_stock", "admin_remove_stock",
    "admin_delete_product", "admin_edit_product",
    "admin_view_products", "admin_wallet",
    "admin_check_balance", "admin_add_balance",
    "admin_remove_balance", "admin_users", "admin_user",
    "admin_user_orders", "admin_user_add_balance",
    "admin_user_remove_balance", "admin_user_message",
    "admin_ban", "admin_unban", "admin_orders",
    "admin_deposits", "admin_withdrawals",
    "admin_broadcast", "admin_message_user",
    "admin_statistics", "admin_payment_settings",
    "admin_admins", "admin_settings"
])
def command_router(message):
    ensure_user(message.from_user)
    cmd = message.text.split()[0].split("@")[0].lstrip("/")

    if cmd == "profile":
        show_profile(message.chat.id, message.from_user.id)
    elif cmd == "shop":
        show_shop(message.chat.id, message.from_user.id)
    elif cmd == "product":
        show_shop(message.chat.id, message.from_user.id)
    elif cmd == "wallet":
        show_wallet(message.chat.id, message.from_user.id)
    elif cmd == "orders":
        show_orders(message.chat.id, message.from_user.id)
    elif cmd == "deposit":
        start_deposit(message.chat.id, message.from_user.id)
    elif cmd == "withdraw":
        start_withdraw(message.chat.id, message.from_user.id)
    elif cmd == "transactions":
        show_transactions(message.chat.id, message.from_user.id)
    elif cmd == "usdt":
        show_usdt(message.chat.id, message.from_user.id)
    elif cmd == "usdt_buy":
        start_usdt_buy(message.chat.id, message.from_user.id)
    elif cmd == "usdt_sell":
        start_usdt_sell(message.chat.id, message.from_user.id)
    elif cmd == "usdt_requests":
        show_usdt_requests(message.chat.id, message.from_user.id)
    elif cmd == "admin":
        show_admin(message.chat.id, message.from_user.id)
    else:
        admin_command(message, cmd)

# ---------------- USER PAGES ----------------

def show_profile(chat_id, user_id):
    row = get_user(user_id)
    if not row:
        return

    username = f"@{row['username']}" if row["username"] else "Not set"
    status = "BANNED" if row["ban"] == "ok" else "ACTIVE"

    text = (
        "👤 <b>PROFILE</b>\n\n"
        f"🆔 User ID: <code>{row['id']}</code>\n"
        f"👤 Username: {esc(username)}\n"
        f"📝 Name: {esc(row['first_name'])}\n"
        f"💰 Balance: <b>{money(row['balance'])}</b>\n"
        f"📦 Total Orders: {row['order_count']}\n"
        f"💳 Total Deposits: {row['deposit_count']}\n"
        f"📤 Withdrawals: {row['withdrawal_count']}\n"
        f"👥 Referral Count: {row['referral_count']}\n"
        f"📌 Account Status: {status}"
    )

    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("💳 WALLET", callback_data="wallet"),
        Button("📦 ORDERS", callback_data="orders")
    )
    kb.add(Button("🏠 HOME", callback_data="home", style="primary"))
    bot.send_message(chat_id, text, reply_markup=kb)

def show_shop(chat_id, user_id):
    with db_lock:
        conn = db()
        products = conn.execute("""
            SELECT * FROM products
            WHERE status='active' AND available_stock>0
            ORDER BY created_at DESC
        """).fetchall()
        conn.close()

    kb = types.InlineKeyboardMarkup()

    if not products:
        kb.add(Button("🏠 HOME", callback_data="home", style="primary"))
        bot.send_message(
            chat_id,
            "🛍️ <b>SHOP</b>\n\nThere are currently no products in stock.",
            reply_markup=kb
        )
        return

    product_buttons = []
    for p in products:
        style = {"blue":"primary", "green":"success", "red":"danger"}.get(str(p["color"] or "blue").lower(), "primary")
        product_buttons.append(Button(
            f"📦 {p['name']} — {product_money(p)}",
            callback_data=f"product_{p['id']}",
            style=style
        ))
    for i in range(0, len(product_buttons), 2):
        kb.row(*product_buttons[i:i+2])

    kb.add(Button("🏠 HOME", callback_data="home", style="primary"))
    bot.send_message(
        chat_id,
        "🛍️ <b>ɴᴇXᴏ SᴛᴏƦᴇ SHOP</b>\n\nSelect a product:",
        reply_markup=kb
    )

def show_product(chat_id, user_id, product_id):
    with db_lock:
        conn = db()
        p = conn.execute(
            "SELECT * FROM products WHERE id=?",
            (product_id,)
        ).fetchone()
        conn.close()

    if not p:
        bot.send_message(chat_id, "❌ Product not found.", reply_markup=back_home())
        return

    if p["status"] != "active":
        bot.send_message(chat_id, "❌ Product is inactive.", reply_markup=back_home())
        return

    text = (
        f"📦 <b>{esc(p['name'])}</b>\n\n"
        f"💰 Price: <b>{product_money(p)}</b>\n"
        f"📊 Available: <b>{p['available_stock']}</b>\n"
        f"📊 Total Stock: <b>{p['total_stock']}</b>\n\n"
        f"📝 {esc(p['info'])}"
    )

    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("🛒 BUY NOW", callback_data=f"buy_{product_id}", style="success"),
        Button("🔙 SHOP", callback_data="shop", style="primary")
    )
    kb.add(Button("🏠 HOME", callback_data="home", style="primary"))
    bot.send_message(chat_id, text, reply_markup=kb)

def start_buy(chat_id, user_id, product_id):
    with db_lock:
        conn = db()
        p = conn.execute(
            "SELECT * FROM products WHERE id=?",
            (product_id,)
        ).fetchone()
        conn.close()

    if not p or p["status"] != "active":
        bot.send_message(chat_id, "❌ Product unavailable.", reply_markup=back_home())
        return

    if int(p["available_stock"]) <= 0:
        bot.send_message(chat_id, "❌ Out of stock.", reply_markup=back_home())
        return

    user = get_user(user_id)
    if not user or float(user["balance"]) < float(p["price"]):
        start_product_payment(chat_id, user_id, p)
        return

    set_state(user_id, "confirm_buy", product_id)

    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("✅ CONFIRM", callback_data="confirm_buy"),
        Button("❌ CANCEL", callback_data=f"product_{product_id}")
    )
    bot.send_message(
        chat_id,
        f"🛒 <b>CONFIRM PURCHASE</b>\n\n"
        f"📦 Product: <b>{esc(p['name'])}</b>\n"
        f"💰 Price: <b>{product_money(p)}</b>\n"
        f"💳 Your balance: <b>{money(user['balance'])}</b>\n\n"
        "Confirm your order?",
        reply_markup=kb
    )

def confirm_buy(chat_id, user_id):
    state, product_id = get_state(user_id)
    if state != "confirm_buy":
        bot.send_message(chat_id, "❌ Purchase session expired.", reply_markup=back_home())
        return

    with db_lock:
        conn = db()
        p = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        user = conn.execute("SELECT * FROM users WHERE id=?", (str(user_id),)).fetchone()

        if not p or p["status"] != "active":
            conn.close(); clear_state(user_id)
            bot.send_message(chat_id, "❌ Product unavailable.", reply_markup=back_home())
            return
        if int(p["available_stock"]) <= 0:
            conn.close(); clear_state(user_id)
            bot.send_message(chat_id, "❌ Out of stock.", reply_markup=back_home())
            return
        if not user or float(user["balance"]) < float(p["price"]):
            balance = float(user["balance"]) if user else 0
            conn.close(); clear_state(user_id)
            bot.send_message(chat_id, f"❌ <b>Insufficient balance.</b>\n\n💰 Balance: {money(balance)}\n💵 Required: {product_money(p)}", reply_markup=back_home())
            return

        # Deduct the product price immediately because the user's balance covers it.
        conn.execute("UPDATE users SET balance=balance-? WHERE id=?", (float(p["price"]), str(user_id)))

        # Reserve one stock unit while the order waits for admin approval.
        stock = conn.execute("""
            SELECT id,item FROM product_stock
            WHERE product_id=? AND sold=0
            ORDER BY id ASC LIMIT 1
        """, (product_id,)).fetchone()
        delivery = stock["item"] if stock else ""
        if stock:
            conn.execute("UPDATE product_stock SET sold=2 WHERE id=?", (stock["id"],))

        order_id = new_id("ORD")
        conn.execute("""
            INSERT INTO orders(id,user_id,product_id,product_name,price,quantity,total,status,delivery,created_at,completed_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (order_id, str(user_id), product_id, p["name"], float(p["price"]), 1,
              float(p["price"]), "pending", delivery, now(), ""))
        conn.execute("UPDATE products SET available_stock=available_stock-1 WHERE id=?", (product_id,))
        conn.commit()
        conn.close()

    clear_state(user_id)
    order_admin_notify(order_id)
    bot.send_message(
        chat_id,
        "⏳ <b>ORDER SUBMITTED</b>\n\n"
        f"🧾 Order ID: <code>{order_id}</code>\n"
        f"📦 Product: <b>{esc(p['name'])}</b>\n"
        f"💰 Amount: <b>{product_money(p)}</b>\n"
        "📌 Status: <b>WAITING FOR ADMIN APPROVAL</b>\n\n"
        "Your order is reserved. You will receive the product after approval.",
        reply_markup=back_home()
    )


def order_admin_notify(order_id):
    with db_lock:
        conn = db()
        o = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        conn.close()
    if not o:
        return False

    user = get_user(o["user_id"])
    username = user["username"] if user else ""
    first_name = user["first_name"] if user else ""
    balance = user["balance"] if user else 0
    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("✅ APPROVE", callback_data=f"approve_order_{order_id}", style="success"),
        Button("❌ REJECT", callback_data=f"reject_order_{order_id}", style="danger")
    )
    text = (
        "🛒 <b>NEW PRODUCT ORDER — ACTION REQUIRED</b>\n\n"
        f"🧾 Order ID: <code>{esc(o['id'])}</code>\n"
        f"👤 User ID: <code>{esc(o['user_id'])}</code>\n"
        f"👤 Name: <b>{esc(first_name)}</b>\n"
        f"🔗 Username: @{esc(username) if username else 'Not set'}\n"
        f"💳 Current Balance: <b>{money(balance)}</b>\n"
        f"💵 Paid from Balance: <b>{money(o['total'])}</b>\n\n"
        f"📦 Product: <b>{esc(o['product_name'])}</b>\n"
        f"🔢 Quantity: <b>{o['quantity']}</b>\n"
        f"💰 Price: <b>{money(o['price'])}</b>\n"
        f"💵 Total: <b>{money(o['total'])}</b>\n"
        f"🔐 Reserved Product: <b>{'YES' if o['delivery'] else 'COUNTER STOCK'}</b>\n"
        f"🕒 Created: <code>{esc(o['created_at'])}</code>\n\n"
        "📌 Status: <b>PENDING</b>\n\n"
        "👇 <b>Choose an action:</b>"
    )
    sent = notify_admins(text, kb)
    if sent == 0:
        try:
            if post_to_main_group(text, reply_markup=kb):
                logging.warning("Order %s sent to MAIN_GROUP because no admin PM was reachable.", order_id)
                return True
            logging.error("Order %s could not notify admins or MAIN_GROUP.", order_id)
        except Exception as e:
            logging.error("Order group fallback failed: %s", e)
        return False
    return True


def approve_order(chat_id, admin_id, order_id):
    with db_lock:
        conn = db()
        o = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not o:
            conn.close(); bot.send_message(chat_id, "❌ Order not found.", reply_markup=back_admin()); return
        if o["status"] != "pending":
            conn.close(); bot.send_message(chat_id, "⚠️ Order already processed.", reply_markup=back_admin()); return
        # Balance was already deducted when the user confirmed the purchase.
        # Approval must NOT deduct it a second time.
        conn.execute("UPDATE users SET order_count=order_count+1 WHERE id=?", (o["user_id"],))
        conn.execute("UPDATE orders SET status='completed', completed_at=? WHERE id=?", (now(), order_id))
        if o["delivery"]:
            # Reserved item uses sold=2; finalize it as sold=1.
            conn.execute("""
                UPDATE product_stock SET sold=1
                WHERE product_id=? AND item=? AND sold=2
            """, (o["product_id"], o["delivery"]))
        conn.execute("""
            INSERT INTO transactions(id,user_id,type,amount,total,status,created_at,approved_by)
            VALUES(?,?,?,?,?,?,?,?)
        """, (new_id("TX"), o["user_id"], "purchase", float(o["price"]), float(o["total"]), "completed", now(), str(admin_id)))
        conn.commit()
        conn.close()

    clear_state(admin_id)
    try:
        msg = (
            "✅ <b>ORDER APPROVED</b>\n\n"
            f"🧾 Order ID: <code>{esc(o['id'])}</code>\n"
            f"📦 Product: <b>{esc(o['product_name'])}</b>\n"
            f"💰 Paid: <b>{money(o['total'])}</b>\n"
        )
        if o["delivery"]:
            msg += f"\n🔐 <b>Your Product:</b>\n<code>{esc(o['delivery'])}</code>"
        else:
            msg += "\n📌 Product delivery: <b>Contact support</b>"
        bot.send_message(int(o["user_id"]), msg, reply_markup=back_home())
    except Exception:
        pass

    product_sold_group_log(o)
    bot.send_message(chat_id, f"✅ <b>Order approved</b>\n\n🧾 <code>{esc(o['id'])}</code>", reply_markup=back_admin())


def reject_order(chat_id, admin_id, order_id):
    with db_lock:
        conn = db()
        o = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not o:
            conn.close(); bot.send_message(chat_id, "❌ Order not found.", reply_markup=back_admin()); return
        if o["status"] != "pending":
            conn.close(); bot.send_message(chat_id, "⚠️ Order already processed.", reply_markup=back_admin()); return
        conn.execute("UPDATE orders SET status='rejected', completed_at=? WHERE id=?", (now(), order_id))
        conn.execute("UPDATE products SET available_stock=available_stock+1 WHERE id=?", (o["product_id"],))
        conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (float(o["total"]), o["user_id"]))
        if o["delivery"]:
            conn.execute("UPDATE product_stock SET sold=0 WHERE product_id=? AND item=? AND sold=2", (o["product_id"], o["delivery"]))
        conn.commit()
        conn.close()

    try:
        bot.send_message(int(o["user_id"]),
            "❌ <b>ORDER REJECTED</b>\n\n"
            f"🧾 Order ID: <code>{esc(o['id'])}</code>\n"
            f"📦 Product: <b>{esc(o['product_name'])}</b>\n"
            f"💳 <b>{money(o['total'])}</b> has been refunded to your balance.\n\nPlease contact @IRORE0 if you need help.",
            reply_markup=back_home())
    except Exception:
        pass
    bot.send_message(chat_id, f"❌ <b>Order rejected</b>\n\n🧾 <code>{esc(o['id'])}</code>", reply_markup=back_admin())


def product_sold_group_log(order_row):
    o = order_row
    label = str(o["product_name"] or "")
    button_label = label if len(label) <= 44 else label[:41] + "..."
    text = (
        "🛒 <b>Someone just bought {}</b> × <b>{}</b> <b>from Bot!</b>"
    ).format(o["quantity"], esc(label))
    # Green success button for SOLD activity.
    # It still opens the exact product page for the next customer.
    return post_to_main_group(
        text,
        reply_markup=product_url_button(f"🛒 BUY {button_label}", o["product_id"], style="success")
    )


# ---------------- REDEEM CODE SYSTEM ----------------

def admin_redeem_menu(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.row(Button("➕ CREATE REDEEM", callback_data="redeem_create"), Button("📋 LIST CODES", callback_data="redeem_list"))
    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    bot.send_message(chat_id, "🎟️ <b>REDEEM CODE MANAGEMENT</b>", reply_markup=kb)


def redeem_create_start(chat_id, user_id):
    set_state(user_id, "redeem_create_code")
    bot.send_message(chat_id, "🎟️ <b>CREATE REDEEM CODE</b>\n\nSend the code. Example: <code>NEXO100</code>")


def redeem_validate(code, user_id, reserve=False, deposit_id=""):
    code = str(code or "").strip().upper()
    if not code:
        return False, "❌ Redeem code is empty.", None
    with db_lock:
        conn=db()
        rc=conn.execute("SELECT * FROM redeem_codes WHERE upper(code)=?", (code,)).fetchone()
        if not rc:
            conn.close(); return False, "❌ Invalid redeem code.", None
        if not rc["active"]:
            conn.close(); return False, "❌ This redeem code is inactive.", None
        if int(rc["claims_count"]) >= int(rc["max_claims"]):
            conn.close(); return False, "❌ This redeem code has reached its claim limit.", None
        old=conn.execute("SELECT * FROM redeem_claims WHERE code_id=? AND user_id=?", (rc["id"], str(user_id))).fetchone()
        if old and old["status"] in ("reserved","approved"):
            conn.close(); return False, "❌ You have already used this redeem code.", None
        if reserve:
            if old:
                conn.execute("DELETE FROM redeem_claims WHERE id=?", (old["id"],))
            conn.execute("INSERT INTO redeem_claims(code_id,user_id,deposit_id,bonus,status,created_at) VALUES(?,?,?,?,?,?)",
                         (rc["id"],str(user_id),str(deposit_id or ""),float(rc["amount"]),"reserved",now()))
            conn.execute("UPDATE redeem_codes SET claims_count=claims_count+1 WHERE id=?", (rc["id"],))
            conn.commit()
        conn.close()
    return True, "✅ Redeem code valid.", dict(rc)


def redeem_direct(chat_id, user_id, code):
    code = str(code or "").strip().upper()
    if not code:
        bot.send_message(chat_id, "❌ Send a redeem code.", reply_markup=back_home())
        return
    with db_lock:
        conn = db()
        rc = conn.execute("SELECT * FROM redeem_codes WHERE upper(code)=?", (code,)).fetchone()
        if not rc:
            conn.close(); bot.send_message(chat_id, "❌ Invalid redeem code.", reply_markup=back_home()); return
        if not rc["active"]:
            conn.close(); bot.send_message(chat_id, "❌ This redeem code is inactive.", reply_markup=back_home()); return
        if int(rc["claims_count"]) >= int(rc["max_claims"]):
            conn.close(); bot.send_message(chat_id, "❌ This redeem code has reached its claim limit.", reply_markup=back_home()); return
        old = conn.execute("SELECT 1 FROM redeem_claims WHERE code_id=? AND user_id=? AND status IN ('reserved','approved')", (rc["id"], str(user_id))).fetchone()
        if old:
            conn.close(); bot.send_message(chat_id, "❌ You have already used this redeem code.", reply_markup=back_home()); return
        wallet_id = "WALLET_" + secrets.token_hex(8)
        try:
            conn.execute("INSERT INTO redeem_claims(code_id,user_id,deposit_id,bonus,status,created_at,approved_at) VALUES(?,?,?,?,?,?,?)", (rc["id"], str(user_id), wallet_id, float(rc["amount"]), "approved", now(), now()))
            cur = conn.execute("UPDATE redeem_codes SET claims_count=claims_count+1 WHERE id=? AND claims_count < max_claims", (rc["id"],))
            if cur.rowcount != 1:
                raise RuntimeError("Redeem claim limit reached")
            conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (float(rc["amount"]), str(user_id)))
            conn.execute("INSERT INTO transactions(id,user_id,type,amount,status,created_at,approved_by) VALUES(?,?,?,?,?,?,?)", (new_id("RTX"), str(user_id), "redeem", float(rc["amount"]), "completed", now(), "system"))
            conn.commit()
        except Exception as e:
            conn.rollback(); conn.close()
            bot.send_message(chat_id, "❌ Redeem failed. Please try again.", reply_markup=back_home())
            logging.exception("Direct redeem failed: %s", e)
            return
        conn.close()
    newbal = get_user(user_id)["balance"]
    bot.send_message(chat_id, f"🎉 <b>REDEEM SUCCESSFUL</b>\n\n🎟️ Code: <code>{esc(code)}</code>\n💰 Bonus: <b>{money(rc['amount'])} ETB</b>\n💳 Balance: <b>{money(newbal)} ETB</b>", reply_markup=back_home())


def redeem_list(chat_id):
    with db_lock:
        conn=db(); rows=conn.execute("SELECT * FROM redeem_codes ORDER BY id DESC LIMIT 50").fetchall(); conn.close()
    text="🎟️ <b>REDEEM CODES</b>\n\n"
    if not rows: text+="No redeem codes."
    else:
        for r in rows:
            status="ON" if r["active"] else "OFF"
            text+=f"🎟️ <code>{esc(r['code'])}</code> | 💰 {money(r['amount'])} ETB | 👥 {r['claims_count']}/{r['max_claims']} | {status}\n"
    bot.send_message(chat_id,text,reply_markup=back_admin())

# ---------------- WALLET / DEPOSIT / WITHDRAW ----------------

def show_wallet(chat_id, user_id):
    user = get_user(user_id)
    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("💳 DEPOSIT", callback_data="deposit", style="primary"),
        Button("📤 WITHDRAW", callback_data="withdraw", style="danger")
    )
    kb.row(
        Button("🧾 TRANSACTIONS", callback_data="transactions"),
        Button("📦 ORDERS", callback_data="orders")
    )
    kb.add(Button("🎟️ REDEEM CODE", callback_data="redeem"))
    kb.add(Button("🏠 HOME", callback_data="home", style="primary"))

    bot.send_message(
        chat_id,
        "💳 <b>WALLET</b>\n\n"
        f"💰 Balance: <b>{money(user['balance'])}</b>\n"
        f"📦 Orders: {user['order_count']}\n"
        f"💳 Deposits: {user['deposit_count']}\n"
        f"📤 Withdrawals: {user['withdrawal_count']}",
        reply_markup=kb
    )

def start_deposit(chat_id, user_id):
    set_state(user_id, "deposit_amount")
    bot.send_message(
        chat_id,
        "💳 <b>DEPOSIT</b>\n\n"
        "Send the amount you want to deposit.\n"
        "Example: <code>100</code>",
        reply_markup=back_home()
    )

def create_deposit(user_id, amount, redeem_code="", product_id="", product_name=""):
    dep_id = new_id("DEP")
    user = get_user(user_id)
    with db_lock:
        conn = db()
        conn.execute("""
            INSERT INTO deposits(
                id,user_id,username,amount,status,created_at,redeem_code,product_id,product_name
            ) VALUES(?,?,?,?,?,?,?,?,?)
        """, (
            dep_id,
            str(user_id),
            user["username"] if user else "",
            amount,
            "pending",
            now(),
            str(redeem_code or "").upper(),
            str(product_id or ""),
            str(product_name or "")
        ))
        conn.execute(
            "UPDATE users SET deposit_count=deposit_count+1 WHERE id=?",
            (str(user_id),)
        )
        conn.commit()
        conn.close()
    return dep_id

def start_product_payment(chat_id, user_id, product):
    """Create a payment request for the missing product amount and collect proof."""
    user = get_user(user_id)
    balance = float(user["balance"]) if user else 0.0
    due = max(0.0, float(product["price"]) - balance)
    if due <= 0:
        return False

    dep_id = create_deposit(user_id, due, product_id=product["id"], product_name=product["name"])
    set_state(user_id, "deposit_proof", dep_id)

    number = get_setting("telebirr_number", "Not configured")
    manager = get_setting("account_manager", "Not configured")
    kb = types.InlineKeyboardMarkup()
    kb.add(Button("🔙 PRODUCT", callback_data=f"product_{product['id']}", style="primary"))
    bot.send_message(
        chat_id,
        "💳 <b>PAYMENT REQUIRED</b>\n\n"
        f"📦 Product: <b>{esc(product['name'])}</b>\n"
        f"💵 Product Price: <b>{product_money(product)}</b>\n"
        f"💰 Your Balance: <b>{money(balance)} ETB</b>\n"
        f"💳 Amount to Pay: <b>{money(due)} ETB</b>\n\n"
        "📱 <b>Manager Account / Phone Number:</b>\n"
        f"<code>{esc(number)}</code>\n\n"
        "👤 <b>Account Manager:</b>\n"
        f"<b>{esc(manager)}</b>\n\n"
        "📸 After payment, <b>send the screenshot here</b>.\n"
        "⏳ Admin will review it and update your balance.\n"
        "Then you can return to the product and BUY.",
        reply_markup=kb
    )
    return True


def start_withdraw(chat_id, user_id):
    user = get_user(user_id)
    if float(user["balance"]) <= 0:
        bot.send_message(chat_id, "❌ Your balance is empty.", reply_markup=back_home())
        return

    set_state(user_id, "withdraw_amount")
    bot.send_message(
        chat_id,
        f"📤 <b>WITHDRAW</b>\n\n"
        f"💰 Available: <b>{money(user['balance'])}</b>\n\n"
        "Send the withdrawal amount.",
        reply_markup=back_home()
    )

def create_withdrawal(user_id, amount, account):
    wid = new_id("WDR")
    user = get_user(user_id)

    with db_lock:
        conn = db()
        conn.execute("""
            INSERT INTO withdrawals(
                id,user_id,username,amount,account,status,created_at
            ) VALUES(?,?,?,?,?,?,?)
        """, (
            wid,
            str(user_id),
            user["username"] if user else "",
            amount,
            account,
            "pending",
            now()
        ))
        conn.commit()
        conn.close()

    return wid

def show_transactions(chat_id, user_id):
    with db_lock:
        conn = db()
        rows = conn.execute("""
            SELECT * FROM transactions
            WHERE user_id=?
            ORDER BY created_at DESC LIMIT 20
        """, (str(user_id),)).fetchall()
        conn.close()

    text = "🧾 <b>TRANSACTIONS</b>\n\n"
    if not rows:
        text += "No transactions."
    else:
        for r in rows:
            text += (
                f"🧾 <code>{esc(r['id'])}</code>\n"
                f"Type: {esc(r['type'])}\n"
                f"Amount: {money(r['amount'])}\n"
                f"Status: {esc(r['status'])}\n"
                f"Time: {esc(r['created_at'])}\n\n"
            )

    bot.send_message(chat_id, text, reply_markup=back_home())

def show_orders(chat_id, user_id):
    with db_lock:
        conn = db()
        rows = conn.execute("""
            SELECT * FROM orders
            WHERE user_id=?
            ORDER BY created_at DESC LIMIT 20
        """, (str(user_id),)).fetchall()
        conn.close()

    text = "📦 <b>MY ORDERS</b>\n\n"
    if not rows:
        text += "No orders."
    else:
        for r in rows:
            text += (
                f"🧾 <code>{esc(r['id'])}</code>\n"
                f"📦 {esc(r['product_name'])}\n"
                f"💰 {money(r['total'])}\n"
                f"📌 {esc(r['status'])}\n\n"
            )

    bot.send_message(chat_id, text, reply_markup=back_home())

# ---------------- USDT ----------------

def show_usdt(chat_id, user_id):
    buy = safe_float(get_setting("usdt_buy_rate", "0"))
    sell = safe_float(get_setting("usdt_sell_rate", "0"))

    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("💵 BUY USDT", callback_data="usdt_buy"),
        Button("💵 SELL USDT", callback_data="usdt_sell")
    )
    kb.add(Button("📋 MY REQUESTS", callback_data="usdt_requests"))
    kb.add(Button("🏠 HOME", callback_data="home", style="primary"))

    bot.send_message(
        chat_id,
        "💵 <b>USDT BUY / SELL</b>\n\n"
        f"💵 BUY RATE: <b>{money(buy)}</b>\n"
        f"💵 SELL RATE: <b>{money(sell)}</b>\n\n"
        "Choose an option:",
        reply_markup=kb
    )

def start_usdt_buy(chat_id, user_id):
    rate = safe_float(get_setting("usdt_buy_rate", "0"))
    if rate <= 0:
        bot.send_message(chat_id, "⚠️ USDT BUY rate has not been configured yet.", reply_markup=back_home())
        return
    set_state(user_id, "usdt_buy_amount")
    bot.send_message(chat_id, "💵 <b>BUY USDT</b>\n\nSend the USDT amount you want to buy.", reply_markup=back_home())

def start_usdt_sell(chat_id, user_id):
    rate = safe_float(get_setting("usdt_sell_rate", "0"))
    if rate <= 0:
        bot.send_message(chat_id, "⚠️ USDT SELL rate has not been configured yet.", reply_markup=back_home())
        return
    set_state(user_id, "usdt_sell_amount")
    bot.send_message(chat_id, "💵 <b>SELL USDT</b>\n\nSend the USDT amount you want to sell.", reply_markup=back_home())

def show_usdt_requests(chat_id, user_id):
    with db_lock:
        conn = db()
        rows = conn.execute("""
            SELECT * FROM transactions
            WHERE user_id=? AND type IN ('usdt_buy','usdt_sell')
            ORDER BY created_at DESC LIMIT 10
        """, (str(user_id),)).fetchall()
        conn.close()

    text = "📋 <b>MY USDT REQUESTS</b>\n\n"
    if not rows:
        text += "No USDT requests."
    else:
        for r in rows:
            text += (
                f"🧾 <code>{esc(r['id'])}</code>\n"
                f"Type: {esc(r['type'])}\n"
                f"USDT: {money(r['amount'])}\n"
                f"Total: {money(r['total'])}\n"
                f"Status: {esc(r['status'])}\n\n"
            )

    kb = types.InlineKeyboardMarkup()
    kb.add(Button("💵 USDT MENU", callback_data="usdt"))
    kb.add(Button("🏠 HOME", callback_data="home", style="primary"))
    bot.send_message(chat_id, text, reply_markup=kb)

# ---------------- ADMIN PANEL ----------------

def show_admin(chat_id, user_id):
    if not is_admin(user_id):
        bot.send_message(chat_id, "🚫 Unauthorized.")
        return

    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("📦 PRODUCTS", callback_data="admin_products"),
        Button("💰 BALANCE +/-", callback_data="admin_wallet")
    )
    kb.add(Button("🎟️ REDEEM CODES", callback_data="admin_redeem"))
    kb.row(
        Button("👥 USERS", callback_data="admin_users"),
        Button("📋 ORDERS", callback_data="admin_orders")
    )
    kb.add(Button("⏳ PENDING ORDERS", callback_data="admin_pending_orders"))
    kb.row(
        Button("🛡️ BAN / UNBAN", callback_data="admin_user"),
        Button("💬 MESSAGE USER", callback_data="admin_message_user")
    )
    kb.add(Button("🔎 ORDER ID CHECK", callback_data="admin_order_check"))
    kb.row(
        Button("💰 DEPOSITS", callback_data="admin_deposits"),
        Button("📤 WITHDRAWALS", callback_data="admin_withdrawals")
    )
    kb.add(Button("📢 BROADCAST", callback_data="admin_broadcast"))
    kb.add(Button("📢 GROUP MESSAGE TEST", callback_data="admin_group_test"))
    kb.row(
        Button("📊 STATISTICS", callback_data="admin_statistics"),
        Button("💳 PAYMENT SETTINGS", callback_data="admin_payment_settings")
    )
    kb.row(
        Button("👑 ADMINS", callback_data="admin_admins"),
        Button("⚙️ SETTINGS", callback_data="admin_settings")
    )
    kb.add(Button("🏠 HOME", callback_data="home", style="primary"))

    bot.send_message(
        chat_id,
        "🛠️ <b>ɴᴇXᴏ SᴛᴏƦᴇ ADMIN PANEL</b>\n\nWelcome, Administrator.",
        reply_markup=kb
    )

def admin_products(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("➕ ADD PRODUCT", callback_data="admin_add_product"),
        Button("📋 VIEW", callback_data="admin_view_products")
    )
    kb.row(
        Button("➕ ADD STOCK", callback_data="admin_add_stock"),
        Button("➖ REMOVE STOCK", callback_data="admin_remove_stock")
    )
    kb.row(
        Button("✏️ EDIT", callback_data="admin_edit_product"),
        Button("🗑️ DELETE", callback_data="admin_delete_product")
    )
    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    bot.send_message(chat_id, "📦 <b>PRODUCT MANAGEMENT</b>", reply_markup=kb)

def list_admin_products(chat_id):
    with db_lock:
        conn = db()
        rows = conn.execute(
            "SELECT * FROM products ORDER BY created_at DESC"
        ).fetchall()
        conn.close()

    text = "📦 <b>ALL PRODUCTS</b>\n\n"
    if not rows:
        text += "No products."
    else:
        for p in rows:
            text += (
                f"🆔 <code>{esc(p['id'])}</code>\n"
                f"📦 {esc(p['name'])}\n"
                f"💰 {product_money(p)}\n"
                f"📊 Stock: {p['available_stock']}/{p['total_stock']}\n"
                f"🎨 Color: {esc(p['color'] or 'blue').upper()}\n"
                f"📌 {esc(p['status'])}\n\n"
            )

    bot.send_message(chat_id, text, reply_markup=back_admin())

def start_add_product(chat_id, user_id):
    set_state(user_id, "add_product_name")
    bot.send_message(
        chat_id,
        "➕ <b>ADD PRODUCT</b>\n\n"
        "1️⃣ Send the <b>Product Name</b>."
    )

def create_product_from_state(user_id, incoming):
    # This function is kept as a compatibility fallback for old add-product state data.
    parts = [x.strip() for x in incoming.split("|")]
    if len(parts) != 5:
        return False, (
            "❌ Invalid format.\n\n"
            "Use:\n"
            "<code>Product Name | Price | Currency | Added Stock | Total Stock</code>"
        )

    name = parts[0]
    price = safe_float(parts[1], -1)
    currency = parts[2].strip().upper()
    added = safe_int(parts[3], -1)
    total = safe_int(parts[4], -1)

    if not name or price <= 0 or not currency or len(currency) > 10 or added < 0 or total < 0:
        return False, "❌ Invalid product details."

    pid = new_id("P")
    with db_lock:
        conn = db()
        conn.execute("""
            INSERT INTO products(
                id,name,price,currency,added_stock,available_stock,total_stock,
                info,color,status,created_by,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (
            pid, name, price, currency, added, added, total,
            "", "blue", "active", str(user_id), now()
        ))
        conn.commit()
        conn.close()

    set_state(user_id, "product_info", pid)
    return True, (
        "✅ <b>Product details received.</b>\n\n"
        f"📦 Product: {esc(name)}\n"
        f"💰 Price: {money(price)} {esc(currency)}\n"
        f"📊 Added Stock: {added}\n"
        f"📊 Total Stock: {total}\n\n"
        "📝 Now send the Product Information."
    )

def handle_add_product_state(uid, chat_id, incoming):
    state, data = get_state(uid)

    if state == "add_product_name":
        name = incoming.strip()
        if not name:
            bot.send_message(chat_id, "❌ Product name cannot be empty.")
            return True
        set_state(uid, "add_product_price", json.dumps({"name": name}, ensure_ascii=False))
        bot.send_message(chat_id, "💰 <b>Send the Product Price.</b>\n\nExample: <code>800</code>")
        return True

    if state == "add_product_price":
        try:
            draft = json.loads(data)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Product session expired. Please start again.")
            return True
        price = safe_float(incoming, -1)
        if price <= 0:
            bot.send_message(chat_id, "❌ Invalid price. Send a number greater than 0.")
            return True
        draft["price"] = price
        set_state(uid, "add_product_currency", json.dumps(draft, ensure_ascii=False))
        bot.send_message(chat_id, "💱 <b>Send the Product Currency.</b>\n\nExamples: <code>ETB</code>, <code>USD</code>, <code>USDT</code>")
        return True

    if state == "add_product_currency":
        try:
            draft = json.loads(data)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Product session expired. Please start again.")
            return True
        currency = incoming.strip().upper()
        if not currency or len(currency) > 10 or not currency.replace("-", "").replace("_", "").isalnum():
            bot.send_message(chat_id, "❌ Invalid currency. Example: <code>ETB</code>, <code>USD</code>, <code>USDT</code>")
            return True
        draft["currency"] = currency
        set_state(uid, "add_product_stock", json.dumps(draft, ensure_ascii=False))
        bot.send_message(chat_id, "📦 <b>Send Stock.</b>\n\nFormat: <code>Added Stock | Total Stock</code>\nExample: <code>6 | 22</code>")
        return True

    if state == "add_product_stock":
        try:
            draft = json.loads(data)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Product session expired. Please start again.")
            return True
        parts = [x.strip() for x in incoming.split("|")]
        if len(parts) != 2:
            bot.send_message(chat_id, "❌ Use: <code>Added Stock | Total Stock</code>")
            return True
        added = safe_int(parts[0], -1)
        total = safe_int(parts[1], -1)
        if added < 0 or total < 0 or added > total:
            bot.send_message(chat_id, "❌ Invalid stock values. Added Stock cannot be greater than Total Stock.")
            return True

        draft["added_stock"] = added
        draft["total_stock"] = total
        set_state(uid, "add_product_color", json.dumps(draft, ensure_ascii=False))
        kb = types.InlineKeyboardMarkup()
        kb.row(Button("🔵 BLUE", callback_data="product_color_blue", style="primary"), Button("🟢 GREEN", callback_data="product_color_green", style="success"))
        kb.add(Button("🔴 RED", callback_data="product_color_red", style="danger"))
        bot.send_message(chat_id, "🎨 <b>PRODUCT COLOR</b>\n\nChoose the color for this product button.", reply_markup=kb)
        return True

    return False

def product_group_announcement(product_row):
    """Publish a newly-added product to the store group."""
    p = product_row
    name = str(p["name"] or "")
    label = name if len(name) <= 48 else name[:45] + "..."
    text = (
        "🆕 <b>NEW PRODUCT ADDED!</b>\n\n"
        f"📦 <b>{esc(name)}</b>\n"
        f"💰 Price: <b>{product_money(p)}</b>\n"
        f"📦 Stock: <b>{p["available_stock"]}</b> units\n\n"
        "🔥 <b>Available now — order from the bot.</b>"
    )
    # Blue primary button for NEW PRODUCT posts.
    # Clicking it opens the exact product page inside the bot.
    return post_to_main_group(
        text,
        reply_markup=product_url_button(f"🛒 BUY {label}", p["id"], style={"blue":"primary", "green":"success", "red":"danger"}.get(str(p["color"] or "blue").lower(), "primary"))
    )


def finish_product_info(user_id, info):
    state, pid = get_state(user_id)
    if state != "product_info":
        return "❌ Product draft expired."

    with db_lock:
        conn = db()
        conn.execute(
            "UPDATE products SET info=? WHERE id=?",
            (info, pid)
        )
        p = conn.execute(
            "SELECT * FROM products WHERE id=?",
            (pid,)
        ).fetchone()
        conn.commit()
        conn.close()

    clear_state(user_id)

    if not p:
        return "❌ Product not found."

    group_ok = product_group_announcement(p)
    group_status = "📢 Group: <b>POSTED</b>" if group_ok else "⚠️ Group: <b>POST FAILED</b> — check that the bot is an admin in the group."
    return (
        "✅ <b>Product Created</b>\n\n"
        f"📦 {esc(p['name'])}\n"
        f"💰 Price: {product_money(p)}\n"
        f"📊 Available: {p['available_stock']}\n"
        f"📊 Total: {p['total_stock']}\n\n"
        f"{group_status}"
    )

def select_product(chat_id, user_id, state_name, title):
    with db_lock:
        conn = db()
        rows = conn.execute(
            "SELECT id,name,available_stock FROM products ORDER BY name"
        ).fetchall()
        conn.close()

    if not rows:
        bot.send_message(chat_id, "❌ No products.", reply_markup=back_admin())
        return

    kb = types.InlineKeyboardMarkup()
    for p in rows:
        kb.add(Button(
            f"📦 {p['name']} ({p['available_stock']})",
            callback_data=f"{state_name}_{p['id']}"
        ))
    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    bot.send_message(chat_id, title, reply_markup=kb)

def admin_add_stock_start(chat_id, user_id):
    select_product(chat_id, user_id, "select_add_stock", "➕ Select product")

def admin_remove_stock_start(chat_id, user_id):
    select_product(chat_id, user_id, "select_remove_stock", "➖ Select product")

def stock_action(chat_id, user_id, product_id, action):
    with db_lock:
        conn = db()
        p = conn.execute(
            "SELECT * FROM products WHERE id=?",
            (product_id,)
        ).fetchone()
        conn.close()

    if not p:
        bot.send_message(chat_id, "❌ Product not found.", reply_markup=back_admin())
        return

    set_state(user_id, action, product_id)
    word = "add" if action == "add_stock" else "remove"
    bot.send_message(
        chat_id,
        f"📦 <b>{p['name']}</b>\n\n"
        f"Send the stock amount to {word}."
    )

def delete_product_start(chat_id, user_id):
    select_product(chat_id, user_id, "delete_product", "🗑️ Select product to delete")

def delete_product(chat_id, product_id):
    with db_lock:
        conn = db()
        conn.execute("DELETE FROM product_stock WHERE product_id=?", (product_id,))
        conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        conn.close()
    bot.send_message(chat_id, "✅ Product deleted.", reply_markup=back_admin())

def edit_product_start(chat_id, user_id):
    select_product(chat_id, user_id, "edit_product", "✏️ Select product to edit")

def activate_deactivate(chat_id, product_id, active):
    with db_lock:
        conn = db()
        conn.execute(
            "UPDATE products SET status=? WHERE id=?",
            ("active" if active else "inactive", product_id)
        )
        conn.commit()
        conn.close()
    bot.send_message(
        chat_id,
        "✅ Product status updated.",
        reply_markup=back_admin()
    )

def admin_wallet(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(Button("🔎 CHECK USER BALANCE", callback_data="admin_check_balance"))
    kb.row(
        Button("➕ ADD BALANCE", callback_data="admin_add_balance"),
        Button("➖ REMOVE BALANCE", callback_data="admin_remove_balance")
    )
    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    bot.send_message(chat_id, "💳 <b>ADMIN WALLET</b>", reply_markup=kb)

def start_user_lookup(chat_id, user_id, state, prompt):
    set_state(user_id, state)
    bot.send_message(chat_id, prompt)

def user_details(chat_id, user_id, target_id):
    target = get_user(target_id)
    if not target:
        bot.send_message(chat_id, "❌ User not found.", reply_markup=back_admin())
        return

    # Store selected target for follow-up actions.
    set_state(user_id, "admin_selected_user", str(target_id))

    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("➕ ADD BALANCE", callback_data="admin_add_balance"),
        Button("➖ REMOVE BALANCE", callback_data="admin_remove_balance")
    )
    kb.row(
        Button("💬 MESSAGE", callback_data="admin_user_message"),
        Button("📦 ORDERS", callback_data="admin_user_orders")
    )
    kb.row(
        Button("🚫 BAN", callback_data="admin_ban"),
        Button("✅ UNBAN", callback_data="admin_unban")
    )
    kb.add(Button("🔙 ADMIN", callback_data="admin"))

    bot.send_message(
        chat_id,
        "👤 <b>USER DETAILS</b>\n\n"
        f"🆔 ID: <code>{target['id']}</code>\n"
        f"👤 Username: @{esc(target['username'])}\n"
        f"💰 Balance: <b>{money(target['balance'])}</b>\n"
        f"📦 Orders: {target['order_count']}\n"
        f"💳 Deposits: {target['deposit_count']}\n"
        f"📤 Withdrawals: {target['withdrawal_count']}\n"
        f"🚫 Ban: {esc(target['ban'])}",
        reply_markup=kb
    )

def admin_users(chat_id):
    with db_lock:
        conn = db()
        rows = conn.execute("""
            SELECT id,first_name,username,balance,ban
            FROM users ORDER BY registered_at DESC LIMIT 30
        """).fetchall()
        conn.close()

    text = "👥 <b>USERS</b>\n\n"
    if not rows:
        text += "No users."
    else:
        for r in rows:
            text += (
                f"🆔 <code>{r['id']}</code> | "
                f"@{esc(r['username'])} | "
                f"💰 {money(r['balance'])} | "
                f"{'🚫' if r['ban']=='ok' else '✅'}\n"
            )
    bot.send_message(chat_id, text, reply_markup=back_admin())

def admin_pending_orders(chat_id):
    with db_lock:
        conn = db()
        rows = conn.execute("SELECT * FROM orders WHERE status='pending' ORDER BY created_at DESC LIMIT 30").fetchall()
        conn.close()
    text = "⏳ <b>PENDING PRODUCT ORDERS</b>\n\n"
    if not rows:
        text += "No pending orders."
        bot.send_message(chat_id, text, reply_markup=back_admin())
        return
    for o in rows:
        text += (f"🧾 <code>{esc(o['id'])}</code>\n"
                 f"👤 User: <code>{esc(o['user_id'])}</code>\n"
                 f"📦 {esc(o['product_name'])} × {o['quantity']}\n"
                 f"💰 {money(o['total'])}\n"
                 f"🕒 {esc(o['created_at'])}\n\n")
    kb = types.InlineKeyboardMarkup()
    for o in rows:
        kb.row(Button(f"✅ APPROVE {o['id'][-6:]}", callback_data=f"approve_order_{o['id']}", style="success"),
               Button(f"❌ REJECT {o['id'][-6:]}", callback_data=f"reject_order_{o['id']}", style="danger"))
    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    bot.send_message(chat_id, text, reply_markup=kb)


def admin_orders(chat_id):
    with db_lock:
        conn = db()
        rows = conn.execute("""
            SELECT * FROM orders ORDER BY created_at DESC LIMIT 30
        """).fetchall()
        conn.close()

    text = "📋 <b>ALL ORDERS</b>\n\n"
    if not rows:
        text += "No orders."
    else:
        for r in rows:
            text += (
                f"🧾 <code>{esc(r['id'])}</code>\n"
                f"👤 {r['user_id']}\n"
                f"📦 {esc(r['product_name'])}\n"
                f"💰 {money(r['total'])}\n"
                f"📌 {esc(r['status'])}\n\n"
            )
    bot.send_message(chat_id, text, reply_markup=back_admin())

def admin_deposits(chat_id):
    with db_lock:
        conn = db()
        rows = conn.execute("""
            SELECT * FROM deposits
            WHERE status='pending'
            ORDER BY created_at DESC LIMIT 30
        """).fetchall()
        conn.close()

    text = "💰 <b>PENDING DEPOSITS</b>\n\n"
    kb = types.InlineKeyboardMarkup()

    if not rows:
        text += "No pending deposits."
    else:
        for r in rows:
            text += (
                f"🧾 <code>{r['id']}</code>\n"
                f"👤 User: <code>{r['user_id']}</code>\n"
                f"💵 Amount: <b>{money(r['amount'])} ETB</b>\n"
                f"📦 Purpose / Product: <b>{esc(r['product_name']) if 'product_name' in r.keys() and r['product_name'] else 'Wallet Deposit'}</b>\n"
                f"🧾 TXID: <code>{esc(r['transaction_id'])}</code>\n\n"
            )
            kb.row(
                Button(
                    "✅ APPROVE",
                    callback_data=f"approve_deposit_{r['id']}"
                ),
                Button(
                    "❌ REJECT",
                    callback_data=f"reject_deposit_{r['id']}"
                )
            )

    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    bot.send_message(chat_id, text, reply_markup=kb)

def admin_withdrawals(chat_id):
    with db_lock:
        conn = db()
        rows = conn.execute("""
            SELECT * FROM withdrawals
            WHERE status='pending'
            ORDER BY created_at DESC LIMIT 30
        """).fetchall()
        conn.close()

    text = "📤 <b>PENDING WITHDRAWALS</b>\n\n"
    kb = types.InlineKeyboardMarkup()

    if not rows:
        text += "No pending withdrawals."
    else:
        for r in rows:
            text += (
                f"🧾 <code>{r['id']}</code>\n"
                f"👤 User: <code>{r['user_id']}</code>\n"
                f"💵 Amount: <b>{money(r['amount'])}</b>\n"
                f"💳 Account: <code>{esc(r['account'])}</code>\n\n"
            )
            kb.row(
                Button(
                    "✅ APPROVE",
                    callback_data=f"approve_withdraw_{r['id']}"
                ),
                Button(
                    "❌ REJECT",
                    callback_data=f"reject_withdraw_{r['id']}"
                )
            )

    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    bot.send_message(chat_id, text, reply_markup=kb)

def admin_statistics(chat_id):
    with db_lock:
        conn = db()
        users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        products = conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
        orders = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
        completed = conn.execute(
            "SELECT COUNT(*) c FROM orders WHERE status='completed'"
        ).fetchone()["c"]
        revenue = conn.execute(
            "SELECT COALESCE(SUM(total),0) s FROM orders WHERE status='completed'"
        ).fetchone()["s"]
        deposits = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM deposits WHERE status='approved'"
        ).fetchone()["s"]
        withdrawals = conn.execute(
            "SELECT COALESCE(SUM(amount),0) s FROM withdrawals WHERE status='approved'"
        ).fetchone()["s"]
        conn.close()

    bot.send_message(
        chat_id,
        "📊 <b>STATISTICS</b>\n\n"
        f"👥 Users: <b>{users}</b>\n"
        f"📦 Products: <b>{products}</b>\n"
        f"🧾 Orders: <b>{orders}</b>\n"
        f"✅ Completed Orders: <b>{completed}</b>\n"
        f"💰 Revenue: <b>{money(revenue)}</b>\n"
        f"💳 Approved Deposits: <b>{money(deposits)}</b>\n"
        f"📤 Approved Withdrawals: <b>{money(withdrawals)}</b>",
        reply_markup=back_admin()
    )

def admin_payment_settings(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(Button("📱 SET TELEBIRR NUMBER", callback_data="set_payment_phone"))
    kb.add(Button("👤 SET ACCOUNT MANAGER", callback_data="set_payment_manager"))
    kb.add(Button("📤 SET USDT SELL ADDRESS", callback_data="set_usdt_sell_address"))
    kb.row(
        Button("💵 BUY RATE", callback_data="set_usdt_buy_rate"),
        Button("💵 SELL RATE", callback_data="set_usdt_sell_rate")
    )
    kb.add(Button("🔙 ADMIN", callback_data="admin"))

    bot.send_message(
        chat_id,
        "💳 <b>PAYMENT SETTINGS</b>\n\n"
        f"📱 Telebirr: <code>{esc(get_setting('telebirr_number'))}</code>\n"
        f"👤 Manager: <b>{esc(get_setting('account_manager'))}</b>\n"
        f"💵 BUY: <b>{money(get_setting('usdt_buy_rate','0'))}</b>\n"
        f"💵 SELL: <b>{money(get_setting('usdt_sell_rate','0'))}</b>\n"
        f"📤 SELL ADDRESS: <code>{esc(get_setting('usdt_sell_address',''))}</code>",
        reply_markup=kb
    )

def admin_admins(chat_id):
    ids = admin_ids()
    text = "👑 <b>ADMINS</b>\n\n"
    for aid in ids:
        text += f"🆔 <code>{esc(aid)}</code>\n"

    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("➕ ADD ADMIN", callback_data="add_admin"),
        Button("➖ REMOVE ADMIN", callback_data="remove_admin")
    )
    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    bot.send_message(chat_id, text, reply_markup=kb)

def admin_settings(chat_id):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button("📢 GROUP LOG ON/OFF", callback_data="toggle_group_log"),
        Button("🎨 BUTTON THEME", callback_data="button_theme_menu"),
    )
    kb.add(Button("🖼️ SET GROUP LOG PHOTO", callback_data="set_group_log_photo"))
    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    kb.add(Button("🚀 V11 SETTINGS", callback_data="v11_settings", style="primary"))

    enabled = "ON" if get_setting("group_log_enabled", "1") == "1" else "OFF"
    theme = get_setting("button_theme", "primary").upper()
    bot.send_message(
        chat_id,
        "⚙️ <b>SYSTEM SETTINGS</b>\n\n"
        f"🏪 Store: <b>{STORE_NAME}</b>\n"
        f"👤 Bot: <code>@{BOT_USERNAME}</code>\n"
        f"👥 Group: <code>{MAIN_GROUP}</code>\n"
        f"🆘 Support: {SUPPORT}\n\n"
        f"📢 Group success logs: <b>{enabled}</b>\n"
        f"🎨 Button theme: <b>{theme}</b>\n"
        f"🖼️ Group log photo: <code>{esc(get_setting('group_log_photo',''))}</code>",
        reply_markup=kb
    )

def admin_broadcast_start(chat_id, user_id):
    clear_state(user_id)
    broadcast_menu(chat_id)

def do_broadcast(chat_id, text):
    # Backward-compatible text broadcast.
    content = {"type": "text", "file_id": "", "caption": text}
    broadcast_finish(chat_id, 0, "users", content)

def admin_command(message, cmd):
    uid = message.from_user.id
    chat_id = message.chat.id

    if not is_admin(uid):
        bot.send_message(chat_id, "🚫 Unauthorized.")
        return

    mapping = {
        "admin_products": lambda: admin_products(chat_id),
        "admin_add_product": lambda: start_add_product(chat_id, uid),
        "admin_add_stock": lambda: admin_add_stock_start(chat_id, uid),
        "admin_remove_stock": lambda: admin_remove_stock_start(chat_id, uid),
        "admin_view_products": lambda: list_admin_products(chat_id),
        "admin_delete_product": lambda: delete_product_start(chat_id, uid),
        "admin_edit_product": lambda: edit_product_start(chat_id, uid),
        "admin_wallet": lambda: admin_wallet(chat_id),
        "admin_check_balance": lambda: start_user_lookup(
            chat_id, uid, "wallet_user", "🔎 Send user ID."
        ),
        "admin_add_balance": lambda: start_user_lookup(
            chat_id, uid, "wallet_add_target", "➕ Send user ID."
        ),
        "admin_remove_balance": lambda: start_user_lookup(
            chat_id, uid, "wallet_minus_target", "➖ Send user ID."
        ),
        "admin_users": lambda: admin_users(chat_id),
        "admin_user": lambda: start_user_lookup(
            chat_id, uid, "user_lookup", "👤 Send user ID."
        ),
        "admin_user_orders": lambda: start_user_lookup(
            chat_id, uid, "admin_user_orders", "📦 Send user ID."
        ),
        "admin_user_message": lambda: start_user_lookup(
            chat_id, uid, "message_user_target", "💬 Send user ID."
        ),
        "admin_ban": lambda: start_user_lookup(
            chat_id, uid, "ban_user", "🚫 Send user ID."
        ),
        "admin_unban": lambda: start_user_lookup(
            chat_id, uid, "unban_user", "✅ Send user ID."
        ),
        "admin_orders": lambda: admin_orders(chat_id),
        "admin_deposits": lambda: admin_deposits(chat_id),
        "admin_withdrawals": lambda: admin_withdrawals(chat_id),
        "admin_broadcast": lambda: admin_broadcast_start(chat_id, uid),
        "admin_message_user": lambda: start_user_lookup(
            chat_id, uid, "message_user_target", "💬 Send user ID."
        ),
        "admin_statistics": lambda: admin_statistics(chat_id),
        "admin_payment_settings": lambda: admin_payment_settings(chat_id),
        "admin_admins": lambda: admin_admins(chat_id),
        "admin_settings": lambda: admin_settings(chat_id),
    }

    fn = mapping.get(cmd)
    if fn:
        fn()

# ---------------- TEXT STATE HANDLER ----------------

@bot.message_handler(content_types=["text", "photo", "video", "document", "audio", "animation"])
def text_handler(message):
    ensure_user(message.from_user)
    uid = message.from_user.id
    chat_id = message.chat.id

    message_text = message.text or message.caption or ""
    if message_text.startswith("/"):
        return

    if banned(uid):
        bot.send_message(chat_id, "🚫 Your account is currently banned.")
        return

    state, data = get_state(uid)

    # Normal users must satisfy Force Join before using the store. Admins bypass it.
    if not is_admin(uid) and v11_force_join_enabled() and not v11_all_channels_joined(uid):
        bot.send_message(
            chat_id,
            "🔒 <b>JOIN REQUIRED</b>\n\nPlease join all required chats below, then press <b>CHECK JOIN</b>.",
            parse_mode="HTML",
            reply_markup=v11_force_join_keyboard()
        )
        return
    incoming = message_text.strip()

    # Rich broadcast content methods.
    if state == "broadcast_content":
        target = data
        if message.content_type == "text":
            content = {"type": "text", "file_id": "", "caption": incoming}
        elif message.content_type == "photo":
            content = {
                "type": "photo",
                "file_id": message.photo[-1].file_id,
                "caption": message.caption or ""
            }
        elif message.content_type == "video":
            content = {
                "type": "video",
                "file_id": message.video.file_id,
                "caption": message.caption or ""
            }
        elif message.content_type == "document":
            content = {
                "type": "document",
                "file_id": message.document.file_id,
                "caption": message.caption or ""
            }
        elif message.content_type == "audio":
            content = {
                "type": "audio",
                "file_id": message.audio.file_id,
                "caption": message.caption or ""
            }
        elif message.content_type == "animation":
            content = {
                "type": "animation",
                "file_id": message.animation.file_id,
                "caption": message.caption or ""
            }
        else:
            bot.send_message(chat_id, "❌ Unsupported broadcast method.")
            return

        broadcast_button_prompt(chat_id, uid, content, target)
        return

    if not state:
        send_home(chat_id, uid)
        return

    if state == "redeem_direct":
        redeem_direct(chat_id, uid, incoming)
        clear_state(uid)
        return

    if state == "redeem_create_code":
        if not is_admin(uid):
            clear_state(uid); bot.send_message(chat_id,"🚫 Unauthorized."); return
        code=incoming.strip().upper()
        if not code or len(code)>64 or " " in code:
            bot.send_message(chat_id,"❌ Invalid code. Use letters/numbers without spaces."); return
        with db_lock:
            conn=db(); exists=conn.execute("SELECT 1 FROM redeem_codes WHERE upper(code)=?",(code,)).fetchone(); conn.close()
        if exists:
            bot.send_message(chat_id,"❌ Code already exists. Send another code."); return
        set_state(uid,"redeem_create_amount",code)
        bot.send_message(chat_id,"💰 Send the bonus amount in ETB. Example: <code>100</code>")
        return

    if state == "redeem_create_amount":
        amount=safe_float(incoming,-1)
        if amount<=0:
            bot.send_message(chat_id,"❌ Invalid amount."); return
        set_state(uid,"redeem_create_limit",json.dumps({"code":data,"amount":amount}))
        bot.send_message(chat_id,"👥 Send the maximum number of users who can claim this code. Example: <code>10</code>")
        return

    if state == "redeem_create_limit":
        try:
            draft = json.loads(data)
            code = str(draft.get("code", "")).strip().upper()
            amount = safe_float(draft.get("amount"), -1)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Session expired. Please start Create Redeem again.", reply_markup=back_admin())
            return

        limit = safe_int(incoming, -1)
        if limit <= 0:
            bot.send_message(
                chat_id,
                "⚠️ <b>INVALID CLAIM LIMIT</b>\n\n"
                "👥 Send a whole number greater than 0.\n"
                "Example: <code>10</code>",
                reply_markup=back_admin()
            )
            return
        if limit > 1000000000:
            bot.send_message(chat_id, "⚠️ Claim limit is too large. Please use a reasonable number.", reply_markup=back_admin())
            return
        if not code or amount <= 0:
            clear_state(uid)
            bot.send_message(chat_id, "❌ <b>INVALID REDEEM DATA</b>\n\nPlease start Create Redeem again.", reply_markup=back_admin())
            return

        try:
            with db_lock:
                conn = db()
                exists = conn.execute("SELECT id FROM redeem_codes WHERE upper(code)=?", (code,)).fetchone()
                if exists:
                    conn.close()
                    bot.send_message(chat_id, "❌ Code already exists. Please create another code.", reply_markup=back_admin())
                    set_state(uid, "redeem_create_code")
                    return
                conn.execute(
                    "INSERT INTO redeem_codes(code,amount,max_claims,claims_count,active,created_by,created_at) VALUES(?,?,?,?,?,?,?)",
                    (code, amount, limit, 0, True, str(uid), now())
                )
                conn.commit()
                conn.close()
        except Exception as e:
            logging.exception("Redeem create failed")
            bot.send_message(chat_id, f"❌ Could not create redeem code.\n<code>{esc(str(e))[:300]}</code>", reply_markup=back_admin())
            return

        clear_state(uid)
        kb = types.InlineKeyboardMarkup()
        kb.row(
            Button("🎟️ LIST CODES", callback_data="redeem_list", style="primary"),
            Button("🔙 ADMIN", callback_data="admin", style="primary")
        )
        bot.send_message(
            chat_id,
            "🎉 <b>REDEEM CODE CREATED SUCCESSFULLY</b>\n\n"
            f"🎟️ Code: <code>{esc(code)}</code>\n"
            f"💰 Bonus: <b>{money(amount)} ETB</b>\n"
            f"👥 Maximum Claims: <b>{limit}</b>\n"
            "📌 Status: <b>ACTIVE</b>",
            reply_markup=kb
        )
        return

    if state == "deposit_amount":
        amount = safe_float(incoming, -1)
        if amount <= 0:
            bot.send_message(chat_id, "❌ Please enter a valid deposit amount.")
            return

        set_state(uid, "deposit_redeem", json.dumps({"amount": amount}, ensure_ascii=False))
        bot.send_message(chat_id, "🎟️ <b>REDEEM CODE (OPTIONAL)</b>\n\nSend your redeem code, or send <code>SKIP</code> if you don't have one.", reply_markup=back_home())
        return

    if state == "deposit_redeem":
        try:
            draft=json.loads(data); amount=float(draft["amount"])
        except Exception:
            clear_state(uid); bot.send_message(chat_id,"❌ Deposit session expired.",reply_markup=back_home()); return
        code="" if incoming.upper()=="SKIP" else incoming.upper()
        dep_id=create_deposit(uid,amount,code)
        if code:
            ok,msg,rc=redeem_validate(code,uid,reserve=True,deposit_id=dep_id)
            if not ok:
                # Remove the temporary deposit; user can retry with another code.
                with db_lock:
                    conn=db(); conn.execute("DELETE FROM deposits WHERE id=?",(dep_id,)); conn.execute("UPDATE users SET deposit_count=CASE WHEN deposit_count>0 THEN deposit_count-1 ELSE 0 END WHERE id=?",(str(uid),)); conn.commit(); conn.close()
                bot.send_message(chat_id,msg+"\n\nTry another code or send <code>SKIP</code>.",reply_markup=back_home())
                set_state(uid,"deposit_amount")
                return
        set_state(uid, "deposit_proof", dep_id)

        number = get_setting("telebirr_number")
        manager = get_setting("account_manager")

        bot.send_message(
            chat_id,
            "💳 <b>DEPOSIT</b>\n\n"
            f"💵 Amount: <b>{money(amount)}</b>\n\n"
            "📱 Telebirr Number:\n"
            f"<code>{esc(number)}</code>\n\n"
            "👤 Account Manager:\n"
            f"<b>{esc(manager)}</b>\n\n"
            "📸 After payment, <b>send a payment screenshot</b>.\n"
            "You may also send the Transaction ID if you do not have a screenshot.\n"
            "❗ Your balance will NOT be credited automatically.",
            reply_markup=back_home()
        )
        return

    if state in ("deposit_proof", "deposit_txid"):
        dep_id = data
        screenshot_id = ""
        txid = ""
        if message.content_type == "photo":
            screenshot_id = message.photo[-1].file_id
            txid = incoming
        elif message.content_type == "text":
            txid = incoming
        else:
            bot.send_message(chat_id, "❌ Please send a <b>payment screenshot</b> or a <b>Transaction ID</b>.", reply_markup=back_home())
            return

        if not screenshot_id and not txid:
            bot.send_message(chat_id, "❌ Screenshot or Transaction ID cannot be empty.", reply_markup=back_home())
            return

        with db_lock:
            conn = db()
            if txid:
                exists = conn.execute(
                    "SELECT 1 FROM deposits WHERE lower(transaction_id)=lower(?) AND id<>?",
                    (txid, dep_id)
                ).fetchone()
                if exists:
                    conn.close()
                    bot.send_message(chat_id, "❌ This Transaction ID has already been submitted.", reply_markup=back_home())
                    return
            if screenshot_id and txid:
                conn.execute("UPDATE deposits SET screenshot=?, transaction_id=? WHERE id=? AND status='pending'", (screenshot_id, txid, dep_id))
            elif screenshot_id:
                conn.execute("UPDATE deposits SET screenshot=? WHERE id=? AND status='pending'", (screenshot_id, dep_id))
            else:
                conn.execute("UPDATE deposits SET transaction_id=? WHERE id=? AND status='pending'", (txid, dep_id))
            row = conn.execute("SELECT * FROM deposits WHERE id=?", (dep_id,)).fetchone()
            conn.commit()
            conn.close()

        clear_state(uid)
        if not row:
            bot.send_message(chat_id, "❌ Deposit request not found.", reply_markup=back_home())
            return

        kb = types.InlineKeyboardMarkup()
        kb.row(
            Button("✅ APPROVE", callback_data=f"approve_deposit_{dep_id}", style="success"),
            Button("❌ REJECT", callback_data=f"reject_deposit_{dep_id}", style="danger")
        )
        proof = []
        if row["transaction_id"]:
            proof.append(f"🧾 Transaction ID: <code>{esc(row['transaction_id'])}</code>")
        if row["screenshot"]:
            proof.append("📸 Payment Screenshot: <b>ATTACHED BELOW</b>")
        proof_text = "\n".join(proof)
        text = (
            "💳 <b>NEW DEPOSIT REQUEST — ACTION REQUIRED</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🧾 Deposit ID: <code>{esc(row['id'])}</code>\n"
            f"👤 User ID: <code>{uid}</code>\n"
            f"👤 Username: @{esc(row['username']) if row['username'] else 'Not set'}\n"
            f"💵 Amount: <b>{money(row['amount'])}</b>\n"
            f"📦 Product: <b>{esc(row['product_name']) if 'product_name' in row.keys() and row['product_name'] else 'Wallet Deposit'}</b>\n"
            f"🎟️ Redeem Code: <b>{esc(row['redeem_code']) if row['redeem_code'] else 'NONE'}</b>\n"
            f"{proof_text}\n"
            f"🕐 Request time: <code>{esc(row['created_at'])}</code>\n\n"
            "📌 Status: <b>PENDING</b>\n\n"
            "👇 <b>Approve or reject this deposit:</b>"
        )

        sent = notify_admins_photo(row["screenshot"], text, kb) if row["screenshot"] else notify_admins(text, kb)
        if sent == 0:
            try:
                if row["screenshot"]:
                    post_to_main_group(text, reply_markup=kb, photo=row["screenshot"])
                else:
                    post_to_main_group(text, reply_markup=kb)
            except Exception as e:
                logging.error("Deposit group fallback failed: %s", e)

        bot.send_message(
            chat_id,
            "✅ <b>Deposit proof submitted successfully.</b>\n\n"
            f"🧾 Deposit ID: <code>{esc(dep_id)}</code>\n"
            f"📸 Screenshot: <b>{'YES' if row['screenshot'] else 'NO'}</b>\n"
            f"🧾 TXID: <b>{'YES' if row['transaction_id'] else 'NO'}</b>\n"
            "📌 Status: <b>WAITING FOR ADMIN APPROVAL</b>",
            reply_markup=back_home()
        )
        return

    if state == "withdraw_amount":
        amount = safe_float(incoming, -1)
        user = get_user(uid)

        if amount <= 0:
            bot.send_message(chat_id, "❌ Invalid withdrawal amount.")
            return

        if amount > float(user["balance"]):
            bot.send_message(
                chat_id,
                f"❌ <b>Insufficient balance.</b>\n\n"
                f"💰 Balance: {money(user['balance'])}\n"
                f"💵 Requested: {money(amount)}"
            )
            return

        set_state(uid, "withdraw_account", str(amount))
        bot.send_message(
            chat_id,
            "📤 <b>Withdrawal Account</b>\n\n"
            "Send your wallet/account/payment number."
        )
        return

    if state == "withdraw_account":
        amount = safe_float(data, 0)
        account = incoming
        user = get_user(uid)

        if amount <= 0 or amount > float(user["balance"]):
            clear_state(uid)
            bot.send_message(chat_id, "❌ Insufficient balance.", reply_markup=back_home())
            return

        wid = create_withdrawal(uid, amount, account)
        clear_state(uid)

        kb = types.InlineKeyboardMarkup()
        kb.row(
            Button("✅ APPROVE", callback_data=f"approve_withdraw_{wid}"),
            Button("❌ REJECT", callback_data=f"reject_withdraw_{wid}")
        )

        text = (
            "📤 <b>NEW WITHDRAWAL REQUEST</b>\n\n"
            f"👤 User ID: <code>{uid}</code>\n"
            f"👤 Username: @{esc(user['username'])}\n"
            f"💵 Amount: <b>{money(amount)}</b>\n"
            f"💳 Account: <code>{esc(account)}</code>\n"
            f"🕐 Request time: {now()}\n"
            "📌 Status: <b>PENDING</b>"
        )
        notify_admins(text, kb)

        bot.send_message(
            chat_id,
            f"✅ Withdrawal request created.\n\n"
            f"💵 Amount: {money(amount)}\n"
            "📌 Status: PENDING",
            reply_markup=back_home()
        )
        return

    if state == "usdt_buy_amount":
        amount = safe_float(incoming, -1)
        rate = safe_float(get_setting("usdt_buy_rate", "0"))
        if amount <= 0:
            bot.send_message(chat_id, "❌ Invalid USDT amount.")
            return
        if rate <= 0:
            clear_state(uid)
            bot.send_message(chat_id, "⚠️ BUY rate is not configured.")
            return

        total = amount * rate
        set_state(uid, "usdt_buy_method", f"{amount}|{rate}|{total}")
        kb = types.InlineKeyboardMarkup()
        kb.row(Button("📱 TELEBIRR", callback_data="usdt_buy_method_telebirr"), Button("₿ BYBIT", callback_data="usdt_buy_method_bybit"))
        kb.row(Button("🟡 BINANCE", callback_data="usdt_buy_method_binance"), Button("🟣 OKX", callback_data="usdt_buy_method_okx"))
        kb.add(Button("🔗 OTHER WALLET", callback_data="usdt_buy_method_other"))
        kb.add(Button("🔙 USDT", callback_data="usdt"))
        bot.send_message(
            chat_id,
            "💵 <b>BUY USDT</b>\n\n"
            f"💵 USDT: <b>{money(amount)}</b>\n"
            f"💱 Rate: <b>{money(rate)}</b>\n"
            f"💰 Total: <b>{money(total)} ETB</b>\n\n"
            "📥 <b>Choose the method where you will receive USDT:</b>",
            reply_markup=kb
        )
        return

    if state == "usdt_buy_method":
        bot.send_message(chat_id, "❌ Please choose a receiving method using the buttons above.", reply_markup=back_home())
        return

    if state == "usdt_buy_address":
        try:
            amount, rate, total, method = data.split("|", 3)
            amount, rate, total = float(amount), float(rate), float(total)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Request expired.", reply_markup=back_home())
            return
        address = incoming
        if not address:
            bot.send_message(chat_id, "❌ Address / ID cannot be empty.", reply_markup=back_home())
            return
        rid = new_id("USDT")
        payment_info = f"{method}: {address}"
        with db_lock:
            conn = db()
            conn.execute("INSERT INTO transactions(id,user_id,type,amount,rate,total,payment_information,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)", (rid, str(uid), "usdt_buy", amount, rate, total, payment_info, "pending", now()))
            conn.commit()
            conn.close()
        clear_state(uid)
        usdt_request_admin_notify(uid, rid)
        bot.send_message(chat_id, "✅ <b>USDT BUY REQUEST SUBMITTED</b>\n\n📌 Status: <b>PENDING</b>\n🧾 Order ID: <code>" + esc(rid) + "</code>", reply_markup=back_home())
        return

    if state == "usdt_buy_payment":
        try:
            amount, rate, total = map(float, data.split("|"))
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Request expired.")
            return

        rid = new_id("USDT")
        with db_lock:
            conn = db()
            conn.execute("""
                INSERT INTO transactions(
                    id,user_id,type,amount,rate,total,
                    payment_information,status,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
            """, (
                rid, str(uid), "usdt_buy",
                amount, rate, total,
                incoming, "pending", now()
            ))
            conn.commit()
            conn.close()

        clear_state(uid)
        usdt_request_admin_notify(uid, rid)
        bot.send_message(chat_id, "✅ USDT Buy request submitted.\n\n📌 Status: PENDING", reply_markup=back_home())
        return

    if state == "usdt_sell_amount":
        amount = safe_float(incoming, -1)
        rate = safe_float(get_setting("usdt_sell_rate", "0"))
        if amount <= 0:
            bot.send_message(chat_id, "❌ Invalid USDT amount.")
            return
        if rate <= 0:
            clear_state(uid)
            bot.send_message(chat_id, "⚠️ SELL rate is not configured.")
            return

        total = amount * rate
        sell_address = get_setting("usdt_sell_address", "").strip()
        if not sell_address:
            bot.send_message(
                chat_id,
                "⚠️ <b>USDT SELL ADDRESS IS NOT CONFIGURED.</b>\n\n"
                "Please contact the administrator.",
                reply_markup=back_home()
            )
            return

        set_state(uid, "usdt_sell_account", f"{amount}|{rate}|{total}")
        bot.send_message(
            chat_id,
            "💵 <b>SELL USDT</b>\n\n"
            f"💵 USDT: <b>{money(amount)}</b>\n"
            f"💱 Rate: <b>{money(rate)}</b>\n"
            f"💰 You receive: <b>{money(total)} ETB</b>\n\n"
            "📤 <b>SEND USDT TO THIS ADDRESS:</b>\n"
            f"<code>{esc(sell_address)}</code>\n\n"
            "📱 After sending the USDT, send your <b>TELEBIRR ACCOUNT / PHONE NUMBER</b>.",
            reply_markup=back_home()
        )
        return

    if state == "usdt_sell_account":
        try:
            amount, rate, total = map(float, data.split("|"))
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Request expired.")
            return

        rid = new_id("USDT")
        with db_lock:
            conn = db()
            conn.execute("""
                INSERT INTO transactions(
                    id,user_id,type,amount,rate,total,
                    receiving_account,status,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
            """, (
                rid, str(uid), "usdt_sell",
                amount, rate, total,
                incoming, "pending", now()
            ))
            conn.commit()
            conn.close()

        clear_state(uid)
        usdt_request_admin_notify(uid, rid)
        bot.send_message(chat_id, "✅ USDT Sell request submitted.\n\n📌 Status: PENDING", reply_markup=back_home())
        return

    if state in ("add_product_name", "add_product_price", "add_product_currency", "add_product_stock"):
        handle_add_product_state(uid, chat_id, incoming)
        return

    if state == "add_product":
        ok, msg = create_product_from_state(uid, incoming)
        bot.send_message(chat_id, msg)
        return

    if state == "product_info":
        bot.send_message(chat_id, finish_product_info(uid, incoming), reply_markup=back_admin())
        return

    if state in ("add_stock", "remove_stock"):
        amount = safe_int(incoming, -1)
        if amount <= 0:
            bot.send_message(chat_id, "❌ Send a valid stock amount.")
            return

        with db_lock:
            conn = db()
            p = conn.execute(
                "SELECT * FROM products WHERE id=?",
                (data,)
            ).fetchone()

            if not p:
                conn.close()
                clear_state(uid)
                bot.send_message(chat_id, "❌ Product not found.")
                return

            if state == "remove_stock":
                if amount > int(p["available_stock"]):
                    conn.close()
                    bot.send_message(
                        chat_id,
                        f"❌ Cannot remove that much stock.\n\nAvailable: {p['available_stock']}"
                    )
                    return

                conn.execute("""
                    UPDATE products
                    SET available_stock=available_stock-?
                    WHERE id=?
                """, (amount, data))
            else:
                conn.execute("""
                    UPDATE products
                    SET available_stock=available_stock+?,
                        total_stock=total_stock+?,
                        added_stock=added_stock+?
                    WHERE id=?
                """, (amount, amount, amount, data))

            conn.commit()
            p2 = conn.execute(
                "SELECT * FROM products WHERE id=?",
                (data,)
            ).fetchone()
            conn.close()

        clear_state(uid)
        action = "Added" if state == "add_stock" else "Removed"
        bot.send_message(
            chat_id,
            f"✅ <b>Stock {action}</b>\n\n"
            f"📦 {esc(p2['name'])}\n"
            f"📊 Available: {p2['available_stock']}",
            reply_markup=back_admin()
        )
        return

    if state == "admin_order_check":
        admin_order_id_check(chat_id, incoming)
        clear_state(uid)
        return

    if state in ("wallet_user", "user_lookup", "wallet_add_target",
                 "wallet_minus_target", "admin_user_orders",
                 "message_user_target", "ban_user", "unban_user"):
        target_id = incoming
        if not target_id.isdigit():
            bot.send_message(chat_id, "❌ Invalid user ID.")
            return

        target = get_user(target_id)
        if not target:
            bot.send_message(chat_id, "❌ User not found.")
            return

        if state == "wallet_user":
            clear_state(uid)
            user_details(chat_id, uid, target_id)
            return

        if state == "user_lookup":
            clear_state(uid)
            set_state(uid, "admin_selected_user", str(target_id))
            show_admin_user_complete(chat_id, uid, target_id)
            return

        if state == "wallet_add_target":
            set_state(uid, "wallet_add_amount", target_id)
            bot.send_message(chat_id, f"➕ Send amount to add to <code>{target_id}</code>.")
            return

        if state == "wallet_minus_target":
            set_state(uid, "wallet_minus_amount", target_id)
            bot.send_message(chat_id, f"➖ Send amount to remove from <code>{target_id}</code>.")
            return

        if state == "admin_user_orders":
            with db_lock:
                conn = db()
                rows = conn.execute(
                    "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
                    (target_id,)
                ).fetchall()
                conn.close()
            text = f"📦 <b>USER ORDERS</b>\n\nUser: <code>{target_id}</code>\n\n"
            for r in rows:
                text += f"🧾 {r['id']} | {esc(r['product_name'])} | {money(r['total'])} | {r['status']}\n"
            clear_state(uid)
            bot.send_message(chat_id, text, reply_markup=back_admin())
            return

        if state == "message_user_target":
            set_state(uid, "message_user_content", target_id)
            bot.send_message(
                chat_id,
                f"💬 <b>SEND MESSAGE TO USER</b> <code>{target_id}</code>\n\n"
                "You can send text, photo, video, document, audio or animation.",
                reply_markup=back_admin()
            )
            return

        if state == "ban_user":
            with db_lock:
                conn = db()
                conn.execute("UPDATE users SET ban='ok' WHERE id=?", (target_id,))
                conn.commit()
                conn.close()
            clear_state(uid)
            bot.send_message(chat_id, "🚫 User banned.", reply_markup=back_admin())
            return

        if state == "unban_user":
            with db_lock:
                conn = db()
                conn.execute("UPDATE users SET ban='' WHERE id=?", (target_id,))
                conn.commit()
                conn.close()
            clear_state(uid)
            bot.send_message(chat_id, "✅ User unbanned.", reply_markup=back_admin())
            return

    if state == "wallet_add_amount":
        amount = safe_float(incoming, -1)
        target_id = data
        if amount <= 0:
            bot.send_message(chat_id, "❌ Invalid amount.")
            return

        change_balance(target_id, amount)
        txid = new_id("ATX")
        with db_lock:
            conn = db()
            conn.execute("""
                INSERT INTO transactions(
                    id,user_id,type,amount,status,created_at,approved_by
                ) VALUES(?,?,?,?,?,?,?)
            """, (
                txid, target_id, "admin_add_balance",
                amount, "completed", now(), str(uid)
            ))
            conn.commit()
            conn.close()

        clear_state(uid)
        bot.send_message(chat_id, "✅ Balance added.", reply_markup=back_admin())
        try:
            newbal = get_user(target_id)["balance"]
            bot.send_message(
                int(target_id),
                f"💰 <b>Balance Added</b>\n\n"
                f"➕ Amount: <b>{money(amount)}</b>\n"
                f"💰 New Balance: <b>{money(newbal)}</b>"
            )
        except Exception:
            pass
        return

    if state == "wallet_minus_amount":
        amount = safe_float(incoming, -1)
        target_id = data
        target = get_user(target_id)

        if amount <= 0:
            bot.send_message(chat_id, "❌ Invalid amount.")
            return
        if not target or amount > float(target["balance"]):
            bot.send_message(chat_id, "❌ User does not have enough balance.")
            return

        change_balance(target_id, -amount)
        txid = new_id("ATX")
        with db_lock:
            conn = db()
            conn.execute("""
                INSERT INTO transactions(
                    id,user_id,type,amount,status,created_at,approved_by
                ) VALUES(?,?,?,?,?,?,?)
            """, (
                txid, target_id, "admin_remove_balance",
                amount, "completed", now(), str(uid)
            ))
            conn.commit()
            conn.close()

        clear_state(uid)
        bot.send_message(chat_id, "✅ Balance removed.", reply_markup=back_admin())
        return

    if state in ("message_user_content", "message_user_text"):
        target_id = data
        try:
            target_chat = int(target_id)
            if message.content_type == "text":
                bot.send_message(target_chat, incoming)
            elif message.content_type == "photo":
                bot.send_photo(target_chat, message.photo[-1].file_id, caption=message.caption or "")
            elif message.content_type == "video":
                bot.send_video(target_chat, message.video.file_id, caption=message.caption or "")
            elif message.content_type == "document":
                bot.send_document(target_chat, message.document.file_id, caption=message.caption or "")
            elif message.content_type == "audio":
                bot.send_audio(target_chat, message.audio.file_id, caption=message.caption or "")
            elif message.content_type == "animation":
                bot.send_animation(target_chat, message.animation.file_id, caption=message.caption or "")
            else:
                raise ValueError("Unsupported message type")
            bot.send_message(chat_id, "✅ <b>Message sent successfully.</b>", reply_markup=back_admin())
        except Exception as e:
            bot.send_message(chat_id, f"❌ Could not send message.\n\n{esc(e)}", reply_markup=back_admin())
        clear_state(uid)
        return

    if state == "add_admin":
        target = incoming
        if not target.isdigit():
            bot.send_message(chat_id, "❌ Invalid admin ID.")
            return
        with db_lock:
            conn = db()
            conn.execute(
                "INSERT INTO admins(user_id) VALUES (?) ON CONFLICT (user_id) DO NOTHING",
                (target,)
            )
            conn.commit()
            conn.close()
        clear_state(uid)
        bot.send_message(chat_id, "✅ Admin added.", reply_markup=back_admin())
        return

    if state == "remove_admin":
        target = incoming
        if target == str(MASTER_ADMIN):
            bot.send_message(chat_id, "❌ Master Admin cannot be removed.")
            return
        with db_lock:
            conn = db()
            conn.execute("DELETE FROM admins WHERE user_id=?", (target,))
            conn.commit()
            conn.close()
        clear_state(uid)
        bot.send_message(chat_id, "✅ Admin removed if it existed.", reply_markup=back_admin())
        return

    if state == "usdt_sell_address":
        if not incoming:
            bot.send_message(chat_id, "❌ Address cannot be empty.")
            return
        set_setting("usdt_sell_address", incoming)
        clear_state(uid)
        bot.send_message(
            chat_id,
            "✅ <b>USDT SELL ADDRESS UPDATED.</b>\n\n"
            f"<code>{esc(incoming)}</code>",
            reply_markup=back_admin()
        )
        return

    if state == "group_log_photo":
        if message.content_type == "photo":
            set_setting("group_log_photo", message.photo[-1].file_id)
        elif incoming.lower() == "off":
            set_setting("group_log_photo", "")
        elif not incoming:
            bot.send_message(chat_id, "❌ Send a photo, image URL, or <code>off</code>.", reply_markup=back_admin())
            return
        else:
            parsed = urlparse(incoming)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                bot.send_message(chat_id, "❌ Invalid image URL.", reply_markup=back_admin())
                return
            set_setting("group_log_photo", incoming)
        clear_state(uid)
        bot.send_message(chat_id, "✅ Group log photo updated.", reply_markup=back_admin())
        return

    if state == "payment_phone":
        set_setting("telebirr_number", incoming)
        clear_state(uid)
        bot.send_message(chat_id, "✅ Telebirr number updated.", reply_markup=back_admin())
        return

    if state == "payment_manager":
        set_setting("account_manager", incoming)
        clear_state(uid)
        bot.send_message(chat_id, "✅ Account manager updated.", reply_markup=back_admin())
        return

    if state == "usdt_buy_rate":
        rate = safe_float(incoming, -1)
        if rate <= 0:
            bot.send_message(chat_id, "❌ Invalid BUY rate.")
            return
        set_setting("usdt_buy_rate", rate)
        clear_state(uid)
        bot.send_message(chat_id, f"✅ USDT BUY rate updated to <b>{money(rate)}</b>.", reply_markup=back_admin())
        return

    if state == "usdt_sell_rate":
        rate = safe_float(incoming, -1)
        if rate <= 0:
            bot.send_message(chat_id, "❌ Invalid SELL rate.")
            return
        set_setting("usdt_sell_rate", rate)
        clear_state(uid)
        bot.send_message(chat_id, f"✅ USDT SELL rate updated to <b>{money(rate)}</b>.", reply_markup=back_admin())
        return

    if state == "broadcast_button_text":
        try:
            payload = json.loads(data)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Broadcast session expired.", reply_markup=back_admin())
            return

        if not incoming:
            bot.send_message(chat_id, "❌ Button text cannot be empty.")
            return

        payload["button_text"] = incoming
        set_state(
            uid,
            "broadcast_button_url",
            json.dumps(payload, ensure_ascii=False)
        )
        bot.send_message(
            chat_id,
            "🔗 <b>SEND BUTTON URL</b>\n\n"
            "Example: http://t.me/Nexo_store_bot"
        )
        return

    if state == "broadcast_button_url":
        try:
            payload = json.loads(data)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Broadcast session expired.", reply_markup=back_admin())
            return

        parsed = urlparse(incoming)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            bot.send_message(chat_id, "❌ Invalid URL. Use https://... or http://...")
            return

        payload["button_url"] = incoming
        set_state(
            uid,
            "broadcast_button_theme",
            json.dumps(payload, ensure_ascii=False)
        )

        kb = types.InlineKeyboardMarkup()
        kb.row(
            Button("🔵 PRIMARY / BLUE", callback_data="theme_primary"),
            Button("🟢 SUCCESS / GREEN", callback_data="theme_success"),
        )
        kb.add(Button("🔴 DANGER / RED", callback_data="theme_danger"))
        bot.send_message(
            chat_id,
            "🎨 <b>BUTTON THEME</b>\n\n"
            "Choose the button theme.",
            reply_markup=kb
        )
        return

    if state == "broadcast_message":
        clear_state(uid)
        do_broadcast(chat_id, incoming)
        return

    if state == "edit_product_name":
        pid = data
        with db_lock:
            conn = db()
            conn.execute("UPDATE products SET name=? WHERE id=?", (incoming, pid))
            conn.commit()
            conn.close()
        clear_state(uid)
        bot.send_message(chat_id, "✅ Product name updated.", reply_markup=back_admin())
        return

    if state == "edit_product_price":
        pid = data
        price = safe_float(incoming, -1)
        if price <= 0:
            bot.send_message(chat_id, "❌ Invalid price.")
            return
        with db_lock:
            conn = db()
            conn.execute("UPDATE products SET price=? WHERE id=?", (price, pid))
            conn.commit()
            conn.close()
        clear_state(uid)
        bot.send_message(chat_id, "✅ Product price updated.", reply_markup=back_admin())
        return

    if state == "edit_product_info":
        pid = data
        with db_lock:
            conn = db()
            conn.execute("UPDATE products SET info=? WHERE id=?", (incoming, pid))
            conn.commit()
            conn.close()
        clear_state(uid)
        bot.send_message(chat_id, "✅ Product information updated.", reply_markup=back_admin())
        return

    if state == "edit_product_select":
        # handled by callback in normal flow
        return

    if state == "admin_broadcast_link":
        clear_state(uid)
        do_broadcast(chat_id, incoming)
        return

    # Fallback
    clear_state(uid)
    send_home(chat_id, uid)

# ---------------- EDIT-IN-PLACE PAGE RENDERERS ----------------

def edit_current(call, text, markup=None):
    """Edit the existing callback message instead of creating another menu message."""
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        return True
    except Exception as e:
        logging.debug("edit_message_text fallback: %s", e)
        try:
            bot.send_message(call.message.chat.id, text, reply_markup=markup)
        except Exception:
            pass
        return False


def edit_home(call, user_id):
    markup = home_keyboard(user_id)
    try:
        bot.edit_message_media(
            types.InputMediaPhoto(WELCOME_IMAGE, caption=home_text()),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        return
    except Exception:
        edit_current(call, home_text(), markup)


def edit_profile(call, user_id):
    row = get_user(user_id)
    if not row:
        return
    username = f"@{row['username']}" if row["username"] else "Not set"
    status = "BANNED" if row["ban"] == "ok" else "ACTIVE"
    text = (
        "👤 <b>PROFILE</b>\n\n"
        f"🆔 User ID: <code>{row['id']}</code>\n"
        f"👤 Username: {esc(username)}\n"
        f"📝 Name: {esc(row['first_name'])}\n"
        f"💰 Balance: <b>{money(row['balance'])}</b>\n"
        f"📦 Total Orders: {row['order_count']}\n"
        f"💳 Total Deposits: {row['deposit_count']}\n"
        f"📤 Withdrawals: {row['withdrawal_count']}\n"
        f"👥 Referral Count: {row['referral_count']}\n"
        f"📌 Account Status: {status}"
    )
    kb = Button("💳 WALLET", callback_data="wallet")
    markup = types.InlineKeyboardMarkup()
    markup.row(kb, Button("📦 ORDERS", callback_data="orders"))
    markup.add(Button("🏠 HOME", callback_data="home", style="primary"))
    edit_current(call, text, markup)


def edit_wallet(call, user_id):
    user = get_user(user_id)
    markup = types.InlineKeyboardMarkup()
    markup.row(Button("💳 DEPOSIT", callback_data="deposit", style="primary"), Button("📤 WITHDRAW", callback_data="withdraw", style="danger"))
    markup.row(Button("🧾 TRANSACTIONS", callback_data="transactions"), Button("📦 ORDERS", callback_data="orders"))
    markup.add(Button("🏠 HOME", callback_data="home", style="primary"))
    text = (
        "💳 <b>WALLET</b>\n\n"
        f"💰 Balance: <b>{money(user['balance'])}</b>\n"
        f"📦 Orders: {user['order_count']}\n"
        f"💳 Deposits: {user['deposit_count']}\n"
        f"📤 Withdrawals: {user['withdrawal_count']}"
    )
    edit_current(call, text, markup)


def edit_orders(call, user_id):
    with db_lock:
        conn = db()
        rows = conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 20", (str(user_id),)).fetchall()
        conn.close()
    text = "📦 <b>MY ORDERS</b>\n\n"
    if not rows:
        text += "No orders."
    else:
        for r in rows:
            text += f"🧾 <code>{esc(r['id'])}</code>\n📦 {esc(r['product_name'])}\n💰 {money(r['total'])}\n📌 {esc(r['status'])}\n\n"
    edit_current(call, text, back_home())


def edit_transactions(call, user_id):
    with db_lock:
        conn = db()
        rows = conn.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC LIMIT 20", (str(user_id),)).fetchall()
        conn.close()
    text = "🧾 <b>TRANSACTIONS</b>\n\n"
    if not rows:
        text += "No transactions."
    else:
        for r in rows:
            text += f"🧾 <code>{esc(r['id'])}</code>\nType: {esc(r['type'])}\nAmount: {money(r['amount'])}\nStatus: {esc(r['status'])}\nTime: {esc(r['created_at'])}\n\n"
    edit_current(call, text, back_home())


def edit_usdt(call, user_id):
    buy = safe_float(get_setting("usdt_buy_rate", "0"))
    sell = safe_float(get_setting("usdt_sell_rate", "0"))
    markup = types.InlineKeyboardMarkup()
    markup.row(Button("💵 BUY USDT", callback_data="usdt_buy"), Button("💵 SELL USDT", callback_data="usdt_sell"))
    markup.add(Button("📋 MY REQUESTS", callback_data="usdt_requests"))
    markup.add(Button("🏠 HOME", callback_data="home", style="primary"))
    text = "💵 <b>USDT BUY / SELL</b>\n\n" + f"💵 BUY RATE: <b>{money(buy)}</b>\n💵 SELL RATE: <b>{money(sell)}</b>\n\nChoose an option:"
    edit_current(call, text, markup)


def edit_shop(call, user_id):
    with db_lock:
        conn = db()
        products = conn.execute("SELECT * FROM products WHERE status='active' AND available_stock>0 ORDER BY created_at DESC").fetchall()
        conn.close()
    markup = types.InlineKeyboardMarkup()
    if not products:
        markup.add(Button("🏠 HOME", callback_data="home", style="primary"))
        edit_current(call, "🛍️ <b>SHOP</b>\n\nThere are currently no products in stock.", markup)
        return
    product_buttons = []
    for p in products:
        style = {"blue":"primary", "green":"success", "red":"danger"}.get(str(p["color"] or "blue").lower(), "primary")
        product_buttons.append(Button(f"📦 {p['name']} — {product_money(p)}", callback_data=f"product_{p['id']}", style=style))
    for i in range(0, len(product_buttons), 2):
        markup.row(*product_buttons[i:i+2])
    markup.add(Button("🏠 HOME", callback_data="home", style="primary"))
    edit_current(call, "🛍️ <b>ɴᴇXᴏ SᴛᴏƦᴇ SHOP</b>\n\nSelect a product:", markup)


def edit_product(call, user_id, product_id):
    with db_lock:
        conn = db()
        p = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        conn.close()
    if not p:
        edit_current(call, "❌ Product not found.", back_home()); return
    if p["status"] != "active":
        edit_current(call, "❌ Product is inactive.", back_home()); return
    text = f"📦 <b>{esc(p['name'])}</b>\n\n💰 Price: <b>{product_money(p)}</b>\n📊 Available: <b>{p['available_stock']}</b>\n📊 Total Stock: <b>{p['total_stock']}</b>\n\n📝 {esc(p['info'])}"
    markup = types.InlineKeyboardMarkup()
    markup.row(Button("🛒 BUY NOW", callback_data=f"buy_{product_id}", style="success"), Button("🔙 SHOP", callback_data="shop", style="primary"))
    markup.add(Button("🏠 HOME", callback_data="home", style="primary"))
    edit_current(call, text, markup)


def show_admin_user_complete(chat_id, admin_id, target_id):
    """Detailed admin user information, including all counters and recent activity."""
    target = get_user(target_id)
    if not target:
        bot.send_message(chat_id, "❌ User not found.", reply_markup=back_admin())
        return
    with db_lock:
        conn = db()
        orders = conn.execute("SELECT COUNT(*) AS c FROM orders WHERE user_id=?", (str(target_id),)).fetchone()["c"]
        txs = conn.execute("SELECT COUNT(*) AS c FROM transactions WHERE user_id=?", (str(target_id),)).fetchone()["c"]
        deposits = conn.execute("SELECT COUNT(*) AS c FROM deposits WHERE user_id=?", (str(target_id),)).fetchone()["c"]
        withdrawals = conn.execute("SELECT COUNT(*) AS c FROM withdrawals WHERE user_id=?", (str(target_id),)).fetchone()["c"]
        conn.close()
    kb = types.InlineKeyboardMarkup()
    kb.row(Button("📦 ORDERS", callback_data="admin_user_orders"), Button("🧾 TRANSACTIONS", callback_data="admin_user_transactions"))
    kb.row(Button("➕ ADD BALANCE", callback_data="admin_add_balance"), Button("➖ REMOVE BALANCE", callback_data="admin_remove_balance"))
    kb.row(Button("💬 MESSAGE", callback_data="admin_user_message"), Button("🚫 BAN", callback_data="admin_ban"))
    kb.add(Button("✅ UNBAN", callback_data="admin_unban"))
    kb.add(Button("🔙 ADMIN", callback_data="admin"))
    text = (
        "👤 <b>COMPLETE USER INFORMATION</b>\n\n"
        f"🆔 User ID: <code>{esc(target['id'])}</code>\n"
        f"👤 Username: @{esc(target['username']) if target['username'] else 'Not set'}\n"
        f"📝 Name: {esc(target['first_name'])}\n"
        f"💰 Balance: <b>{money(target['balance'])}</b>\n"
        f"📅 Registered: <code>{esc(target['registered_at'])}</code>\n"
        f"👥 Referrer: <code>{esc(target['referrer'])}</code>\n"
        f"📦 Orders: <b>{orders}</b>\n"
        f"🧾 Transactions: <b>{txs}</b>\n"
        f"💳 Deposits: <b>{deposits}</b>\n"
        f"📤 Withdrawals: <b>{withdrawals}</b>\n"
        f"🚫 Status: <b>{'BANNED' if target['ban']=='ok' else 'ACTIVE'}</b>"
    )
    bot.send_message(chat_id, text, reply_markup=kb)


def admin_order_id_check(chat_id, order_id):
    oid = str(order_id).strip()
    with db_lock:
        conn = db()
        order = conn.execute("SELECT * FROM orders WHERE lower(id)=lower(?)", (oid,)).fetchone()
        tx = conn.execute("SELECT * FROM transactions WHERE lower(id)=lower(?)", (oid,)).fetchone()
        dep = conn.execute("SELECT * FROM deposits WHERE lower(id)=lower(?)", (oid,)).fetchone()
        wd = conn.execute("SELECT * FROM withdrawals WHERE lower(id)=lower(?)", (oid,)).fetchone()
        conn.close()
    if not any((order, tx, dep, wd)):
        bot.send_message(chat_id, f"❌ ID <code>{esc(oid)}</code> not found.", reply_markup=back_admin())
        return
    if order:
        text = ("🔎 <b>ORDER ID CHECK</b>\n\n" f"🧾 Order ID: <code>{esc(order['id'])}</code>\n" f"👤 User: <code>{esc(order['user_id'])}</code>\n" f"📦 Product: <b>{esc(order['product_name'])}</b>\n" f"💰 Total: <b>{money(order['total'])}</b>\n" f"🔢 Quantity: <b>{order['quantity']}</b>\n" f"📌 Status: <b>{esc(order['status'])}</b>\n" f"🕐 Created: <code>{esc(order['created_at'])}</code>\n" f"✅ Completed: <code>{esc(order['completed_at'])}</code>")
    elif tx:
        extra = tx['payment_information'] or tx['receiving_account']
        text = ("🔎 <b>TRANSACTION ID CHECK</b>\n\n" f"🧾 ID: <code>{esc(tx['id'])}</code>\n" f"👤 User: <code>{esc(tx['user_id'])}</code>\n" f"Type: <b>{esc(tx['type'])}</b>\n" f"💵 Amount: <b>{money(tx['amount'])}</b>\n" f"💱 Rate: <b>{money(tx['rate'])}</b>\n" f"💰 Total: <b>{money(tx['total'])}</b>\n" f"📌 Status: <b>{esc(tx['status'])}</b>\n" f"📋 Info: <code>{esc(extra)}</code>")
    elif dep:
        text = ("🔎 <b>DEPOSIT ID CHECK</b>\n\n" f"🧾 ID: <code>{esc(dep['id'])}</code>\n👤 User: <code>{esc(dep['user_id'])}</code>\n" f"💵 Amount: <b>{money(dep['amount'])}</b>\n📋 TXID: <code>{esc(dep['transaction_id'])}</code>\n📌 Status: <b>{esc(dep['status'])}</b>\n🕐 Created: <code>{esc(dep['created_at'])}</code>")
    else:
        text = ("🔎 <b>WITHDRAWAL ID CHECK</b>\n\n" f"🧾 ID: <code>{esc(wd['id'])}</code>\n👤 User: <code>{esc(wd['user_id'])}</code>\n" f"💵 Amount: <b>{money(wd['amount'])}</b>\n💳 Account: <code>{esc(wd['account'])}</code>\n📌 Status: <b>{esc(wd['status'])}</b>\n🕐 Created: <code>{esc(wd['created_at'])}</code>")
    bot.send_message(chat_id, text, reply_markup=back_admin())


# ---------------- V11 FORCE JOIN CALLBACKS ----------------

@bot.callback_query_handler(func=lambda call: str(call.data or "").startswith("v11_") and str(call.data or "") != "v11_settings")
def v11_callbacks(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id
    data = str(call.data or "")
    if not is_admin(uid) and data not in ("v11_check_join",):
        try:
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
        except Exception:
            pass
        return
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if data == "v11_check_join":
        if v11_all_channels_joined(uid):
            try:
                bot.edit_message_text(DEFAULT_WELCOME_MESSAGE, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=home_keyboard(uid))
            except Exception:
                send_home(chat_id, uid)
        else:
            try:
                bot.edit_message_text(
                    "🔒 <b>JOIN REQUIRED</b>\n\nPlease join all required chats, then press <b>CHECK JOIN</b> again.",
                    chat_id, call.message.message_id, parse_mode="HTML", reply_markup=v11_force_join_keyboard()
                )
            except Exception:
                bot.send_message(chat_id, "🔒 <b>JOIN REQUIRED</b>\n\nPlease join all required chats, then press <b>CHECK JOIN</b> again.", reply_markup=v11_force_join_keyboard())
        return

    if data == "v11_force_join_menu":
        current = v11_force_join_enabled()
        set_setting(FORCE_JOIN_KEY, "0" if current else "1")
        v11_send_settings(chat_id)
        return

    if data == "v11_force_join_add":
        set_state(uid, "v11_add_channel")
        bot.send_message(chat_id, "➕ <b>ADD REQUIRED CHAT</b>\n\nSend a public <code>@username</code> or <code>https://t.me/username</code>.\nSupported: Channel, Group, Supergroup.")
        return

    if data == "v11_force_join_remove":
        channels = v11_force_join_channels()
        if not channels:
            bot.send_message(chat_id, "ℹ️ No required chats added.", reply_markup=v11_settings_keyboard())
            return
        kb = types.InlineKeyboardMarkup()
        for ch in channels:
            kb.add(Button("🗑 " + v11_channel_label(ch), callback_data="v11_remove_" + ch.replace("@", "").replace("https://t.me/", "")))
        kb.add(Button("⬅️ Back", callback_data="v11_settings"))
        bot.send_message(chat_id, "🗑 <b>REMOVE REQUIRED CHAT</b>", reply_markup=kb)
        return

    if data.startswith("v11_remove_"):
        key = data[len("v11_remove_"):]
        channels = [x for x in v11_force_join_channels() if v11_channel_label(x).lstrip("@").lower() != key.lower()]
        set_setting(FORCE_JOIN_CHANNELS_KEY, json.dumps(channels, ensure_ascii=False))
        v11_send_settings(chat_id)
        return

    if data == "v11_force_join_style":
        kb = types.InlineKeyboardMarkup()
        kb.add(Button("🔵 BLUE", callback_data="v11_style_blue", style="primary"))
        kb.add(Button("🟢 GREEN", callback_data="v11_style_green", style="success"))
        kb.add(Button("🔴 RED", callback_data="v11_style_red", style="danger"))
        bot.send_message(chat_id, "🎨 <b>JOIN BUTTON COLOR</b>", reply_markup=kb)
        return

    if data in ("v11_style_blue", "v11_style_green", "v11_style_red"):
        set_setting(FORCE_JOIN_STYLE_KEY, data[len("v11_style_"):])
        v11_send_settings(chat_id)
        return

    if data == "v11_welcome_edit":
        set_state(uid, "v11_welcome")
        bot.send_message(chat_id, "✏️ <b>Send the new Welcome Message.</b>")
        return

# ---------------- CALLBACKS ----------------

@bot.callback_query_handler(func=lambda call: not str(call.data or "").startswith("v11_"))
def callbacks(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data or ""

    ensure_user(call.from_user)

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if banned(uid) and not is_admin(uid):
        bot.send_message(chat_id, "🚫 Your account is currently banned.")
        return

    if not is_admin(uid) and v11_force_join_enabled() and not v11_all_channels_joined(uid):
        bot.send_message(
            chat_id,
            "🔒 <b>JOIN REQUIRED</b>\n\nPlease join all required chats below, then press <b>CHECK JOIN</b>.",
            parse_mode="HTML",
            reply_markup=v11_force_join_keyboard()
        )
        return

    if data.startswith("product_color_"):
        if not is_admin(uid):
            return
        color = data[len("product_color_"):].lower()
        state, payload = get_state(uid)
        if state != "add_product_color" or color not in ("blue", "green", "red"):
            bot.send_message(chat_id, "❌ Product session expired.", reply_markup=back_admin())
            return
        try:
            draft = json.loads(payload)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Product session expired.", reply_markup=back_admin())
            return
        pid = new_id("P")
        with db_lock:
            conn = db()
            conn.execute("""
                INSERT INTO products(
                    id,name,price,currency,added_stock,available_stock,total_stock,
                    info,color,status,created_by,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                pid, draft["name"], float(draft["price"]), draft["currency"],
                int(draft["added_stock"]), int(draft["added_stock"]), int(draft["total_stock"]),
                "", color, "active", str(uid), now()
            ))
            conn.commit()
            conn.close()
        set_state(uid, "product_info", pid)
        bot.send_message(chat_id,
            "✅ <b>Product details received.</b>\n\n"
            f"📦 Product: {esc(draft['name'])}\n"
            f"💰 Price: {money(draft['price'])} {esc(draft['currency'])}\n"
            f"📊 Stock: {draft['added_stock']}/{draft['total_stock']}\n"
            f"🎨 Color: <b>{color.upper()}</b>\n\n"
            "📝 Now send the Product Information.")
        return

    if data == "home":
        clear_state(uid)
        edit_home(call, uid)
        return

    if data == "profile":
        clear_state(uid)
        edit_profile(call, uid)
        return

    if data == "shop":
        clear_state(uid)
        edit_shop(call, uid)
        return

    if data == "wallet":
        clear_state(uid)
        edit_wallet(call, uid)
        return

    if data == "orders":
        clear_state(uid)
        edit_orders(call, uid)
        return

    if data == "transactions":
        clear_state(uid)
        edit_transactions(call, uid)
        return

    if data == "deposit":
        start_deposit(chat_id, uid)
        return

    if data == "redeem":
        set_state(uid, "redeem_direct")
        bot.send_message(chat_id, "🎟️ <b>REDEEM CODE</b>\n\nSend your redeem code.", reply_markup=back_home())
        return

    if data == "withdraw":
        start_withdraw(chat_id, uid)
        return

    if data == "usdt":
        clear_state(uid)
        edit_usdt(call, uid)
        return

    if data == "usdt_buy":
        start_usdt_buy(chat_id, uid)
        return

    if data.startswith("usdt_buy_method_"):
        method = data[len("usdt_buy_method_"):].upper()
        state, payload = get_state(uid)
        if state != "usdt_buy_method":
            bot.send_message(chat_id, "❌ BUY session expired.", reply_markup=back_home())
            return
        try:
            amount, rate, total = map(float, payload.split("|"))
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Request expired.", reply_markup=back_home())
            return
        set_state(uid, "usdt_buy_address", f"{amount}|{rate}|{total}|{method}")
        bot.send_message(chat_id, f"📥 <b>{esc(method)}</b> selected.\n\nSend your <b>Address / ID / Account</b> where the USDT will be delivered.", reply_markup=back_home())
        return

    if data == "usdt_sell":
        start_usdt_sell(chat_id, uid)
        return

    if data == "usdt_requests":
        show_usdt_requests(chat_id, uid)
        return

    if data.startswith("product_"):
        clear_state(uid)
        edit_product(call, uid, data[len("product_"):])
        return

    if data.startswith("buy_"):
        start_buy(chat_id, uid, data[len("buy_"):])
        return

    if data == "confirm_buy":
        confirm_buy(chat_id, uid)
        return

    if data.startswith("receive_product_"):
        dep_id = data[len("receive_product_"):]
        with db_lock:
            conn = db()
            dep = conn.execute("SELECT * FROM deposits WHERE id=?", (dep_id,)).fetchone()
            conn.close()
        if not dep or str(dep["user_id"]) != str(uid) or dep["status"] != "approved" or not dep["product_name"]:
            bot.send_message(chat_id, "❌ This receive request is no longer available.", reply_markup=back_home())
            return
        product_name = dep["product_name"]
        sent = send_receive_to_support(uid, product_name, dep_id)
        kb = types.InlineKeyboardMarkup()
        kb.add(Button("🆘 OPEN SUPPORT", url=receive_support_url(product_name, dep_id), style="primary"))
        if sent:
            bot.send_message(chat_id, f"✅ <b>REQUEST SENT TO SUPPORT</b>\n\n📦 Product: <b>{esc(product_name)}</b>\n🧾 Deposit: <code>{esc(dep_id)}</code>", reply_markup=kb)
        else:
            bot.send_message(chat_id, f"📦 <b>RECEIVE REQUEST</b>\n\nProduct: <b>{esc(product_name)}</b>\n\nSupport could not be notified automatically. Press <b>OPEN SUPPORT</b>; the product name will be pre-filled.", reply_markup=kb)
        return

    # -------- ADMIN --------
    if data == "admin":
        show_admin(chat_id, uid)
        return

    if not is_admin(uid):
        bot.send_message(chat_id, "🚫 Unauthorized.")
        return

    if data == "admin_products":
        admin_products(chat_id)
        return

    if data == "admin_redeem":
        admin_redeem_menu(chat_id)
        return

    if data == "redeem_create":
        redeem_create_start(chat_id, uid)
        return

    if data == "redeem_list":
        redeem_list(chat_id)
        return

    if data == "admin_add_product":
        start_add_product(chat_id, uid)
        return

    if data == "admin_view_products":
        list_admin_products(chat_id)
        return

    if data == "admin_add_stock":
        admin_add_stock_start(chat_id, uid)
        return

    if data == "admin_remove_stock":
        admin_remove_stock_start(chat_id, uid)
        return

    if data.startswith("select_add_stock_"):
        stock_action(chat_id, uid, data[len("select_add_stock_"):], "add_stock")
        return

    if data.startswith("select_remove_stock_"):
        stock_action(chat_id, uid, data[len("select_remove_stock_"):], "remove_stock")
        return

    if data == "admin_delete_product":
        delete_product_start(chat_id, uid)
        return

    if data.startswith("delete_product_"):
        delete_product(chat_id, data[len("delete_product_"):])
        return

    if data == "admin_edit_product":
        edit_product_start(chat_id, uid)
        return

    if data.startswith("edit_product_"):
        pid = data[len("edit_product_"):]
        set_state(uid, "edit_product_menu", pid)
        kb = types.InlineKeyboardMarkup()
        kb.row(
            Button("✏️ NAME", callback_data=f"edit_name_{pid}"),
            Button("💰 PRICE", callback_data=f"edit_price_{pid}")
        )
        kb.row(
            Button("📝 INFO", callback_data=f"edit_info_{pid}"),
            Button("🔙 ADMIN", callback_data="admin")
        )
        bot.send_message(chat_id, "✏️ Select what to edit:", reply_markup=kb)
        return

    if data.startswith("edit_name_"):
        pid = data[len("edit_name_"):]
        set_state(uid, "edit_product_name", pid)
        bot.send_message(chat_id, "✏️ Send the new product name.")
        return

    if data.startswith("edit_price_"):
        pid = data[len("edit_price_"):]
        set_state(uid, "edit_product_price", pid)
        bot.send_message(chat_id, "💰 Send the new product price.")
        return

    if data.startswith("edit_info_"):
        pid = data[len("edit_info_"):]
        set_state(uid, "edit_product_info", pid)
        bot.send_message(chat_id, "📝 Send the new product information.")
        return

    if data == "admin_wallet":
        admin_wallet(chat_id)
        return

    if data == "admin_check_balance":
        start_user_lookup(chat_id, uid, "wallet_user", "🔎 Send user ID.")
        return

    if data == "admin_add_balance":
        state, selected = get_state(uid)
        if state == "admin_selected_user":
            set_state(uid, "wallet_add_amount", selected)
            bot.send_message(chat_id, f"➕ Send amount to add to <code>{selected}</code>.")
        else:
            start_user_lookup(chat_id, uid, "wallet_add_target", "➕ Send user ID.")
        return

    if data == "admin_remove_balance":
        state, selected = get_state(uid)
        if state == "admin_selected_user":
            set_state(uid, "wallet_minus_amount", selected)
            bot.send_message(chat_id, f"➖ Send amount to remove from <code>{selected}</code>.")
        else:
            start_user_lookup(chat_id, uid, "wallet_minus_target", "➖ Send user ID.")
        return

    if data == "admin_users":
        admin_users(chat_id)
        return

    if data == "admin_user":
        start_user_lookup(chat_id, uid, "user_lookup", "👤 Send user ID.")
        return

    if data == "admin_user_orders":
        state, selected = get_state(uid)
        if state == "admin_selected_user":
            with db_lock:
                conn = db()
                rows = conn.execute(
                    "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
                    (selected,)
                ).fetchall()
                conn.close()
            text = f"📦 <b>USER ORDERS</b>\n\nUser: <code>{selected}</code>\n\n"
            for r in rows:
                text += f"🧾 {r['id']} | {esc(r['product_name'])} | {money(r['total'])} | {r['status']}\n"
            bot.send_message(chat_id, text, reply_markup=back_admin())
        else:
            start_user_lookup(chat_id, uid, "admin_user_orders", "📦 Send user ID.")
        return

    if data == "admin_user_message":
        state, selected = get_state(uid)
        if state == "admin_selected_user":
            set_state(uid, "message_user_text", selected)
            bot.send_message(chat_id, f"💬 Send message to <code>{selected}</code>.")
        else:
            start_user_lookup(chat_id, uid, "message_user_target", "💬 Send user ID.")
        return

    if data == "admin_ban":
        state, selected = get_state(uid)
        if state == "admin_selected_user":
            with db_lock:
                conn = db()
                conn.execute("UPDATE users SET ban='ok' WHERE id=?", (selected,))
                conn.commit()
                conn.close()
            clear_state(uid)
            bot.send_message(chat_id, "🚫 User banned.", reply_markup=back_admin())
        else:
            start_user_lookup(chat_id, uid, "ban_user", "🚫 Send user ID.")
        return

    if data == "admin_unban":
        state, selected = get_state(uid)
        if state == "admin_selected_user":
            with db_lock:
                conn = db()
                conn.execute("UPDATE users SET ban='' WHERE id=?", (selected,))
                conn.commit()
                conn.close()
            clear_state(uid)
            bot.send_message(chat_id, "✅ User unbanned.", reply_markup=back_admin())
        else:
            start_user_lookup(chat_id, uid, "unban_user", "✅ Send user ID.")
        return

    if data == "admin_pending_orders":
        admin_pending_orders(chat_id)
        return

    if data.startswith("approve_order_"):
        approve_order(chat_id, uid, data[len("approve_order_"):])
        return

    if data.startswith("reject_order_"):
        reject_order(chat_id, uid, data[len("reject_order_"):])
        return

    if data == "admin_orders":
        admin_orders(chat_id)
        return

    if data == "admin_order_check":
        set_state(uid, "admin_order_check")
        bot.send_message(chat_id, "🔎 <b>ADMIN ORDER ID CHECK</b>\n\nSend Order ID / Transaction ID / Deposit ID / Withdrawal ID.", reply_markup=back_admin())
        return

    if data == "admin_user_transactions":
        state, selected = get_state(uid)
        if state == "admin_selected_user":
            with db_lock:
                conn = db()
                rows = conn.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC LIMIT 30", (selected,)).fetchall()
                conn.close()
            text = f"🧾 <b>USER TRANSACTIONS</b>\n\nUser: <code>{selected}</code>\n\n"
            for r in rows:
                text += f"🧾 <code>{esc(r['id'])}</code> | {esc(r['type'])} | {money(r['amount'])} | {esc(r['status'])}\n"
            bot.send_message(chat_id, text, reply_markup=back_admin())
        else:
            bot.send_message(chat_id, "❌ Select a user first.", reply_markup=back_admin())
        return

    if data == "admin_deposits":
        admin_deposits(chat_id)
        return

    if data == "admin_withdrawals":
        admin_withdrawals(chat_id)
        return

    if data == "admin_statistics":
        admin_statistics(chat_id)
        return

    if data == "admin_payment_settings":
        admin_payment_settings(chat_id)
        return

    if data == "set_payment_phone":
        set_state(uid, "payment_phone")
        bot.send_message(chat_id, "📱 Send the Telebirr payment number.")
        return

    if data == "set_payment_manager":
        set_state(uid, "payment_manager")
        bot.send_message(chat_id, "👤 Send the account manager name/username.")
        return

    if data == "set_usdt_buy_rate":
        set_state(uid, "usdt_buy_rate")
        bot.send_message(chat_id, "💵 Send the new USDT BUY rate.")
        return

    if data == "set_usdt_sell_rate":
        set_state(uid, "usdt_sell_rate")
        bot.send_message(chat_id, "💵 Send the new USDT SELL rate.")
        return

    if data == "admin_admins":
        admin_admins(chat_id)
        return

    if data == "add_admin":
        set_state(uid, "add_admin")
        bot.send_message(chat_id, "➕ Send the Telegram user ID to add as admin.")
        return

    if data == "remove_admin":
        set_state(uid, "remove_admin")
        bot.send_message(chat_id, "➖ Send the Telegram user ID to remove.")
        return

    if data == "admin_settings":
        admin_settings(chat_id)
        return

    if data == "admin_message_user":
        start_user_lookup(chat_id, uid, "message_user_target", "💬 Send user ID.")
        return

    if data == "admin_broadcast":
        admin_broadcast_start(chat_id, uid)
        return

    if data == "broadcast_share":
        state, payload = get_state(uid)
        if state != "broadcast_preview":
            bot.send_message(chat_id, "❌ Preview expired.", reply_markup=back_admin())
            return
        try:
            obj = json.loads(payload)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Preview expired.", reply_markup=back_admin())
            return
        broadcast_finish(
            chat_id, uid, obj["target"], obj["content"],
            obj.get("button_text", ""), obj.get("button_url", ""),
            obj.get("button_style")
        )
        return

    if data == "broadcast_edit":
        state, payload = get_state(uid)
        if state != "broadcast_preview":
            bot.send_message(chat_id, "❌ Preview expired.", reply_markup=back_admin())
            return
        try:
            obj = json.loads(payload)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Preview expired.", reply_markup=back_admin())
            return
        set_state(uid, "broadcast_content", obj["target"])
        bot.send_message(chat_id, "✏️ <b>EDIT BROADCAST</b>\n\nSend the new text/media. This will replace the previous preview.", reply_markup=back_admin())
        return

    if data == "broadcast_cancel":
        clear_state(uid)
        bot.send_message(chat_id, "❌ Broadcast cancelled.", reply_markup=back_admin())
        return

    if data == "broadcast_target_users":
        broadcast_content_prompt(chat_id, uid, "users")
        return

    if data == "broadcast_target_group":
        broadcast_content_prompt(chat_id, uid, "group")
        return

    if data == "broadcast_button_yes":
        state, payload = get_state(uid)
        if state != "broadcast_button":
            bot.send_message(chat_id, "❌ Broadcast session expired.")
            return
        try:
            obj = json.loads(payload)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Broadcast session expired.", reply_markup=back_admin())
            return
        set_state(
            uid,
            "broadcast_button_text",
            json.dumps(obj, ensure_ascii=False)
        )
        bot.send_message(chat_id, "✏️ <b>SEND BUTTON TEXT</b>\n\nExample: Open Store")
        return

    if data == "broadcast_button_no":
        state, payload = get_state(uid)
        if state != "broadcast_button":
            bot.send_message(chat_id, "❌ Broadcast session expired.")
            return
        try:
            obj = json.loads(payload)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Broadcast session expired.", reply_markup=back_admin())
            return
        obj["button_text"] = ""
        obj["button_url"] = ""
        set_state(uid, "broadcast_preview", json.dumps(obj, ensure_ascii=False))
        send_broadcast_preview(chat_id, obj)
        return

    if data in ("theme_primary", "theme_success", "theme_danger"):
        state, payload = get_state(uid)
        if state != "broadcast_button_theme":
            bot.send_message(chat_id, "❌ Broadcast session expired.")
            return
        try:
            obj = json.loads(payload)
        except Exception:
            clear_state(uid)
            bot.send_message(chat_id, "❌ Broadcast session expired.", reply_markup=back_admin())
            return
        theme = data.replace("theme_", "")
        obj["button_style"] = theme
        set_state(uid, "broadcast_preview", json.dumps(obj, ensure_ascii=False))
        send_broadcast_preview(chat_id, obj)
        return

    if data == "toggle_group_log":
        current = get_setting("group_log_enabled", "1")
        set_setting("group_log_enabled", "0" if current == "1" else "1")
        admin_settings(chat_id)
        return

    if data == "button_theme_menu":
        kb = types.InlineKeyboardMarkup()
        kb.row(
            Button("🔵 PRIMARY / BLUE", callback_data="set_theme_primary"),
            Button("🟢 SUCCESS / GREEN", callback_data="set_theme_success"),
        )
        kb.add(Button("🔴 DANGER / RED", callback_data="set_theme_danger"))
        kb.add(Button("🔙 SETTINGS", callback_data="admin_settings"))
        bot.send_message(chat_id, "🎨 <b>BUTTON THEME</b>\n\nChoose a theme.", reply_markup=kb)
        return

    if data in ("set_theme_blue", "set_theme_green", "set_theme_red", "set_theme_gold"):
        theme = data.replace("set_theme_", "")
        set_setting("button_theme", theme)
        bot.send_message(chat_id, f"✅ Button theme set to <b>{theme.upper()}</b>.", reply_markup=back_admin())
        return

    if data == "set_group_log_photo":
        set_state(uid, "group_log_photo")
        bot.send_message(
            chat_id,
            "🖼️ <b>SET GROUP LOG PHOTO</b>\n\n"
            "Send an image URL. Send <code>off</code> to disable the photo."
        )
        return

    if data == "set_usdt_sell_address":
        set_state(uid, "usdt_sell_address")
        bot.send_message(
            chat_id,
            "📤 <b>SET USDT SELL ADDRESS</b>\n\n"
            "Send the USDT wallet/address where users must send USDT when selling."
        )
        return

    if data.startswith("approve_deposit_"):
        approve_deposit(chat_id, uid, data[len("approve_deposit_"):])
        return

    if data.startswith("reject_deposit_"):
        reject_deposit(chat_id, uid, data[len("reject_deposit_"):])
        return

    if data.startswith("approve_withdraw_"):
        approve_withdraw(chat_id, uid, data[len("approve_withdraw_"):])
        return

    if data.startswith("reject_withdraw_"):
        reject_withdraw(chat_id, uid, data[len("reject_withdraw_"):])
        return

    if data.startswith("approve_usdt_"):
        approve_usdt(chat_id, uid, data[len("approve_usdt_"):])
        return

    if data.startswith("reject_usdt_"):
        reject_usdt(chat_id, uid, data[len("reject_usdt_"):])
        return

# ---------------- ADMIN ACTIONS ----------------


def send_receive_to_support(user_id, product_name, dep_id):
    product_name = str(product_name or "").strip() or "Unknown Product"
    msg = (
        "📦 <b>PRODUCT RECEIVE REQUEST</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"📦 Product: <b>{esc(product_name)}</b>\n"
        f"🧾 Deposit ID: <code>{esc(dep_id)}</code>"
    )
    # If the support account has already started the bot, notify it automatically.
    try:
        bot.send_message(SUPPORT_ACCOUNT, msg)
        return True
    except Exception:
        return False

def receive_support_url(product_name, dep_id):
    text = f"Hello, I want to receive: {product_name} (Deposit: {dep_id})"
    return "https://t.me/IRORE0?text=" + quote(text)

def approve_deposit(chat_id, admin_id, dep_id):
    with db_lock:
        conn = db()
        dep = conn.execute(
            "SELECT * FROM deposits WHERE id=?",
            (dep_id,)
        ).fetchone()

        if not dep:
            conn.close()
            bot.send_message(chat_id, "❌ Deposit not found.")
            return

        if dep["status"] != "pending":
            conn.close()
            bot.send_message(chat_id, "⚠️ Deposit already processed.")
            return

        conn.execute("""
            UPDATE deposits
            SET status='approved', approved_by=?
            WHERE id=?
        """, (str(admin_id), dep_id))

        bonus = 0.0
        if dep["redeem_code"]:
            claim = conn.execute("""SELECT rc.*, cl.id AS claim_id, cl.status AS claim_status, cl.bonus AS claim_bonus
                                   FROM redeem_codes rc JOIN redeem_claims cl ON cl.code_id=rc.id
                                   WHERE cl.user_id=? AND upper(rc.code)=upper(?) AND cl.deposit_id=?""",
                                (dep["user_id"], dep["redeem_code"], dep["id"])).fetchone()
            if claim and claim["claim_status"] == "reserved":
                bonus = float(claim["claim_bonus"])
                conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (float(dep["amount"])+bonus, dep["user_id"]))
                conn.execute("UPDATE redeem_claims SET status='approved', approved_at=? WHERE id=?", (now(), claim["claim_id"]))
            else:
                conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (float(dep["amount"]), dep["user_id"]))
        else:
            conn.execute(
                "UPDATE users SET balance=balance+? WHERE id=?",
                (float(dep["amount"]), dep["user_id"])
            )

        conn.execute("""
            INSERT INTO transactions(
                id,user_id,type,amount,status,created_at,approved_by
            ) VALUES(?,?,?,?,?,?,?)
        """, (
            new_id("TX"),
            dep["user_id"],
            "deposit",
            float(dep["amount"]),
            "completed",
            now(),
            str(admin_id)
        ))

        if bonus > 0:
            conn.execute("INSERT INTO transactions(id,user_id,type,amount,status,created_at,approved_by) VALUES(?,?,?,?,?,?,?)",
                         (new_id("RBX"), dep["user_id"], "redeem_bonus", bonus, "completed", now(), str(admin_id)))
        conn.commit()
        conn.close()

    try:
        newbal = get_user(dep["user_id"])["balance"]
        product_name = str(dep["product_name"] or "").strip() if "product_name" in dep.keys() else ""
        if product_name:
            kb = types.InlineKeyboardMarkup()
            kb.add(Button("📦 RECEIVE", callback_data=f"receive_product_{dep['id']}", style="success"))
            kb.add(Button("🆘 SUPPORT", url=SUPPORT))
            bot.send_message(
                int(dep["user_id"]),
                "✅ <b>YOUR DEPOSIT APPROVED</b>\n\n"
                f"📦 Product: <b>{esc(product_name)}</b>\n"
                f"💵 Deposit: <b>{money(dep['amount'])} ETB</b>\n"
                f"💰 New Balance: <b>{money(newbal)} ETB</b>\n\n"
                "Your payment was approved. Press <b>RECEIVE</b> to request this product from support.",
                reply_markup=kb
            )
        else:
            bot.send_message(
                int(dep["user_id"]),
                "✅ <b>YOUR DEPOSIT APPROVED</b>\n\n"
                f"💵 Amount: <b>{money(dep['amount'])} ETB</b>\n"
                f"💰 New Balance: <b>{money(newbal)} ETB</b>",
                reply_markup=back_home()
            )
    except Exception:
        logging.exception("Could not notify deposit approval")

    bot.send_message(
        chat_id,
        f"✅ <b>DEPOSIT APPROVED</b>\n\n"
        f"💵 Amount: {money(dep['amount'])}\n"
        f"📦 Product: <b>{esc(dep['product_name']) if 'product_name' in dep.keys() and dep['product_name'] else 'Wallet Deposit'}</b>",
        reply_markup=back_admin()
    )

def reject_deposit(chat_id, admin_id, dep_id):
    with db_lock:
        conn = db()
        dep = conn.execute(
            "SELECT * FROM deposits WHERE id=?",
            (dep_id,)
        ).fetchone()

        if not dep:
            conn.close()
            bot.send_message(chat_id, "❌ Deposit not found.")
            return

        if dep["status"] != "pending":
            conn.close()
            bot.send_message(chat_id, "⚠️ Deposit already processed.")
            return

        conn.execute("""
            UPDATE deposits
            SET status='rejected', rejected_by=?
            WHERE id=?
        """, (str(admin_id), dep_id))
        if dep["redeem_code"]:
            claim = conn.execute("SELECT * FROM redeem_claims WHERE user_id=? AND deposit_id=? AND status='reserved'", (dep["user_id"], dep_id)).fetchone()
            if claim:
                conn.execute("DELETE FROM redeem_claims WHERE id=?", (claim["id"],))
                conn.execute("UPDATE redeem_codes SET claims_count=CASE WHEN claims_count>0 THEN claims_count-1 ELSE 0 END WHERE id=?", (claim["code_id"],))
        conn.commit()
        conn.close()

    try:
        bot.send_message(
            int(dep["user_id"]),
            "❌ <b>DEPOSIT REJECTED</b>\n\n"
            f"📦 Product: <b>{esc(dep['product_name']) if 'product_name' in dep.keys() and dep['product_name'] else 'Wallet Deposit'}</b>\n\n"
            "Please contact @IRORE0."
        )
    except Exception:
        pass

    bot.send_message(chat_id, "❌ Deposit rejected.", reply_markup=back_admin())

def approve_withdraw(chat_id, admin_id, wid):
    with db_lock:
        conn = db()
        w = conn.execute(
            "SELECT * FROM withdrawals WHERE id=?",
            (wid,)
        ).fetchone()

        if not w:
            conn.close()
            bot.send_message(chat_id, "❌ Withdrawal not found.")
            return

        if w["status"] != "pending":
            conn.close()
            bot.send_message(chat_id, "⚠️ Withdrawal already processed.")
            return

        user = conn.execute(
            "SELECT balance FROM users WHERE id=?",
            (w["user_id"],)
        ).fetchone()

        if not user or float(user["balance"]) < float(w["amount"]):
            conn.close()
            bot.send_message(chat_id, "❌ User no longer has enough balance.")
            return

        conn.execute(
            "UPDATE users SET balance=balance-? WHERE id=?",
            (float(w["amount"]), w["user_id"])
        )
        conn.execute("""
            UPDATE withdrawals
            SET status='approved', approved_by=?
            WHERE id=?
        """, (str(admin_id), wid))
        conn.execute("""
            INSERT INTO transactions(
                id,user_id,type,amount,status,created_at,approved_by
            ) VALUES(?,?,?,?,?,?,?)
        """, (
            new_id("TX"),
            w["user_id"],
            "withdrawal",
            float(w["amount"]),
            "completed",
            now(),
            str(admin_id)
        ))
        conn.commit()
        conn.close()

    try:
        bot.send_message(
            int(w["user_id"]),
            "✅ <b>WITHDRAWAL APPROVED</b>\n\n"
            f"💵 Amount: <b>{money(w['amount'])}</b>\n"
            f"💳 Account: <code>{esc(w['account'])}</code>"
        )
    except Exception:
        pass

    bot.send_message(chat_id, "✅ Withdrawal approved.", reply_markup=back_admin())

def reject_withdraw(chat_id, admin_id, wid):
    with db_lock:
        conn = db()
        w = conn.execute(
            "SELECT * FROM withdrawals WHERE id=?",
            (wid,)
        ).fetchone()

        if not w:
            conn.close()
            bot.send_message(chat_id, "❌ Withdrawal not found.")
            return

        if w["status"] != "pending":
            conn.close()
            bot.send_message(chat_id, "⚠️ Withdrawal already processed.")
            return

        conn.execute("""
            UPDATE withdrawals
            SET status='rejected', rejected_by=?
            WHERE id=?
        """, (str(admin_id), wid))
        conn.commit()
        conn.close()

    try:
        bot.send_message(
            int(w["user_id"]),
            "❌ <b>WITHDRAWAL REJECTED</b>\n\n"
            "Please contact @IRORE0."
        )
    except Exception:
        pass

    bot.send_message(chat_id, "❌ Withdrawal rejected.", reply_markup=back_admin())

def usdt_success_group_log(transaction_row):
    r = transaction_row
    user = get_user(r["user_id"])
    username = (user or {}).get("username", "")
    username_text = f"@{esc(username)}" if username else f"<code>{esc(r['user_id'])}</code>"

    if r["type"] == "usdt_buy":
        payout_info = str(r["payment_information"] or "")
        if ":" in payout_info:
            payout_method, payout_value = payout_info.split(":", 1)
        else:
            payout_method, payout_value = "TELEBIRR", payout_info
        payout = mask_account(payout_value.strip())
        text = (
            "💵 <b>USDT BOUGHT SUCCESSFULLY</b>\n\n"
            f"💰 Amount: <b>{money(r['amount'])} USDT</b>\n"
            f"🏦 Delivery method: <b>{esc(payout_method.upper())}</b>\n"
            f"💵 ETB paid: <b>{money(r['total'])} ETB</b>\n"
            f"📤 Payout: <b>{esc(payout_method)} {esc(payout)}</b>\n\n"
            "☑️ <i>Have USDT to sell? Submit your transfer and receive ETB quickly.</i>\n"
            "🛍️ <b>Open the bot to buy, sell, or order now.</b>"
        )
    else:
        delivery = mask_account(r["receiving_account"])
        text = (
            "💵 <b>USDT SOLD SUCCESSFULLY</b>\n\n"
            f"💰 Amount: <b>{money(r['amount'])} USDT</b>\n"
            f"📤 Delivery: <b>TELEBIRR → {esc(delivery)}</b>\n"
            f"💵 ETB payment: <b>{money(r['total'])} ETB</b>\n\n"
            "☑️ <i>Need USDT? Buy securely and receive it at your preferred crypto destination.</i>\n"
            "🛍️ <b>Open the bot to buy, sell, or order now.</b>"
        )

    ok = send_group_log(text)
    logging.info(
        "USDT success group log: user=%s username=%s type=%s sent=%s",
        r["user_id"], username_text, r["type"], ok
    )
    return ok


def usdt_request_admin_notify(user_id, request_id):
    with db_lock:
        conn = db()
        r = conn.execute(
            "SELECT * FROM transactions WHERE id=?",
            (request_id,)
        ).fetchone()
        conn.close()

    if not r:
        return

    user = get_user(user_id)
    kb = types.InlineKeyboardMarkup()
    kb.row(
        Button(
            "✅ APPROVE",
            callback_data=f"approve_usdt_{request_id}"
        ),
        Button(
            "❌ REJECT",
            callback_data=f"reject_usdt_{request_id}"
        )
    )

    extra = (
        f"💳 Payment Info:\n{esc(r['payment_information'])}"
        if r["type"] == "usdt_buy"
        else f"💳 Receiving Account:\n{esc(r['receiving_account'])}"
    )

    text = (
        f"💵 <b>NEW {r['type'].upper().replace('_',' ')}</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"👤 Username: @{esc(user['username'] if user else '')}\n"
        f"💵 USDT Amount: <b>{money(r['amount'])}</b>\n"
        f"💱 Rate: <b>{money(r['rate'])}</b>\n"
        f"💰 Total: <b>{money(r['total'])}</b>\n"
        f"{extra}\n\n"
        "📌 Status: <b>PENDING</b>"
    )
    notify_admins(text, kb)

def approve_usdt(chat_id, admin_id, request_id):
    with db_lock:
        conn = db()
        r = conn.execute(
            "SELECT * FROM transactions WHERE id=?",
            (request_id,)
        ).fetchone()

        if not r:
            conn.close()
            bot.send_message(chat_id, "❌ USDT request not found.")
            return

        if r["status"] != "pending":
            conn.close()
            bot.send_message(chat_id, "⚠️ USDT request already processed.")
            return

        conn.execute("""
            UPDATE transactions
            SET status='approved', approved_by=?
            WHERE id=?
        """, (str(admin_id), request_id))
        conn.commit()
        conn.close()

    try:
        bot.send_message(
            int(r["user_id"]),
            "✅ <b>USDT REQUEST APPROVED</b>\n\n"
            f"💵 Type: {esc(r['type'])}\n"
            f"💵 USDT: {money(r['amount'])}\n"
            f"💰 Total: {money(r['total'])}\n\n"
            "Please coordinate delivery/payment with support."
        )
    except Exception:
        pass

    bot.send_message(
        chat_id,
        "✅ USDT request approved.\n\n"
        "⚠️ No blockchain/payment verification was performed.",
        reply_markup=back_admin()
    )

    # Publish a success log to the configured group.
    usdt_success_group_log(r)

def reject_usdt(chat_id, admin_id, request_id):
    with db_lock:
        conn = db()
        r = conn.execute(
            "SELECT * FROM transactions WHERE id=?",
            (request_id,)
        ).fetchone()

        if not r:
            conn.close()
            bot.send_message(chat_id, "❌ USDT request not found.")
            return

        if r["status"] != "pending":
            conn.close()
            bot.send_message(chat_id, "⚠️ USDT request already processed.")
            return

        conn.execute("""
            UPDATE transactions
            SET status='rejected', rejected_by=?
            WHERE id=?
        """, (str(admin_id), request_id))
        conn.commit()
        conn.close()

    try:
        bot.send_message(
            int(r["user_id"]),
            "❌ <b>USDT REQUEST REJECTED</b>\n\n"
            "Please contact @IRORE0."
        )
    except Exception:
        pass

    bot.send_message(chat_id, "❌ USDT request rejected.", reply_markup=back_admin())

# ---------------- STARTUP ----------------


# =========================
# V11 SETTINGS ENTRY FIX
# =========================
@bot.callback_query_handler(func=lambda call: str(call.data or "") == "v11_settings")
def v11_settings_entry_callback(call):
    if not is_admin(call.from_user.id):
        try:
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
        except Exception:
            pass
        return

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    settings_text = "⚙️ <b>V11 SETTINGS</b>\n\nSelect an option below:"
    try:
        bot.edit_message_text(
            settings_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=v11_settings_keyboard(),
        )
    except Exception as e:
        print("V11 SETTINGS ERROR:", repr(e))
        try:
            bot.send_message(
                call.message.chat.id,
                settings_text,
                parse_mode="HTML",
                reply_markup=v11_settings_keyboard(),
            )
        except Exception as e2:
            print("V11 SETTINGS SEND ERROR:", repr(e2))


if __name__ == "__main__":
    init_db()
    logging.info("ɴᴇXᴏ SᴛᴏƦᴇ Python bot VERSION 11 starting...")
    logging.info("Master admin: %s", MASTER_ADMIN)
    logging.info("Main group: %s", MAIN_GROUP)
    bot.infinity_polling(
        skip_pending=True,
        allowed_updates=["message", "callback_query"]
    )
