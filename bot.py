import os
import json
from flask import Flask, request, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBAPP_URL")  # приклад: https://web-production-xxxx.up.railway.app

app_telegram = ApplicationBuilder().token(TOKEN).build()
flask_app = Flask(__name__)

# HTML-сторінка (меню)
@flask_app.route("/menu")
def menu():
    return send_from_directory("static", "menu.html")

# Головна сторінка (для тесту)
@flask_app.route("/")
def index():
    return "✅ Webhook bot працює", 200

# Webhook endpoint — Telegram надсилає сюди
@flask_app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), app_telegram.bot)
    await app_telegram.process_update(update)
    return "ok", 200

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Відкрити меню", web_app=WebAppInfo(url=f"{WEBHOOK_URL}/menu"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Натисни кнопку нижче, щоб відкрити меню:", reply_markup=reply_markup)

# Обробка WebAppData (замовлення)
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        dish = data.get("dish")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🍽️ Ви обрали: {dish}")
    except Exception as e:
        print("❌ Помилка обробки WebAppData:", e)

# Реєструємо хендлери
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

# Стартуємо Flask + Telegram Webhook
if __name__ == "__main__":
    import asyncio

    async def set_webhook():
        webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
        await app_telegram.bot.set_webhook(webhook_url)
        print(f"📡 Webhook встановлено: {webhook_url}")

    asyncio.run(set_webhook())
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
