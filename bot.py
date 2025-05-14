import os
import json
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.ext import Dispatcher, CallbackContext
from telegram.ext.webhookhandler import WebhookHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBAPP_URL")  # має бути https://web-production-....railway.app/

# Ініціалізація бота
app = ApplicationBuilder().token(TOKEN).build()
dispatcher = app

# Flask веб-сервер
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return '🤖 Bot is running with webhook!', 200

@flask_app.route('/menu')
def serve_menu():
    return flask_app.send_static_file('menu.html')

@flask_app.route(f'/{TOKEN}', methods=['POST'])
async def receive_update():
    update = Update.de_json(request.get_json(force=True), app.bot)
    await dispatcher.process_update(update)
    return 'ok'

# Обробник /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = os.getenv("WEBAPP_URL") + "/menu"
    keyboard = [
        [InlineKeyboardButton("📋 Відкрити меню", web_app=WebAppInfo(url=url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Натисни кнопку нижче, щоб відкрити меню:", reply_markup=reply_markup)

# Обробник WebApp Data
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        dish = data.get("dish")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"🍽️ Ви обрали: {dish}")
    except Exception as e:
        print("❌ Помилка:", e)

# Реєстрація обробників
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

# Установка webhook при запуску
async def setup_webhook():
    await app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print(f"📡 Webhook встановлено: {WEBHOOK_URL}/{TOKEN}")

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_webhook())
    flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
