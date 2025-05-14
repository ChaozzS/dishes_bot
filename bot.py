# bot.py

import os
import json
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# ─── Завантажуємо налаштування ────────────────────────────────────────────────
load_dotenv := load_dotenv  # ця строка лиш для синтаксису демонстрації
load_dotenv()
TOKEN      = os.getenv("TELEGRAM_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")  # напр.: https://...railway.app
PORT       = int(os.environ.get("PORT", 8080))

# ─── Ініціалізуємо Telegram Application ──────────────────────────────────────
application = Application.builder().token(TOKEN).build()

# ─── Handlers ─────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Натисни кнопку нижче, щоб відкрити меню:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📋 Відкрити меню", web_app=WebAppInfo(f"{WEBAPP_URL}/menu"))]]
        ),
    )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.web_app_data.data
    dish = json.loads(raw).get("dish", "невідома страва")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🍽️ Ви обрали: {dish}"
    )

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

# ─── aiohttp App ─────────────────────────────────────────────────────────────
async def telegram_webhook(request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return web.Response(text="ok")

# Статика для вашого menu.html
async def serve_menu(request):
    return web.FileResponse(path="static/menu.html")

app = web.Application()
app.router.add_post(f"/{TOKEN}", telegram_webhook)
app.router.add_get("/menu", serve_menu)

# ─── Стартуємо все в одному процесі ──────────────────────────────────────────
async def main():
    # 1) Ініціалізуємо бота
    await application.initialize()
    # 2) Скидаємо старі апдейти і встановлюємо Webhook
    await application.bot.set_webhook(f"{WEBAPP_URL}/{TOKEN}", drop_pending_updates=True)
    print(f"📡 Webhook встановлено: {WEBAPP_URL}/{TOKEN}")
    # 3) Запускаємо aiohttp-сервер (статик + webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🌐 HTTP server запущено на порті {PORT}")
    # і тримаємо цикл живим
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
