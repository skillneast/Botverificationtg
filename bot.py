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

# --- CONFIGURATION (Sabse pehle load karo) ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
CHANNEL_1_ID_STR = os.environ.get('CHANNEL_1_ID')
CHANNEL_2_ID_STR = os.environ.get('CHANNEL_2_ID')
WEBSITE_URL = os.environ.get('WEBSITE_URL', 'https://render.com')
FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
FIREBASE_KEY_BASE64 = os.environ.get('FIREBASE_KEY_BASE64')
TOKEN_VALIDITY_MINUTES = 15
OWNER_USERNAME = "neasthub" # Hardcoded

# --- STARTUP CHECKS (Sabse Zaroori) ---
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
    logger.critical(f"FATAL: CHANNEL_1_ID ('{CHANNEL_1_ID_STR}') or CHANNEL_2_ID ('{CHANNEL_2_ID_STR}') are not valid integers!")
    exit()

# --- FIREBASE SETUP ---
try:
    if FIREBASE_KEY_BASE64:
        # ... (Firebase setup code) ...
        pass
except Exception as e:
    logger.error(f"Firebase initialization failed: {e}")


# --- BOT & FLASK INITIALIZATION ---
app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True, workers=4)


# --- BOT FUNCTIONS ---
def start(update: Update, context: CallbackContext):
    # ... (Start function ka poora code) ...

def check_join_status(update: Update, context: CallbackContext):
    # ... (check_join_status function ka poora code) ...

def generate_and_send_token(query, user_id):
    # ... (generate_and_send_token function ka poora code) ...


# --- HANDLER REGISTRATION ---
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(check_join_status, pattern='^check_join$'))


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
    return 'Bot is alive!'


# --- POORA CODE YAHAN PASTE KARNA HAI ---
# (Yahan main functions dobara de raha hoon taaki koi galti na ho)

def start(update: Update, context: CallbackContext):
    welcome_text = (
        "🚀 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗸𝗶𝗹𝗹𝗻𝗲𝗮𝘀𝘁!*\n\n"
        "📚 *𝗚𝗲𝘁 𝗙𝗿𝗲𝗲 𝗔𝗰𝗰𝗲𝘀𝘀 𝘁𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗼𝗻𝘁𝗲𝗻𝘁* —\n"
        # ... (baaki ka welcome text)
    )
    keyboard = [
        [InlineKeyboardButton("📩 Join Skillneast", url=f"https://t.me/{'skillneastreal'}")],
        [InlineKeyboardButton("📩 Join Skillneast Backup", url=f"https://t.me/{'skillneast'}")],
        [InlineKeyboardButton("✅ I Joined", callback_data='check_join')],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

def check_join_status(update: Update, context: CallbackContext):
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
        query.answer("Error. Make sure bot is an admin and you have joined.", show_alert=True)

def generate_and_send_token(query, user_id):
    # ... (generate_and_send_token function ka poora code) ...
    pass
