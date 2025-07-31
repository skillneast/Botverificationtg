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

# --- CONFIGURATION (Yeh Render par Environment Variables se aayega) ---
# Inki values Render ke dashboard mein set honi chahiye.
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHANNEL_1_ID = os.environ.get('CHANNEL_1_ID')
CHANNEL_2_ID = os.environ.get('CHANNEL_2_ID')
WEBSITE_URL = os.environ.get('WEBSITE_URL')
OWNER_USERNAME = os.environ.get('OWNER_USERNAME')
FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
TOKEN_VALIDITY_MINUTES = 15

# --- FIREBASE SETUP ---
# Yeh section safely aapki Base64 encoded key ko decode karke Firebase se connect karega.
try:
    encoded_key = os.environ.get('FIREBASE_KEY_BASE64')
    if not encoded_key:
        raise ValueError("FIREBASE_KEY_BASE64 environment variable not set.")
        
    decoded_key = base64.b64decode(encoded_key)
    firebase_key_dict = json.loads(decoded_key)
    
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DATABASE_URL
    })
except Exception as e:
    print(f"CRITICAL: Firebase initialization failed: {e}")
    # Agar Firebase connect nahi hua, to bot ko band kar do kyunki woh kaam nahi kar payega.
    exit()

# --- BOT FUNCTIONS ---

# /start command handler
def start(update: Update, context: CallbackContext):
    """Sends the welcome message and channel join buttons."""
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

# "I Joined" button click handler
def check_join_status(update: Update, context: CallbackContext):
    """Checks if the user has joined both channels."""
    query = update.callback_query
    user_id = query.from_user.id
    try:
        status1 = context.bot.get_chat_member(chat_id=CHANNEL_1_ID, user_id=user_id)
        status2 = context.bot.get_chat_member(chat_id=CHANNEL_2_ID, user_id=user_id)
        
        # User in states 'member', 'administrator', or 'creator' is considered a member
        if status1.status in ['member', 'administrator', 'creator'] and \
           status2.status in ['member', 'administrator', 'creator']:
            generate_and_send_token(query, user_id)
        else:
            # User ne join nahi kiya hai
            query.answer("❌ Please join both channels first!", show_alert=True)

    except telegram.error.BadRequest as e:
        # Is error ko handle karna zaroori hai
        if "user not found" in str(e).lower():
            # Yeh tab hota hai jab user ne channel join hi nahi kiya ho
            query.answer("❌ You must join both channels to get the token.", show_alert=True)
        else:
            # Yeh koi aur technical error hai (jaise bot admin nahi hai)
            print(f"Error checking membership for user {user_id}: {e}")
            query.answer("Error! Make sure bot is an admin in both channels.", show_alert=True)
    
    except Exception as e:
        # Baaki sabhi anjaan errors ke liye
        print(f"An unexpected error occurred for user {user_id}: {e}")
        query.answer("An unexpected error occurred. Please try again later.", show_alert=True)

# Token generation and sending function
def generate_and_send_token(query, user_id):
    """Generates a token and saves it to Realtime Database."""
    token = secrets.token_hex(8).upper()
    
    # Hum UNIX timestamp (seconds mein) save karenge
    current_time_seconds = int(time.time())
    expiry_timestamp_seconds = current_time_seconds + (TOKEN_VALIDITY_MINUTES * 60)
    
    # Realtime Database mein data 'users' ke andar user_id ke naam se save hoga
    ref = db.reference(f'users/{user_id}')
    ref.set({
        'token': token,
        'expiry_timestamp': expiry_timestamp_seconds,
        'used': False
    })
    
    access_text = (
        "🎉 *Access Granted!*\n\n"
        f"Here is your one-time token, valid for *{TOKEN_VALIDITY_MINUTES} minutes*:\n\n"
        f"`{token}`\n\n"  # This makes the token easy to copy on mobile
        "✅ Paste this on the website to continue!\n"
        "⚠️ *Note: If you leave any channel, your access will be revoked.*"
    )
    keyboard = [
        [InlineKeyboardButton("🔐 Access Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Message ko edit karke token dikhao
    query.edit_message_text(text=access_text, reply_markup=reply_markup, parse_mode='Markdown')
    query.answer("✅ Token Generated!")

# Main function to start the bot
def main():
    """Starts the bot."""
    # Check if all necessary environment variables are set
    if not all([TELEGRAM_BOT_TOKEN, CHANNEL_1_ID, CHANNEL_2_ID, WEBSITE_URL, OWNER_USERNAME, FIREBASE_DATABASE_URL]):
        print("CRITICAL: One or more environment variables are missing. Please check your Render configuration.")
        return

    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(check_join_status, pattern='^check_join$'))
    
    print("Bot is running with Realtime Database...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
