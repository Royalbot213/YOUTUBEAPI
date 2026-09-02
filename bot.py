import os
import logging
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from api import make_api_key

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in Heroku Config Vars")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔑 My API Key", callback_data="key"),
            InlineKeyboardButton("📖 API Docs", callback_data="docs"),
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    key, expiry = make_api_key(user.id)

    text = (
        "👋 <b>Welcome to Fresh YouTube API</b>\n\n"
        "Your API key is ready.\n\n"
        f"🔑 <code>{key}</code>\n"
        f"📅 Valid until: <b>{expiry.strftime('%Y-%m-%d %H:%M UTC')}</b>\n\n"
        "Use the buttons below."
    )
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    key, expiry = make_api_key(user.id)

    if query.data == "key":
        text = (
            "🔑 <b>Your API Key</b>\n\n"
            f"<code>{key}</code>\n\n"
            f"📅 Expires: <b>{expiry.strftime('%Y-%m-%d %H:%M UTC')}</b>\n\n"
            "This key is verified by the API server."
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    elif query.data == "docs":
        base_url = os.environ.get("API_BASE_URL", "https://youtubeapi-india.herokuapp.com")
        text = (
            "📖 <b>API Documentation</b>\n\n"
            f"Base URL:\n<code>{base_url}</code>\n\n"
            "Health:\n"
            f"<code>{base_url}/health</code>\n\n"
            "Swagger:\n"
            f"<code>{base_url}/docs</code>\n\n"
            "Download:\n"
            f"<code>{base_url}/download</code>\n\n"
            "Parameters:\n"
            "• url = YouTube URL\n"
            "• type = audio or video\n"
            "• api_key = your API key\n\n"
            "Example:\n"
            f"<code>{base_url}/download?url=YOUTUBE_URL&type=audio&api_key={key}</code>"
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    elif query.data == "help":
        text = (
            "ℹ️ <b>Help</b>\n\n"
            "1. Copy your API key.\n"
            "2. Send a YouTube URL to your application/client.\n"
            "3. Use type=audio for MP3 or type=video for MP4.\n\n"
            "The API key is tied to your Telegram user ID."
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Telegram update error: %s", context.error)


def run():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(buttons))
    application.add_error_handler(error_handler)

    logger.info("Telegram bot starting...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run()
