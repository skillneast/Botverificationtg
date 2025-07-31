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
WEBSITE_URL = os.environ.get('WEBSITE_URL', 'https://render.com')
FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
FIREBASE_KEY_BASE64 = os.environ.get('FIREBASE_KEY_BASE64')
TOKEN_VALIDITY_MINUTES = 15

# --- Firebase Setup ---
# ... (Firebase setup code is the same) ...

# --- BOT & FLASK INITIALIZATION ---
app = Flask(__name__)
try:
    bot = telegram.Bot(token=TOKEN)
    dispatcher = Dispatcher(bot, None, use_context=True, workers=4)
except Exception as e:
    logger.critical(f"FATAL: Bot initialization failed. TOKEN is likely wrong. Error: {e}")
    exit()

# --- BOT FUNCTIONS ---
def start(update: Update, context: CallbackContext):
    # ... (Start function is the same) ...
    welcome_text = "🚀 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗸𝗶𝗹𝗹𝗻𝗲𝗮𝘀𝘁!*\n\n" + \
                   "📚 *𝗚𝗲𝘁 𝗙𝗿𝗲𝗲 𝗔𝗰𝗰𝗲𝘀𝘀 𝘁𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗼𝗻𝘁𝗲𝗻𝘁* —\n" #...and so on
    
    keyboard = [
        [InlineKeyboardButton("📩 Join Skillneast", url=f"https://t.me/{CHANNEL_1_USERNAME}")],
        [InlineKeyboardButton("📩 Join Skillneast Backup", url=f"https://t.me/{CHANNEL_2_USERNAME}")],
        [InlineKeyboardButton("✅ I Joined", callback_data='check_join')],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')


# --- YEH FUNCTION BADLA GAYA HAI ---
def check_join_status(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    logger.info(f"Checking membership for user {user_id}...")
    
    try:
        # Step 1: Pehle channel ko check karo
        logger.info(f"Checking channel 1: @{CHANNEL_1_USERNAME}")
        member1 = context.bot.get_chat_member(chat_id=f"@{CHANNEL_1_USERNAME}", user_id=user_id)
        if member1.status in ['left', 'kicked']:
            logger.warning(f"User {user_id} is not in channel 1. Status: {member1.status}")
            query.answer("❌ You are not in the first channel. Please join.", show_alert=True)
            return

        # Step 2: Doosre channel ko check karo
        logger.info(f"Checking channel 2: @{CHANNEL_2_USERNAME}")
        member2 = context.bot.get_chat_member(chat_id=f"@{CHANNEL_2_USERNAME}", user_id=user_id)
        if member2.status in ['left', 'kicked']:
            logger.warning(f"User {user_id} is not in channel 2. Status: {member2.status}")
            query.answer("❌ You are not in the second channel. Please join.", show_alert=True)
            return

        # Step 3: Agar sab theek hai, to token do
        logger.info(f"User {user_id} is in both channels. Granting token.")
        generate_and_send_token(query, user_id)

    except Exception as e:
        # YEH SABSE ZAROORI HISSA HAI
        # Yeh hamein Telegram se mila hua asli error dikhayega
        logger.error(f"--- REAL TELEGRAM API ERROR --- for user {user_id}: {e}")
        query.answer("Error. Could not verify membership. Check server logs for details.", show_alert=True)


def generate_and_send_token(query, user_id):
    # ... (Generate token function is the same) ...
    pass

# ... (baaki ka poora code neeche hai, usse copy kar lein) ...

# --- Full functions to avoid errors ---
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
    return 'Bot is alive and running!'
