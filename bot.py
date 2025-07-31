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
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
CHANNEL_1_ID = "skillneastreal"
CHANNEL_2_ID = "skillneast"
OWNER_USERNAME = "neasthub"

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBSITE_URL = os.environ.get('WEBSITE_URL', 'https://render.com')
FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
FIREBASE_KEY_BASE64 = os.environ.get('FIREBASE_KEY_BASE64')
TOKEN_VALIDITY_MINUTES = 15

# --- SETUP FUNCTIONS ---
def check_env_variables():
    required_vars = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "WEBSITE_URL": WEBSITE_URL,
        "FIREBASE_DATABASE_URL": FIREBASE_DATABASE_URL,
        "FIREBASE_KEY_BASE64": FIREBASE_KEY_BASE64
    }
    missing_vars = [key for key, value in required_vars.items() if not value]
    if missing_vars:
        error_message = f"CRITICAL: Missing environment variables: {', '.join(missing_vars)}"
        print(error_message)
        exit()
    print("All environment variables loaded successfully.")

def initialize_firebase():
    try:
        decoded_key = base64.b64decode(FIREBASE_KEY_BASE64)
        firebase_key_dict = json.loads(decoded_key)
        cred = credentials.Certificate(firebase_key_dict)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})
        print("Firebase initialized successfully.")
    except Exception as e:
        print(f"CRITICAL: Firebase initialization failed: {e}")
        exit()

# --- BOT FUNCTIONS ---
def start(update: Update, context: CallbackContext):
    welcome_text = (
        "🚀 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗸𝗶𝗹𝗹𝗻𝗲𝗮𝘀𝘁!*\n\n"
        "📚 *𝗚𝗲𝘁 𝗙𝗿𝗲𝗲 𝗔𝗰𝗰𝗲𝘀𝘀 𝘁𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗼𝗻𝘁𝗲𝗻𝘁* —\n"
        "*𝗖𝗼𝘂𝗿𝘀𝗲𝘀, 𝗣𝗗𝗙 𝗕𝗼𝗼𝗸𝘀, 𝗣𝗮𝗶𝗱 𝗧𝗶𝗽𝘀 & 𝗧𝗿𝗶𝗰𝗸𝘀, 𝗦𝗸𝗶𝗹𝗹-𝗕𝗮𝘀𝗲𝗱 𝗠𝗮𝘁𝗲𝗿𝗶𝗮𝗹 & 𝗠𝗼𝗿𝗲!*\n\n"
        "🧠 *𝗠𝗮𝘀𝘁𝗲𝗿 𝗡𝗲𝘄 𝗦𝗸𝗶𝗹𝗹𝘀 & 𝗟𝗲𝗮𝗿𝗻 𝗪𝗵𝗮𝘁 𝗥𝗲𝗮𝗹𝗹𝘆 𝗠𝗮𝘁𝘁𝗲𝗿𝘀* — *𝟭𝟬𝟬% 𝗙𝗥𝗘𝗘!*\n\n"
        "💸 *𝗔𝗹𝗹 𝗧𝗼𝗽 𝗖𝗿𝗲𝗮торы' 𝗣𝗮𝗶𝗱 𝗖𝗼𝘂𝗿𝘀𝗲𝘀 𝗮𝘁 𝗡𝗼 𝗖𝗼𝘀𝘁!*\n\n"
        "🔐 *𝗔𝗰𝗰𝗲𝘀𝘀 𝗶𝘀 𝘀𝗲𝗰𝘂𝗿𝗲𝗱 𝘃𝗶𝗮 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗺𝗲𝗺𝗯𝗲𝗿𝘀𝗵𝗶𝗽.*\n\n"
        "👉 *𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝘁𝗵𝗲 𝗯𝗲𝗹𝗼𝘄 𝗰𝗵𝗮𝗻𝗻𝗲𝗹𝘀 𝘁𝗼 𝘂𝗻𝗹𝗼𝗰𝗸 𝘆𝗼𝘂𝗿 𝗱𝗮𝗶𝗹𝘆 𝗮𝗰𝗰𝗲𝘀𝘀 𝘁𝗼𝗸𝗲𝗻* 👇"
    )
    channel1_url = f"https://t.me/{CHANNEL_1_ID}"
    channel2_url = f"https://t.me/{CHANNEL_2_ID}"
    owner_url = f"https://t.me/{OWNER_USERNAME}"
    keyboard = [
        [InlineKeyboardButton("📩 Join Skillneast", url=channel1_url)],
        [InlineKeyboardButton("📩 Join Skillneast Backup", url=channel2_url)],
        [InlineKeyboardButton("✅ I Joined", callback_data='check_join')],
        [InlineKeyboardButton("👑 Owner", url=owner_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

def check_join_status(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    try:
        status1 = context.bot.get_chat_member(chat_id=f"@{CHANNEL_1_ID}", user_id=user_id)
        status2 = context.bot.get_chat_member(chat_id=f"@{CHANNEL_2_ID}", user_id=user_id)
        
        if status1.status in ['member', 'administrator', 'creator'] and \
           status2.status in ['member', 'administrator', 'creator']:
            generate_and_send_token(query, user_id)
        else:
            query.answer("❌ Please join both channels first!", show_alert=True)
    except Exception as e:
        print(f"Error in check_join_status: {e}")
        query.answer("An error occurred. Please try again.", show_alert=True)

def generate_and_send_token(query, user_id):
    token = secrets.token_hex(8).upper()
    current_time_seconds = int(time.time())
    expiry_timestamp_seconds = current_time_seconds + (TOKEN_VALIDITY_MINUTES * 60)
    
    ref = db.reference(f'users/{user_id}')
    ref.set({'token': token, 'expiry_timestamp': expiry_timestamp_seconds, 'used': False})
    
    access_text = (
        "🎉 *Access Granted!*\n\n"
        f"Here is your one-time token, valid for *{TOKEN_VALIDITY_MINUTES} minutes*:\n\n"
        f"`{token}`\n\n"
        "✅ Paste this on the website to continue!"
    )
    keyboard = [
        [InlineKeyboardButton("🔐 Access Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=access_text, reply_markup=reply_markup, parse_mode='Markdown')
    query.answer("✅ Token Generated!")

# --- WEB SERVER & BOT STARTUP ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive and running!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# YAHAN BADLAV KIYA GAYA HAI
def run_bot():
    print("Bot thread started")
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(check_join_status, pattern='^check_join$'))
    
    print("Bot is starting polling...")
    updater.start_polling()
    print("Bot is now polling.")
    # `idle()` ko thread mein chalane se kabhi-kabhi problem aati hai,
    # isliye hum use hata rahe hain. Thread chalta rahega.

# Main execution block
if __name__ == "__main__":
    check_env_variables()
    initialize_firebase()
    
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    
    print("Web server is starting...")
    run_web_server()
