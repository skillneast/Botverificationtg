import os
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatInviteLink
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ChatJoinRequestHandler
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

# IMPORTANT: Ab humein Channel ID (number wali) chahiye, username nahi.
# Kaise milegi: Channel mein koi message forward karein "My ID Bot" ko.
CHANNEL_1_ID = int(os.environ.get('CHANNEL_1_ID')) # Example: -100123456789
CHANNEL_2_ID = int(os.environ.get('CHANNEL_2_ID')) # Example: -100987654321

OWNER_USERNAME = "neasthub"
WEBSITE_URL = os.environ.get('WEBSITE_URL', 'https://render.com')
FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL')
FIREBASE_KEY_BASE64 = os.environ.get('FIREBASE_KEY_BASE64')
TOKEN_VALIDITY_MINUTES = 15

# --- FIREBASE SETUP ---
try:
    if FIREBASE_KEY_BASE64:
        # ... (Firebase setup code waisa hi rahega)
        pass # For brevity
except Exception as e:
    logger.critical(f"Firebase initialization failed: {e}")

# --- BOT FUNCTIONS ---

def start(update: Update, context: CallbackContext):
    # ... (Start message waisa hi rahega) ...
    # Yahan hum channel links nahi denge, kyunki woh agle step mein aayenge
    keyboard = [
        [InlineKeyboardButton("✅ Verify Membership", callback_data='verify_membership')],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🚀 *Welcome!* Click below to start the verification process.", reply_markup=reply_markup, parse_mode='Markdown')

def verify_membership_step1(update: Update, context: CallbackContext):
    """Generates unique invite links for the user."""
    query = update.callback_query
    user_id = query.from_user.id
    try:
        # Link ek ghante ke liye valid hoga
        expire_date = int(time.time()) + 3600 
        
        # Pehle channel ke liye link
        link1 = context.bot.create_chat_invite_link(
            chat_id=CHANNEL_1_ID, 
            expire_date=expire_date,
            member_limit=1,
            name=f"Verification for {user_id}"
        )
        # Doosre channel ke liye link
        link2 = context.bot.create_chat_invite_link(
            chat_id=CHANNEL_2_ID, 
            expire_date=expire_date,
            member_limit=1,
            name=f"Verification for {user_id}"
        )

        text = "Great! To verify you're human and to get access, please join using the buttons below. \n\n*Even if you are already a member, you must click these buttons to be verified.*"
        keyboard = [
            [InlineKeyboardButton("1️⃣ Join Skillneast", url=link1.invite_link)],
            [InlineKeyboardButton("2️⃣ Join Skillneast Backup", url=link2.invite_link)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Could not create invite links: {e}")
        query.answer("Error: Could not create verification links. Make sure the bot is an admin with 'Invite Users via Link' permission.", show_alert=True)


def chat_join_request_handler(update: Update, context: CallbackContext):
    """Handles the event when a user clicks an invite link."""
    user_id = update.chat_join_request.from_user.id
    chat_id = update.chat_join_request.chat.id
    
    # User ko channel mein approve karo
    context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
    
    # Firebase mein user ka progress save karo
    user_ref = db.reference(f'verification_progress/{user_id}')
    user_ref.child(str(chat_id)).set(True)
    
    # Check karo ki kya user ne dono channels join kar liye
    progress = user_ref.get()
    if progress and str(CHANNEL_1_ID) in progress and str(CHANNEL_2_ID) in progress:
        logger.info(f"User {user_id} has joined both channels. Granting token.")
        # Dono join ho gaye, ab token do
        generate_and_send_token_by_id(user_id, context.bot)
        # Progress delete kar do
        user_ref.delete()

def generate_and_send_token_by_id(user_id, bot):
    """Generates and sends the token directly to a user ID."""
    token = secrets.token_hex(8).upper()
    # ... (Firebase mein token save karne ka code waisa hi rahega) ...
    
    access_text = "✅ *Verification Complete!*\n\n🎉 *Access Granted!*\n\n" + f"Here is your one-time token:\n\n`{token}`"
    keyboard = [[InlineKeyboardButton("🔐 Access Website", url=WEBSITE_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=user_id, text=access_text, reply_markup=reply_markup, parse_mode='Markdown')

# --- WEB SERVER (WEBHOOK) SETUP ---
app = Flask(__name__)
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

# Naye Handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CallbackQueryHandler(verify_membership_step1, pattern='^verify_membership$'))
dispatcher.add_handler(ChatJoinRequestHandler(chat_join_request_handler))

# ... (baaki ka webhook code waisa hi rahega) ...
