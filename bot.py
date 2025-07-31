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

# --- CONFIGURATION ---
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
CHANNEL_1_USERNAME = os.environ.get('CHANNEL_1_USERNAME')
CHANNEL_2_USERNAME = os.environ.get('CHANNEL_2_USERNAME')
OWNER_USERNAME = os.environ.get('OWNER_USERNAME')
WEBSITE_URL = os.environ.get('WEBSITE_URL')
FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
FIREBASE_KEY_BASE64 = os.environ.get('FIREBASE_KEY_BASE64')
TOKEN_VALIDITY_MINUTES = 15

# --- Firebase Setup ---
# ... (Firebase setup code is the same) ...
try:
    if FIREBASE_KEY_BASE64:
        decoded_key = base64.b64decode(FIREBASE_KEY_BASE64)
        firebase_key_dict = json.loads(decoded_key)
        cred = credentials.Certificate(firebase_key_dict)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})
        logger.info("Firebase initialized successfully.")
except Exception as e:
    logger.critical(f"FATAL: Firebase initialization failed. Error: {e}")
    exit()


# --- BOT & FLASK INITIALIZATION ---
app = Flask(__name__)
# IMPORTANT: Updater ko yahan initialize karna hai taaki JobQueue mil sake
updater = Updater(TOKEN)
dispatcher = updater.dispatcher
job_queue = updater.job_queue

# --- BOT FUNCTIONS ---

def start(update: Update, context: CallbackContext):
    """Sends the welcome message."""
    # ... (Start function is the same) ...
    welcome_text = "🚀 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗸𝗶𝗹𝗹𝗻𝗲𝗮𝘀𝘁!*\n\n" # ... and so on
    keyboard = [
        [InlineKeyboardButton("📩 Join Skillneast", url=f"https://t.me/{CHANNEL_1_USERNAME}")],
        [InlineKeyboardButton("📩 Join Skillneast Backup", url=f"https://t.me/{CHANNEL_2_USERNAME}")],
        [InlineKeyboardButton("✅ I Joined", callback_data='get_token')],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')


# --- YEH FUNCTION BADLA GAYA HAI ---
def get_token_handler(update: Update, context: CallbackContext):
    """Schedules the token sending job after a delay, without blocking."""
    query = update.callback_query
    
    # Turant message edit karo aur Telegram ko jawab de do
    query.edit_message_text(text="🔄 *Verifying your status... Please wait.*", parse_mode='Markdown')
    
    # Data jo humein 5 second baad wale function mein chahiye
    job_context = {
        'chat_id': query.message.chat_id,
        'message_id': query.message.message_id,
        'user_id': query.from_user.id
    }
    
    # 5 second baad `send_token_job` function ko chalao
    context.job_queue.run_once(send_token_job, 5, context=job_context, name=f"token_job_{query.from_user.id}")
    
    query.answer() # Button click ka jawab do

# --- YEH NAYA FUNCTION HAI ---
def send_token_job(context: CallbackContext):
    """This function is called by the JobQueue after 5 seconds."""
    job = context.job
    chat_id = job.context['chat_id']
    message_id = job.context['message_id']
    user_id = job.context['user_id']
    
    logger.info(f"5-second job running for user {user_id}")
    
    # Token generate karo
    token = secrets.token_hex(8).upper()
    current_time_seconds = int(time.time())
    expiry_timestamp_seconds = current_time_seconds + (TOKEN_VALIDITY_MINUTES * 60)
    
    try:
        ref = db.reference(f'users/{user_id}')
        ref.set({'token': token, 'expiry_timestamp': expiry_timestamp_seconds, 'used': False})
    except Exception as e:
        logger.error(f"Firebase DB error during job for user {user_id}: {e}")
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="❌ An error occurred while saving your token. Please try again."
        )
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
    
    # Message ko edit karke token dikhao
    context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=access_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


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
    return 'Bot is alive!'
