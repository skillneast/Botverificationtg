import os
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import firebase_admin
from firebase_admin import credentials, db # <- YAHAN FIRESTORE KI JAGAH 'db' IMPORT KIYA HAI
import secrets
import json
import base64
import time # <- UNIX timestamp ke liye 'time' import kiya hai

# --- CONFIGURATION (Render Environment Variables se aayega) ---
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHANNEL_1_ID = os.environ.get('CHANNEL_1_ID')
CHANNEL_2_ID = os.environ.get('CHANNEL_2_ID')
WEBSITE_URL = os.environ.get('WEBSITE_URL')
OWNER_USERNAME = os.environ.get('OWNER_USERNAME')
TOKEN_VALIDITY_MINUTES = 15

# Aapke Realtime Database ka URL
FIREBASE_DATABASE_URL = 'https://adminneast-default-rtdb.firebaseio.com'

# --- FIREBASE SETUP ---
try:
    encoded_key = os.environ.get('FIREBASE_KEY_BASE64')
    decoded_key = base64.b64decode(encoded_key)
    firebase_key_dict = json.loads(decoded_key)
    cred = credentials.Certificate(firebase_key_dict)
    # YAHAN DATABASE URL ADD KARNA ZAROORI HAI
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DATABASE_URL
    })
except Exception as e:
    print(f"CRITICAL: Firebase initialization failed: {e}")
    exit()

# --- BOT FUNCTIONS ---

# start() function wahi rahega, usmein koi change nahi hai
def start(update: Update, context: CallbackContext):
    # ... (Pehle jaisa hi code yahan paste karein)
    welcome_text = (
        "🚀 *Welcome to StudyEra!*\n\n"
        "📚 Free Educational Resources — Notes, PYQs, Live Batches, Test Series & more!\n\n"
        "🔐 Access is secured via channel membership.\n\n"
        "👉 Please join the below channels to unlock your daily access token 👇"
    )
    keyboard = [
        [InlineKeyboardButton("📩 Join Channel 1", url=f"https://t.me/{CHANNEL_1_ID.replace('@', '')}")],
        [InlineKeyboardButton("📩 Join Channel 2", url=f"https://t.me/{CHANNEL_2_ID.replace('@', '')}")],
        [InlineKeyboardButton("✅ I Joined", callback_data='check_join')],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')


# check_join_status() function bhi wahi rahega
def check_join_status(update: Update, context: CallbackContext):
    # ... (Pehle jaisa hi code yahan paste karein)
    query = update.callback_query
    user_id = query.from_user.id
    try:
        status1 = context.bot.get_chat_member(chat_id=CHANNEL_1_ID, user_id=user_id)
        status2 = context.bot.get_chat_member(chat_id=CHANNEL_2_ID, user_id=user_id)
        
        if status1.status in ['member', 'administrator', 'creator'] and status2.status in ['member', 'administrator', 'creator']:
            generate_and_send_token(query, user_id)
        else:
            query.answer("❌ Please join both channels first!", show_alert=True)
    except telegram.error.BadRequest as e:
        # ... (error handling code)


# YEH FUNCTION BADLA HAI
def generate_and_send_token(query, user_id):
    token = secrets.token_hex(8).upper()
    
    # Hum UNIX timestamp (seconds mein) save karenge
    current_time_seconds = int(time.time())
    expiry_timestamp_seconds = current_time_seconds + (TOKEN_VALIDITY_MINUTES * 60)
    
    # Realtime Database mein data 'users' ke andar user_id ke naam se save hoga
    ref = db.reference(f'users/{user_id}')
    ref.set({
        'token': token,
        'expiry_timestamp': expiry_timestamp_seconds, # Seconds mein expiry time
        'used': False
    })
    
    # Baaki ka token bhejne wala code wahi rahega
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

# main() function wahi rahega
def main():
    # ... (Pehle jaisa hi code yahan paste karein)
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(check_join_status, pattern='^check_join$'))
    
    print("Bot is running with Realtime Database...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
