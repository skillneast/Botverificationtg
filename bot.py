import os
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, Dispatcher
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

# --- CONFIGURATION (Load everything from environment variables) ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
CHANNEL_1_USERNAME = os.environ.get('CHANNEL_1_USERNAME')
CHANNEL_2_USERNAME = os.environ.get('CHANNEL_2_USERNAME')
OWNER_USERNAME = os.environ.get('OWNER_USERNAME')
WEBSITE_URL = os.environ.get('WEBSITE_URL')
FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
FIREBASE_KEY_BASE64 = os.environ.get('FIREBASE_KEY_BASE64')
TOKEN_VALIDITY_MINUTES = 15

# --- CRITICAL STARTUP CHECKS ---
if not all([TOKEN, WEBHOOK_URL, CHANNEL_1_USERNAME, CHANNEL_2_USERNAME, OWNER_USERNAME, WEBSITE_URL, FIREBASE_DATABASE_URL, FIREBASE_KEY_BASE64]):
    logger.critical("FATAL: One or more environment variables are missing! Please check all variables on Render.")
    exit()

# --- FIREBASE SETUP ---
try:
    decoded_key = base64.b64decode(FIREBASE_KEY_BASE64)
    firebase_key_dict = json.loads(decoded_key)
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})
    logger.info("Firebase initialized successfully.")
except Exception as e:
    logger.critical(f"FATAL: Firebase initialization failed. The BASE64 key or URL is likely incorrect. Error: {e}")
    exit()

# --- BOT & FLASK INITIALIZATION ---
app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True, workers=4)

# --- BOT FUNCTIONS ---
def start(update: Update, context: CallbackContext):
    """Sends the welcome message."""
    welcome_text = (
        "🚀 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗸𝗶𝗹𝗹𝗻𝗲𝗮𝘀𝘁!*\n\n"
        "📚 *𝗚𝗲𝘁 𝗙𝗿𝗲𝗲 𝗔𝗰𝗰𝗲𝘀𝘀 𝘁𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗼𝗻𝘁𝗲𝗻𝘁* —\n"
        "*𝗖𝗼𝘂𝗿𝘀𝗲𝘀, 𝗣𝗗𝗙 𝗕𝗼𝗼𝗸𝘀, 𝗣𝗮𝗶𝗱 𝗧𝗶𝗽𝘀 & 𝗧𝗿𝗶𝗰𝗸𝘀, 𝗦𝗸𝗶𝗹𝗹-𝗕𝗮𝘀𝗲𝗱 𝗠𝗮𝘁𝗲𝗿𝗶𝗮𝗹 & 𝗠𝗼𝗿𝗲!*\n\n"
        "🧠 *𝗠𝗮𝘀𝘁𝗲𝗿 𝗡𝗲𝘄 𝗦𝗸𝗶𝗹𝗹𝘀 & 𝗟𝗲𝗮𝗿𝗻 𝗪𝗵𝗮𝘁 𝗥𝗲𝗮𝗹𝗹𝘆 𝗠𝗮𝘁𝘁𝗲𝗿𝘀* — *𝟭𝟬𝟬% 𝗙𝗥𝗘𝗘!*\n\n"
        "💸 *𝗔𝗹𝗹 𝗧𝗼𝗽 𝗖𝗿𝗲𝗮𝘁𝗼𝗿𝘀' 𝗣𝗮𝗶𝗱 𝗖𝗼𝘂𝗿𝘀𝗲𝘀 𝗮𝘁 𝗡𝗼 𝗖𝗼𝘀𝘁!*\n\n"
        "🔐 *𝗔𝗰𝗰𝗲𝘀𝘀 𝗶𝘀 𝘀𝗲𝗰𝘂𝗿𝗲𝗱 𝘃𝗶𝗮 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗺𝗲𝗺𝗯𝗲𝗿𝘀𝗵𝗶𝗽.*\n\n"
        "👉 *𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝘁𝗵𝗲 𝗯𝗲𝗹𝗼𝘄 𝗰𝗵𝗮𝗻𝗻𝗲𝗹𝘀 𝘁𝗼 𝘂𝗻𝗹𝗼𝗰𝗸 𝘆𝗼𝘂𝗿 𝗱𝗮𝗶𝗹𝘆 𝗮𝗰𝗰𝗲𝘀𝘀 𝘁𝗼𝗸𝗲𝗻* 👇"
    )
    keyboard = [
        [InlineKeyboardButton("📩 Join Skillneast", url=f"https://t.me/{CHANNEL_1_USERNAME}")],
        [InlineKeyboardButton("📩 Join Skillneast Backup", url=f"https://t.me/{CHANNEL_2_USERNAME}")],
        [InlineKeyboardButton("✅ I Joined", callback_data='get_token')],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# --- YEH FUNCTION POORI TARAH SE NAYA HAI ---
def get_token_handler(update: Update, context: CallbackContext):
    """
    Sends a 'Verifying...' message, waits 5 seconds, then generates the token.
    This function does NOT check for channel membership.
    """
    query = update.callback_query
    user_id = query.from_user.id
    
    # Step 1: User ko ek temporary message dikhao
    verifying_text = "🔄 *Verifying your status... Please wait.*"
    query.edit_message_text(text=verifying_text, parse_mode='Markdown')
    
    # Step 2: 5 second ka intezaar karo
    time.sleep(5)
    
    # Step 3: Token generate aur send karo
    token = secrets.token_hex(8).upper()
    current_time_seconds = int(time.time())
    expiry_timestamp_seconds = current_time_seconds + (TOKEN_VALIDITY_MINUTES * 60)
    
    try:
        ref = db.reference(f'users/{user_id}')
        ref.set({'token': token, 'expiry_timestamp': expiry_timestamp_seconds, 'used': False})
        logger.info(f"Token generated for user {user_id}")
    except Exception as e:
        logger.error(f"Firebase DB error for user {user_id}: {e}")
        query.edit_message_text("❌ An error occurred while generating your token. Please try again.")
        return
        
    access_text = (
        "✅ *Verification Complete!*\n\n"
        "🎉 *Access Granted!*\n\n"
        f"Here is your one-time token. It's valid for *{TOKEN_VALIDITY_MINUTES} minutes*:\n\n"
        f"`{token}`\n\n"
        "Copy this token and paste it on our website to continue."
    )
    keyboard = [
        [InlineKeyboardButton("🔐 Access Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # "Verifying..." message ko edit karke token wala message dikhao
    query.edit_message_text(text=access_text, reply_markup=reply_markup, parse_mode='Markdown')


# --- HANDLER REGISTRATION ---
dispatcher.add_handler(CommandHandler("start", start))
# Hum `get_token_handler` ko 'get_token' callback se jod rahe hain
dispatcher.add_handler(CallbackQueryHandler(get_token_handler, pattern='^get_token$'))

# --- FLASK ROUTES ---
@app.route(f'/{TOKEN}', methods=['POST'])
def respond():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.set_webhook(f'{WEBHOOK_URL}/{TOKEN}')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route('/')
def index():
    return 'Bot is alive and running!'
