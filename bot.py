# Yeh dono functions upar wale code mein ... ki jagah aayenge

def check_join_status(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    try:
        status1 = context.bot.get_chat_member(chat_id=CHANNEL_1_ID, user_id=user_id)
        status2 = context.bot.get_chat_member(chat_id=CHANNEL_2_ID, user_id=user_id)
        
        if status1.status in ['member', 'administrator', 'creator'] and \
           status2.status in ['member', 'administrator', 'creator']:
            generate_and_send_token(query, user_id)
        else:
            query.answer("❌ Please join both channels first!", show_alert=True)
    except telegram.error.BadRequest as e:
        if "user not found" in str(e).lower():
            query.answer("❌ You must join both channels to get the token.", show_alert=True)
        else:
            print(f"Error checking membership for user {user_id}: {e}")
            query.answer("Error! Make sure bot is an admin in both channels.", show_alert=True)
    except Exception as e:
        print(f"An unexpected error occurred for user {user_id}: {e}")
        query.answer("An unexpected error occurred. Please try again later.", show_alert=True)

def generate_and_send_token(query, user_id):
    token = secrets.token_hex(8).upper()
    current_time_seconds = int(time.time())
    expiry_timestamp_seconds = current_time_seconds + (TOKEN_VALIDITY_MINUTES * 60)
    
    ref = db.reference(f'users/{user_id}')
    ref.set({
        'token': token,
        'expiry_timestamp': expiry_timestamp_seconds,
        'used': False
    })
    
    access_text = (
        "🎉 *Access Granted!*\n\n"
        f"Here is your one-time token, valid for *{TOKEN_VALIDITY_MINUTES} minutes*:\n\n"
        f"`{token}`\n\n"
        "✅ Paste this on the website to continue!\n"
        "⚠️ *Note: If you leave any channel, your access will be revoked.*"
    )
    keyboard = [
        [InlineKeyboardButton("🔐 Access Website", url=WEBSITE_URL)],
        [InlineKeyboardButton("👑 Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=access_text, reply_markup=reply_markup, parse_mode='Markdown')
    query.answer("✅ Token Generated!")
