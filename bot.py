# bot.py

import os
import json
import threading
from flask import Flask, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# ─── Завантажуємо налаштування ───────────────────────────────────────────────
load_dotenv()
TOKEN      = os.getenv("TELEGRAM_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")  # наприклад: https://your-project.up.railway.app
PORT       = int(os.environ.get("PORT", 8080))

# ─── Flask для статики ────────────────────────────────────────────────────────
flask_app = Flask(__name__, static_folder="static")

@flask_app.route("/menu")
def serve_menu():
    return send_from_directory("static", "menu.html")

def run_flask():
    # Flask працює на тому ж порті, але ми підхопимо його в окремому потоці
    flask_app.run(host="0.0.0.0", port=PORT)

# ─── Ініціалізація Telegram-бота ─────────────────────────────────────────────
application = ApplicationBuilder().token(TOKEN).build()

# /start — надсилаємо кнопку WebApp
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Відкрити меню", web_app=WebAppInfo(f"{WEBAPP_URL}/menu"))]
    ]
    await update.message.reply_text(
        "Натисни кнопку нижче, щоб відкрити меню:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Обробка натискання в WebApp
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.web_app_data.data
    data = json.loads(raw)
    dish = data.get("dish", "невідома страва")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🍽️ Ви обрали: {dish}")

# Регіструємо хендлери
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

# ─── Запуск webhook + Flask ─────────────────────────────────────────────────
if __name__ == "__main__":
    # 1) Стартуємо Flask в окремому потоці, щоб віддавати /menu
    threading.Thread(target=run_flask, daemon=True).start()

    # 2) Стартуємо PTB-Webhook (цей виклик блокує основний потік)
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,                    # Telegram шле POST на /<TOKEN>
        webhook_url=f"{WEBAPP_URL}/{TOKEN}"
    )
