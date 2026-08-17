import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError


# ==================================================
# CONFIG
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")

# Jis group mein bot kaam karega
CHAT_ID = -1001234567890

# Jis user ko control karna hai
OWNER_USER_ID = 123456789

# Default delete delay
DELETE_AFTER = 3

# Auto-delete initially ON/OFF
AUTO_DELETE = False


# ==================================================
# OWNER CHECK
# ==================================================

def is_owner(update: Update) -> bool:
    user = update.effective_user

    return (
        user is not None
        and user.id == OWNER_USER_ID
    )


# ==================================================
# /ON
# ==================================================

async def turn_on(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global AUTO_DELETE

    # Sirf specified user
    if not is_owner(update):
        return

    # Sirf specified chat
    if update.effective_chat.id != CHAT_ID:
        return

    AUTO_DELETE = True

    await update.message.reply_text(
        "✅ Auto-delete ON\n"
        f"⏱ Delay: {DELETE_AFTER} seconds"
    )


# ==================================================
# /OFF
# ==================================================

async def turn_off(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global AUTO_DELETE

    if not is_owner(update):
        return

    if update.effective_chat.id != CHAT_ID:
        return

    AUTO_DELETE = False

    await update.message.reply_text(
        "🛑 Auto-delete OFF"
    )


# ==================================================
# /SETTIME
# Example: /settime 2
# ==================================================

async def set_time(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global DELETE_AFTER

    if not is_owner(update):
        return

    if update.effective_chat.id != CHAT_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /settime 3"
        )
        return

    try:
        seconds = int(context.args[0])

        if seconds < 1:
            raise ValueError

        DELETE_AFTER = seconds

        await update.message.reply_text(
            f"⏱ Delete delay set to {seconds} seconds."
        )

    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid number.\n"
            "Example: /settime 3"
        )


# ==================================================
# DELETE MESSAGE
# ==================================================

async def delete_message(
    context: ContextTypes.DEFAULT_TYPE
):

    job = context.job

    try:
        await context.bot.delete_message(
            chat_id=job.data["chat_id"],
            message_id=job.data["message_id"]
        )

    except TelegramError as e:
        print(f"Delete failed: {e}")


# ==================================================
# MESSAGE HANDLER
# ==================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    global AUTO_DELETE

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message or not chat or not user:
        return

    # Sirf specified chat
    if chat.id != CHAT_ID:
        return

    # Agar OFF hai to kuch mat karo
    if not AUTO_DELETE:
        return

    # OWNER ke messages ko delete nahi karna
    if user.id == OWNER_USER_ID:
        return

    # Admin status check
    member = await context.bot.get_chat_member(
        chat.id,
        user.id
    )

    # Admin / Owner ke messages safe
    if member.status in ["administrator", "creator"]:
        return

    # Delete schedule
    context.job_queue.run_once(
        delete_message,
        when=DELETE_AFTER,
        data={
            "chat_id": chat.id,
            "message_id": message.message_id,
        }
    )


# ==================================================
# MAIN
# ==================================================

def main():

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler("on", turn_on)
    )

    app.add_handler(
        CommandHandler("off", turn_off)
    )

    app.add_handler(
        CommandHandler("settime", set_time)
    )

    # Messages
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.StatusUpdate.ALL,
            handle_message
        )
    )

    print("Bot started...")

    app.run_polling()


if __name__ == "__main__":
    main()
