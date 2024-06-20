import logging
import sqlite3
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes, Application, CallbackQueryHandler
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DATABASE = 'chat.db'

# Define states for the conversation
ASKING_ID, ASKING_MESSAGE, ASKING_HISTORY_ID, ASKING_REPLY_MESSAGE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf'Hi {user.mention_html()}! Use /register to get your anonymous ID.',
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Register the user and assign an anonymous ID."""
    user = update.effective_user

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Check if the user is already registered
    c.execute("SELECT user_id FROM users WHERE telegram_id = ?", (user.id,))
    result = c.fetchone()

    if result:
        user_id = result[0]
        await update.message.reply_text(f'You are already registered. Your ID is {user_id}.')
    else:
        c.execute("INSERT INTO users (telegram_id, username) VALUES (?, ?)", (user.id, user.username))
        conn.commit()
        user_id = c.lastrowid
        await update.message.reply_text(f'You have been registered. Your anonymous ID is {user_id}.')
    
    conn.close()

async def ask_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for the ID of the recipient."""
    await update.message.reply_text('Please enter the ID of the person you want to message:')
    return ASKING_ID

async def ask_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the ID and ask for the message."""
    context.user_data['recipient_id'] = int(update.message.text)
    await update.message.reply_text('Please enter the message you want to send:')
    return ASKING_MESSAGE

async def send_anonymous_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send the anonymous message to the specified ID and save to DB."""
    sender_telegram_id = update.effective_user.id
    recipient_id = context.user_data['recipient_id']
    message = update.message.text

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Get sender user_id from telegram_id
    c.execute("SELECT user_id FROM users WHERE telegram_id = ?", (sender_telegram_id,))
    sender_id = c.fetchone()[0]
    
    # Ensure sender and recipient IDs are ordered for uniqueness
    participant1_id, participant2_id = sorted([sender_id, recipient_id])

    # Get or create chatroom
    c.execute("""
        SELECT chatroom_id FROM chatrooms 
        WHERE (participant1_id = ? AND participant2_id = ?) 
        OR (participant1_id = ? AND participant2_id = ?)""", 
        (participant1_id, participant2_id, participant2_id, participant1_id))
    result = c.fetchone()
    
    if result:
        chatroom_id = result[0]
    else:
        c.execute("INSERT INTO chatrooms (participant1_id, participant2_id) VALUES (?, ?)", 
                  (participant1_id, participant2_id))
        conn.commit()
        chatroom_id = c.lastrowid
    
    # Save message to DB
    c.execute("INSERT INTO messages (chatroom_id, sender_id, message) VALUES (?, ?, ?)", 
              (chatroom_id, sender_id, message))
    conn.commit()
    message_id = c.lastrowid

    # Fetch the telegram ID of the recipient
    c.execute("SELECT telegram_id FROM users WHERE user_id = ?", (recipient_id,))
    result = c.fetchone()
    conn.close()

    if result:
        target_telegram_id = result[0]
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Reply", callback_data=f'reply_{message_id}_{chatroom_id}')]
        ])
        await context.bot.send_message(chat_id=target_telegram_id, text=f'Anonymous message: {message}', reply_markup=reply_markup)
        await update.message.reply_text('Your message has been sent anonymously!')
    else:
        await update.message.reply_text('Invalid ID. Please check the ID and try again.')

    return ConversationHandler.END

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle reply button click."""
    query = update.callback_query
    query_data = query.data.split('_')
    message_id = query_data[1]
    chatroom_id = query_data[2]

    context.user_data['reply_message_id'] = message_id
    context.user_data['reply_chatroom_id'] = chatroom_id
    await query.message.reply_text('Please enter your reply message:')
    return ASKING_REPLY_MESSAGE

async def send_reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send the reply message to the original sender."""
    reply_message = update.message.text
    recipient_telegram_id = update.effective_user.id
    message_id = context.user_data['reply_message_id']
    chatroom_id = context.user_data['reply_chatroom_id']

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Get recipient user_id from telegram_id
    c.execute("SELECT user_id FROM users WHERE telegram_id = ?", (recipient_telegram_id,))
    recipient_id = c.fetchone()[0]

    # Get the original sender user_id from the message_id
    c.execute("SELECT sender_id FROM messages WHERE message_id = ?", (message_id,))
    sender_id = c.fetchone()[0]

    # Save reply message to DB
    c.execute("INSERT INTO messages (chatroom_id, sender_id, message) VALUES (?, ?, ?)", 
              (chatroom_id, recipient_id, reply_message))
    conn.commit()
    new_message_id = c.lastrowid

    # Fetch the telegram ID of the original sender
    c.execute("SELECT telegram_id FROM users WHERE user_id = ?", (sender_id,))
    result = c.fetchone()
    conn.close()

    if result:
        target_telegram_id = result[0]
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Reply", callback_data=f'reply_{new_message_id}_{chatroom_id}')]
        ])
        await context.bot.send_message(chat_id=target_telegram_id, text=f'Reply to your anonymous message: {reply_message}', reply_markup=reply_markup)
        await update.message.reply_text('Your reply has been sent anonymously!')
    else:
        await update.message.reply_text('Failed to send reply. Please try again.')

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END

async def ask_history_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for the ID of the person to fetch history with."""
    await update.message.reply_text('Please enter the ID of the person you want to see the history with:')
    return ASKING_HISTORY_ID

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Fetch and send the message history with a specified user."""
    sender_telegram_id = update.effective_user.id
    recipient_id = int(update.message.text)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Get sender user_id from telegram_id
    c.execute("SELECT user_id FROM users WHERE telegram_id = ?", (sender_telegram_id,))
    sender_id = c.fetchone()[0]

    # Ensure sender and recipient IDs are ordered for uniqueness
    participant1_id, participant2_id = sorted([sender_id, recipient_id])

    # Get the chatroom ID
    c.execute("""
        SELECT chatroom_id FROM chatrooms 
        WHERE (participant1_id = ? AND participant2_id = ?) 
        OR (participant1_id = ? AND participant2_id = ?)""", 
        (participant1_id, participant2_id, participant2_id, participant1_id))
    result = c.fetchone()
    
    if result:
        chatroom_id = result[0]
        # Fetch messages from the chatroom
        c.execute("SELECT sender_id, message, timestamp FROM messages WHERE chatroom_id = ? ORDER BY timestamp ASC", 
                  (chatroom_id,))
        messages = c.fetchall()
        history_text = "Message history:\n"
        for msg in messages:
            sender = "You" if msg[0] == sender_id else "Them"
            history_text += f"{sender} [{msg[2]}]: {msg[1]}\n"
        await update.message.reply_text(history_text)
    else:
        await update.message.reply_text('No chat history found with the specified user ID.')
    
    conn.close()
    return ConversationHandler.END

async def set_commands(application: Application) -> int:
    """Set the bot's commands menu."""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("register", "Register and get your anonymous ID"),
        BotCommand("send", "Send an anonymous message"),
         BotCommand("history", "Get the message history with a user"),
        BotCommand("cancel", "Cancel the current operation")
    ]
    await application.bot.set_my_commands(commands)
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    # Replace 'YOUR_TOKEN' with the token you got from the BotFather
    application = Application.builder().token("YOUR_TOKEN").build()

    # Set the bot's commands menu
    application.add_handler(CommandHandler("setcommands", lambda update, context: set_commands(application)))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('send', ask_id)],
        states={
            ASKING_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_message)],
            ASKING_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_anonymous_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    history_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('history', ask_history_id)],
        states={
            ASKING_HISTORY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_history)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    reply_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(reply, pattern='^reply_')],
        states={
            ASKING_REPLY_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_reply_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(history_conv_handler)
    application.add_handler(reply_conv_handler)

 # Set the bot's commands when the application starts
    set_commands(application)

    # Start the Bot
    application.run_polling()

   

if __name__ == '__main__':
    main()
