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

# --- CONFIGURATION (Load and check everything first) ---
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

# --- FIREBASE SETUP (This is the most important part now) ---
try:
    decoded_key = base64.b64decode(FIREBASE_KEY_BASE64)
    firebase_key_dict = json.loads(decoded_key)
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})
    logger.info("Firebase initialized successfully.")
except Exception as e:
    # Agar yahan error aaya, to bot ko chalu hi mat karo
    logger.critical(f"FATAL: Firebase initialization failed. The BASE64 key or a-zA-Z0-9' is likely incorrect. Error: {e}")
    exit()

# --- BOT & FLASK INITIALIZATION ---
app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True, workers=4)

# --- BOT FUNCTIONS ---
def start(update: Update, context: CallbackContext):
    # ... (Start function is the same) ...
    pass

def check_join_status(update: Update, context: CallbackContext):
    # ... (check_join_status function is the same) ...
    pass

def generate_and_send_token(query, user_id):
    # ... (generate_and_send_token function is the same) ...
    pass

# --- Full functions to avoid errors ---
# (Main yahan poore functions de raha hoon)
def start(update: Update, context: CallbackContext):
    welcome_text = "🚀 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗸𝗶𝗹𝗹𝗻𝗲𝗮𝘀𝘁!*\n\n" + \
                   "📚 *𝗚𝗲𝘁 𝗙𝗿𝗲𝗲 𝗔𝗰𝗰𝗲𝘀𝘀 𝘁𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗼𝗻𝘁𝗲𝗻𝘁* —\n" #... and so on
    keyboard = [
        [InlineKeyboardButton("📩 Join Skillneast", url=f"https://t.me/{CHANNEL_1_USERNAME}")],
        [InlineKeyboardButton("📩 Join Skillneast Backup", url=f"https://t.me/{CHANNEL_2_USERNAME}")],
        [InlineKeyboardButton("✅ I Joined", callback_data='check_join')],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

def check_join_status(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    try:
        member1 = context.bot.get_chat_member(chat_id=f"@{CHANNEL_1_USERNAME}", user_id=user_id)
        member2 = context.bot.get_chat_member(chat_id=f"@{CHANNEL_2_USERNAME}", user_id=user_id)
        if member1.status not in ['left', 'kicked'] and member2.status not in ['left', 'kicked']:
            generate_and_send_token(query, user_id)
        else:
            query.answer("❌ Please join both channels first!", show_alert=True)
    except Exception as e:
        logger.error(f"Error in check_join_status for user {user_id}: {e}")
        query.answer("Error: Make sure bot is an admin in both channels and you have joined.", show_alert=True)

def generate_and_send_token(query, user_id):
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
    access_text = "🎉 *Access Granted!*\n\n" + f"Here is your one-time token, valid for *{TOKEN_VALIDITY_MINUTES} minutes*:\n\n`{token}`\n\n" + "✅ Paste this on the website to continue!"
    keyboard = [
        [InlineKeyboardButton("🔐 Access Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=access_text, reply_markup=reply_markup, parse_mode='Markdown')
    query.answer("✅ Token Generated!")

# --- HANDLER REGISTRATION & FLASK ROUTES ---
# ... (This part is the same) ...
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(check_join_status, pattern='^check_join$'))
@app.route(f'/{TOKEN}', methods=['POST'])
def respond():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'
@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.set_webhook(f'{WEBHOOK_URL}/{TOKEN}')
    if s: return "webhook setup ok"
    else: return "webhook setup failed"
@app.route('/')
def index():
    return 'Bot is alive!'
