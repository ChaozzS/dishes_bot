import os
import json
from flask import Flask, request, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import asyncio

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

app = Application.builder().token(TOKEN).build()
flask_app = Flask(__name__)

# HTML меню
@flask_app.route("/menu")
def menu():
    return send_from_directory("static", "menu.html")

# коренева сторінка
@flask_app.route("/")
def index():
    return "✅ Telegram Webhook бот працює!", 200

# Webhook точка прийому
@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    app.create_task(app.process_update(update))  # асинхронна обробка
    return "ok", 200

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Відкрити меню", web_app=WebAppInfo(url=f"{WEBAPP_URL}/menu"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Натисни кнопку нижче, щоб відкрити меню:", reply_markup=reply_markup)

# вибір страви
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        dish = data.get("dish")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🍽️ Ви обрали: {dish}")
    except Exception as e:
        print("❌ Помилка при обробці WebAppData:", e)

# реєстрація обробників
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

# запуск
if __name__ == "__main__":
    async def main():
        await app.bot.set_webhook(url=f"{WEBAPP_URL}/{TOKEN}")
        print(f"📡 Webhook встановлено: {WEBAPP_URL}/{TOKEN}")
        flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

    asyncio.run(main())
