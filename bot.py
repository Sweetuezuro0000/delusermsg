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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from aiohttp import web
import asyncio


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    keyboard = [
        [
            InlineKeyboardButton(
                "👨‍💻 Contact Developer",
                url="https://t.me/ParaWebDev"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Silnx 🤖\n\n"
        "This bot is only for admins.\n"
        "To use this bot or get your own custom bot, contact:\n\n"
        "@ParaWebDev",
        reply_markup=reply_markup
    )



# =========================================================
# ENVIRONMENT VARIABLES
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]

# Render automatically provides PORT
PORT = int(os.environ.get("PORT", "10000"))

# Render service ka public URL
RENDER_EXTERNAL_URL = os.environ["RENDER_EXTERNAL_URL"]


# =========================================================
# BOT SETTINGS
# =========================================================

# Sirf isi Telegram group/chat par bot work karega
CHAT_ID = -1001988030840

# Sirf ye Telegram user bot ke commands control kar sakta hai
OWNER_USER_IDS = {
    8690092022,   # Owner 1
    5787360401,   # Owner 2
}


# Default delay
DELETE_AFTER = 3

# Bot initially OFF rahega
AUTO_DELETE = False


# =========================================================
# OWNER CHECK
# =========================================================

def is_owner(update: Update) -> bool:
    user = update.effective_user

    return (
        user is not None
        and user.id in OWNER_USER_IDS
    )


# =========================================================
# /ON
# =========================================================

async def turn_on(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global AUTO_DELETE

    if not update.effective_chat:
        return

    # Sirf owner
    if not is_owner(update):
        return

    # Sirf target group
    if update.effective_chat.id != CHAT_ID:
        return

    AUTO_DELETE = True

    await update.message.reply_text(
        f"✅ Auto-delete ON\n"
        f"⏱ Delay: {DELETE_AFTER} seconds"
    )


# =========================================================
# /OFF
# =========================================================

async def turn_off(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global AUTO_DELETE

    if not update.effective_chat:
        return

    if not is_owner(update):
        return

    if update.effective_chat.id != CHAT_ID:
        return

    AUTO_DELETE = False

    await update.message.reply_text(
        "🛑 Auto-delete OFF"
    )


# =========================================================
# /SETTIME
#
# Example:
# /settime 2
# /settime 3
# /settime 10
# =========================================================

async def set_time(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    global DELETE_AFTER

    if not update.effective_chat:
        return

    if not is_owner(update):
        return

    if update.effective_chat.id != CHAT_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Usage:\n"
            "/settime 3"
        )
        return

    try:
        seconds = int(context.args[0])

        if seconds < 1:
            raise ValueError

        DELETE_AFTER = seconds

        await update.message.reply_text(
            f"✅ Delete delay set to {seconds} seconds."
        )

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid time.\n\n"
            "Example:\n"
            "/settime 2"
        )


# =========================================================
# /STATUS
# =========================================================

async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_chat:
        return

    if not is_owner(update):
        return

    if update.effective_chat.id != CHAT_ID:
        return

    state = "ON 🟢" if AUTO_DELETE else "OFF 🔴"

    await update.message.reply_text(
        f"Auto-delete: {state}\n"
        f"Delay: {DELETE_AFTER} seconds"
    )


# =========================================================
# DELETE MESSAGE
# =========================================================

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


# =========================================================
# MESSAGE HANDLER
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_chat:
        return

    if not update.effective_user:
        return

    if not update.effective_message:
        return

    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    # -----------------------------------------
    # ONLY TARGET CHAT
    # -----------------------------------------

    if chat.id != CHAT_ID:
        return

    # -----------------------------------------
    # AUTO DELETE OFF
    # -----------------------------------------

    if not AUTO_DELETE:
        return

    # -----------------------------------------
    # OWNER MESSAGE
    # -----------------------------------------

    if user.id == OWNER_USER_ID:
        return

    # -----------------------------------------
    # CHECK ADMIN
    # -----------------------------------------

    try:
        member = await context.bot.get_chat_member(
            chat.id,
            user.id
        )

        # Admin / Group Owner messages safe
        if member.status in [
            "administrator",
            "creator"
        ]:
            return

    except TelegramError as e:
        print(f"Admin check failed: {e}")
        return

    # -----------------------------------------
    # SCHEDULE DELETE
    # -----------------------------------------

    context.job_queue.run_once(
        delete_message,
        when=DELETE_AFTER,
        data={
            "chat_id": chat.id,
            "message_id": message.message_id,
        }
    )


# =========================================================
# MAIN
# =========================================================

def main():

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )
    application.add_handler(
    CommandHandler("start", start)
    )


    # Commands
    application.add_handler(
        CommandHandler("on", turn_on)
    )

    application.add_handler(
        CommandHandler("off", turn_off)
    )

    application.add_handler(
        CommandHandler("settime", set_time)
    )

    application.add_handler(
        CommandHandler("status", status)
    )

    # Messages
    application.add_handler(
        MessageHandler(
            filters.ALL & ~filters.StatusUpdate.ALL,
            handle_message
        )
    )

    # Webhook URL
    webhook_url = f"{RENDER_EXTERNAL_URL}/telegram"

    print("Starting Telegram bot...")
    print(f"Webhook: {webhook_url}")
    print(f"Port: {PORT}")

async def home(request):
    return web.Response(
        text="Silnx is running.",
        status=200
    )


async def telegram_webhook(request):
    data = await request.json()

    update = Update.de_json(
        data,
        application.bot
    )

    await application.process_update(update)

    return web.Response(status=200)


async def run_web():
    app = web.Application()

    app.router.add_get("/", home)
    app.router.add_post("/telegram", telegram_webhook)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    print("Silnx Web Service started.")

    await asyncio.Event().wait()
    await application.initialize()
    await application.start()

    await application.bot.set_webhook(
    url=f"{RENDER_EXTERNAL_URL}/telegram",
    drop_pending_updates=True
    )

    await run_web()



if __name__ == "__main__":
    main()
