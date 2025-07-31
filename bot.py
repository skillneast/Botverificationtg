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

# --- Setup ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION (Load everything first) ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
CHANNEL_1_ID_STR = os.environ.get('CHANNEL_1_ID')
CHANNEL_2_ID_STR = os.environ.get('CHANNEL_2_ID')
WEBSITE_URL = os.environ.get('WEBSITE_URL', 'https://render.com')
FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
FIREBASE_KEY_BASE64 = os.environ.get('FIREBASE_KEY_BASE64')
TOKEN_VALIDITY_MINUTES = 15
OWNER_USERNAME = "neasthub" # Hardcoded

# --- STARTUP CHECKS ---
if not TOKEN:
    logger.critical("FATAL: TELEGRAM_BOT_TOKEN environment variable is not set!")
    exit()
if not WEBHOOK_URL:
    logger.critical("FATAL: WEBHOOK_URL environment variable is not set!")
    exit()
try:
    CHANNEL_1_ID = int(CHANNEL_1_ID_STR)
    CHANNEL_2_ID = int(CHANNEL_2_ID_STR)
except (ValueError, TypeError):
    logger.critical(f"FATAL: CHANNEL IDs are not valid integers! Check your environment variables.")
    exit()

# --- FIREBASE SETUP ---
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
    logger.error(f"Firebase initialization failed: {e}")

# --- BOT & FLASK INITIALIZATION ---
app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)
# NOTE: v13.x of the library requires use_context=True
dispatcher = Dispatcher(bot, None, use_context=True, workers=4)

# --- BOT FUNCTIONS ---
def start(update: Update, context: CallbackContext):
    """Sends welcome message."""
    welcome_text = (
        "🚀 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗸𝗶𝗹𝗹𝗻𝗲𝗮𝘀𝘁!*\n\n"
        "📚 *𝗚𝗲𝘁 𝗙𝗿𝗲𝗲 𝗔𝗰𝗰𝗲𝘀𝘀 𝘁𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗼𝗻𝘁𝗲𝗻𝘁* —\n"
        "*𝗖𝗼𝘂𝗿𝘀𝗲𝘀, 𝗣𝗗𝗙 𝗕𝗼𝗼𝗸𝘀, 𝗣𝗮𝗶𝗱 𝗧𝗶𝗽𝘀 & 𝗧𝗿𝗶𝗰𝗸𝘀, 𝗦𝗸𝗶𝗹𝗹-𝗕𝗮𝘀𝗲𝗱 𝗠𝗮𝘁𝗲𝗿𝗶𝗮𝗹 & 𝗠𝗼𝗿𝗲!*\n\n"
        "🧠 *𝗠𝗮𝘀𝘁𝗲𝗿 𝗡𝗲𝘄 𝗦𝗸𝗶𝗹𝗹𝘀 & 𝗟𝗲𝗮𝗿𝗻 𝗪𝗵𝗮𝘁 𝗥𝗲𝗮𝗹𝗹𝘆 𝗠𝗮𝘁𝘁𝗲𝗿𝘀* — *𝟭𝟬𝟬% 𝗙𝗥𝗘𝗘!*\n\n"
        "💸 *𝗔𝗹𝗹 𝗧𝗼𝗽 𝗖𝗿𝗲𝗮𝘁𝗼𝗿𝘀' 𝗣𝗮𝗶𝗱 𝗖𝗼𝘂𝗿𝘀𝗲𝘀 𝗮𝘁 𝗡𝗼 𝗖𝗼𝘀𝘁!*\n\n"
        "🔐 *𝗔𝗰𝗰𝗲𝘀𝘀 𝗶𝘀 𝘀𝗲𝗰𝘂𝗿𝗲𝗱 𝘃𝗶𝗮 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗺𝗲𝗺𝗯𝗲𝗿𝘀𝗵𝗶𝗽.*\n\n"
        "👉 *𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝘁𝗵𝗲 𝗯𝗲𝗹𝗼𝘄 𝗰𝗵𝗮𝗻𝗻𝗲𝗹𝘀 𝘁𝗼 𝘂𝗻𝗹𝗼𝗰𝗸 𝘆𝗼𝘂𝗿 𝗱𝗮𝗶𝗹𝘆 𝗮𝗰𝗰𝗲𝘀𝘀 𝘁𝗼𝗸𝗲𝗻* 👇"
    )
    # Using hardcoded usernames for links, as per your request
    keyboard = [
        [InlineKeyboardButton("📩 Join Skillneast", url="https://t.me/skillneastreal")],
        [InlineKeyboardButton("📩 Join Skillneast Backup", url="https://t.me/skillneast")],
        [InlineKeyboardButton("✅ I Joined", callback_data='check_join')],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

def check_join_status(update: Update, context: CallbackContext):
    """Checks channel membership."""
    query = update.callback_query
    user_id = query.from_user.id
    try:
        member1 = context.bot.get_chat_member(chat_id=CHANNEL_1_ID, user_id=user_id)
        member2 = context.bot.get_chat_member(chat_id=CHANNEL_2_ID, user_id=user_id)
        if member1.status not in ['left', 'kicked'] and member2.status not in ['left', 'kicked']:
            generate_and_send_token(query, user_id)
        else:
            query.answer("❌ Please join both channels first!", show_alert=True)
    except Exception as e:
        logger.error(f"Error in check_join_status for user {user_id}: {e}")
        query.answer("Error. Make sure bot is an admin in both channels and you have joined.", show_alert=True)

def generate_and_send_token(query, user_id):
    """Generates and sends the token."""
    token = secrets.token_hex(8).upper()
    current_time_seconds = int(time.time())
    expiry_timestamp_seconds = current_time_seconds + (TOKEN_VALIDITY_MINUTES * 60)
    
    try:
        ref = db.reference(f'users/{user_id}')
        ref.set({'token': token, 'expiry_timestamp': expiry_timestamp_seconds, 'used': False})
    except Exception as e:
        logger.error(f"Firebase DB error for user {user_id}: {e}")
        query.answer("Could not save your token. Please try again.", show_alert=True)
        return
        
    access_text = (
        "🎉 *Access Granted!*\n\n"
        f"Here is your one-time token, valid for *{TOKEN_VALIDITY_MINUTES} minutes*:\n\n`{token}`\n\n"
        "✅ Paste this on the website to continue!"
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
dispatcher.add_handler(CallbackQueryHandler(check_join_status, pattern='^check_join$'))


# --- FLASK ROUTES ---
@app.route(f'/{TOKEN}', methods=['POST'])
def respond():
    """Processes updates from Telegram."""
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    """Sets the webhook."""
    s = bot.set_webhook(f'{WEBHOOK_URL}/{TOKEN}')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route('/')
def index():
    """A simple page to show the bot is alive."""
    return 'Bot is alive and running with webhook!'
