# bot.py

import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.ext import HTTPXRequest
from dotenv import load_dotenv

# ─── ЗАВАНТАЖЕННЯ НАЛАШТУВАНЬ ──────────────────────────────────────────────────
load_dotenv()
TOKEN       = os.getenv("TELEGRAM_TOKEN")
WEBAPP_URL  = os.getenv("WEBAPP_URL")  # Напр.: https://your-project.up.railway.app
PORT        = int(os.environ.get("PORT", 8080))

# ─── НАЛАШТУВАННЯ HTTPXRequest (щоб уникнути PoolTimeout) ────────────────────
request = HTTPXRequest(
    connect_timeout=20.0,
    read_timeout=20.0,
    pool_limits=(20, 20),
    pool_timeout=30.0,
)

# ─── ІНІЦІАЛІЗАЦІЯ БОТА ───────────────────────────────────────────────────────
application = (
    ApplicationBuilder()
    .token(TOKEN)
    .request(request)
    .build()
)

# ─── ХЕНДЛЕР /start ──────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "📋 Відкрити меню",
                web_app=WebAppInfo(f"{WEBAPP_URL}/menu"),
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Натисни кнопку нижче, щоб відкрити меню:",
        reply_markup=reply_markup,
    )

# ─── ХЕНДЛЕР WebAppData ─────────────────────────────────────────────────────
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw = update.message.web_app_data.data
        data = json.loads(raw)
        dish = data.get("dish", "невідома страва")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🍽️ Ви обрали: {dish}"
        )
    except Exception as e:
        print("❌ Помилка в handle_webapp_data:", e)

# ─── РЕЄСТРАЦІЯ ХЕНДЛЕРІВ ────────────────────────────────────────────────────
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

# ─── СТАРТ WEBHOOK-СЕРВЕРА ───────────────────────────────────────────────────
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBAPP_URL}/{TOKEN}",
    )
