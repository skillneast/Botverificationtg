import os
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import firebase_admin
from firebase_admin import credentials, db
import secrets
import json
import base64
import time
from flask import Flask, request
import logging

# Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION (Sab kuch yahan set hai) ---

# Yeh Render ke Environment Variables se aayenge
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
FIREBASE_KEY_BASE64 = os.environ.get('FIREBASE_KEY_BASE64')

# Yeh humne seedhe code mein daal diye hain (Hardcoded)
CHANNEL_1_USERNAME = "skillneastreal"
CHANNEL_2_USERNAME = "skillneast"
OWNER_USERNAME = "neasthub"
WEBSITE_URL = "https://skillneast.github.io/Skillneast/#"
TOKEN_VALIDITY_MINUTES = 15

# --- Firebase Setup ---
try:
    if FIREBASE_KEY_BASE64:
        decoded_key = base64.b64decode(FIREBASE_KEY_BASE64)
        firebase_key_dict = json.loads(decoded_key)
        cred = credentials.Certificate(firebase_key_dict)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})
        logger.info("Firebase initialized successfully.")
    else:
        logger.warning("Firebase key not found. Database features will fail.")
except Exception as e:
    logger.critical(f"FATAL: Firebase initialization failed. Error: {e}")
    exit()

# --- BOT & FLASK INITIALIZATION ---
app = Flask(__name__)
updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

# --- BOT FUNCTIONS ---

def start(update: Update, context: CallbackContext):
    """Sends the welcome message."""
    # Aapka naya description
    welcome_text = (
        "🚀 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗸𝗶𝗹𝗹𝗻𝗲𝗮𝘀𝘁!*\n\n"
        "📚 *𝗚𝗲𝘁 𝗙𝗿𝗲𝗲 𝗔𝗰𝗰𝗲𝘀𝘀 𝘁𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗼𝗻𝘁𝗲𝗻𝘁* —\n"
        "*𝗖𝗼𝘂𝗿𝘀𝗲𝘀, 𝗣𝗗𝗙 𝗕𝗼𝗼𝗸𝘀, 𝗣𝗮𝗶𝗱 𝗧𝗶𝗽𝘀 & 𝗧𝗿𝗶𝗰𝗸𝘀, 𝗦𝗸𝗶𝗹𝗹-𝗕𝗮𝘀𝗲𝗱 𝗠𝗮𝘁𝗲𝗿𝗶𝗮𝗹 & 𝗠𝗼𝗿𝗲!*\n\n"
        "🧠 *𝗠𝗮𝘀𝘁𝗲𝗿 𝗡𝗲𝘄 𝗦𝗸𝗶𝗹𝗹𝘀 & 𝗟𝗲𝗮𝗿𝗻 𝗪𝗵𝗮𝘁 𝗥𝗲𝗮𝗹𝗹𝘆 𝗠𝗮𝘁𝘁𝗲𝗿𝘀* — *𝟭𝟬𝟬% 𝗙𝗥𝗘𝗘!*\n\n"
        "💸 *𝗔𝗹𝗹 𝗧𝗼𝗽 𝗖𝗿𝗲𝗮𝘁𝗼𝗿𝘀' 𝗣𝗮𝗶𝗱 𝗖𝗼𝘂𝗿𝘀𝗲𝘀 𝗮𝘁 𝗡𝗼 𝗖𝗼𝘀𝘁!*\n\n"
        "🔐 *𝗔𝗰𝗰𝗲𝘀𝘀 𝗶𝘀 𝘀𝗲𝗰𝘂𝗿𝗲𝗱 𝘃𝗶𝗮 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗺𝗲𝗺𝗯𝗲𝗿𝘀𝗵𝗶𝗽.*\n\n"
        "👉 *𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝘁𝗵𝗲 𝗯𝗲𝗹𝗼𝘄 𝗰𝗵𝗮𝗻𝗻𝗲𝗹𝘀 𝘁𝗼 𝘂𝗻𝗹𝗼𝗰𝗸 𝘆𝗼𝘂𝗿 𝗱𝗮𝗶𝗹𝘆 𝗮𝗰𝗰𝗲𝘀𝘀 𝘁𝗼𝗸𝗲𝗻* 👇"
    )
    # Buttons mein bhi hardcoded values use hongi
    keyboard = [
        [InlineKeyboardButton("📩 Join Skillneast", url=f"https://t.me/{CHANNEL_1_USERNAME}")],
        [InlineKeyboardButton("📩 Join Skillneast Backup", url=f"https://t.me/{CHANNEL_2_USERNAME}")],
        [InlineKeyboardButton("✅ I Joined", callback_data='get_token')],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

def get_token_handler(update: Update, context: CallbackContext):
    """Generates and sends the token instantly."""
    query = update.callback_query
    user_id = query.from_user.id
    
    logger.info(f"User {user_id} clicked 'I Joined'. Generating token instantly.")
    
    token_string = f"{secrets.token_hex(6).upper()}/{secrets.token_hex(6).upper()}"
    current_time_seconds = int(time.time())
    expiry_timestamp_seconds = current_time_seconds + (TOKEN_VALIDITY_MINUTES * 60)
    
    try:
        ref = db.reference(f'users/{user_id}')
        ref.set({'token': token_string, 'expiry_timestamp': expiry_timestamp_seconds, 'used': False})
    except Exception as e:
        logger.error(f"Firebase DB error for user {user_id}: {e}")
        query.answer("❌ An error occurred while generating your token. Please try again.", show_alert=True)
        return
    
    access_text = (
        "🎉 *Access Granted!*\n\n"
        "Here is your _one-time token_ for today:\n\n"
        f"`{token_string}`\n\n"
        "✅ Paste this on the website to continue!\n"
        "⚠️ *Note: If you leave any channel later, your access will be revoked automatically.*"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔐 Access Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=access_text, reply_markup=reply_markup, parse_mode='Markdown')
    query.answer("✅ Token Generated!")

# --- HANDLER REGISTRATION ---
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(get_token_handler, pattern='^get_token$'))

# --- FLASK ROUTES ---
@app.route(f'/{TOKEN}', methods=['POST'])
def respond():
    update = Update.de_json(request.get_json(force=True), updater.bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    s = updater.bot.set_webhook(f'{WEBHOOK_URL}/{TOKEN}')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route('/')
def index():
    return 'Bot is alive and running!'
