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

application = Application.builder().token(TOKEN).build()
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "✅ Bot is running!"

@flask_app.route("/menu")
def serve_menu():
    return send_from_directory("static", "menu.html")

@flask_app.route(f"/{TOKEN}", methods=["POST"])
async def telegram_webhook():
    print("➡️  POST на Webhook")
    # Забираємо JSON без await, бо це не корутина
    payload = request.get_json(force=True)
    print("Payload:", payload)
    update = Update.de_json(payload, application.bot)
    print("🆕 Update decoded:", update)
    # Обробляємо оновлення асинхронно
    await application.process_update(update)
    return "ok", 200

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Відкрити меню", web_app=WebAppInfo(url=f"{WEBAPP_URL}/menu"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Натисни кнопку нижче, щоб відкрити меню:", reply_markup=reply_markup)

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        dish = data.get("dish")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🍽️ Ви обрали: {dish}")
    except Exception as e:
        print("❌ WebAppData Error:", e)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

if __name__ == "__main__":
    import asyncio

    async def main():
        await application.initialize()

        webhook_url = f"{WEBAPP_URL}/{TOKEN}"
        # скидаємо всі старі оновлення і відразу вішамо новий webhook
        await application.bot.set_webhook(webhook_url, drop_pending_updates=True)
        print(f"📡 Webhook встановлено (з обнуленням): {webhook_url}")

        flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

    asyncio.run(main())
