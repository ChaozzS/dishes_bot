import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Загружаем токен и chat_id администратора из переменных окружения
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_CHAT_ID = int(os.environ.get('ADMIN_CHAT_ID', 0))

# Структура меню: категории и подкатегории
MENU = {
    'Пицца': ['Маргарита', 'Пепперони', 'Гавайская'],
    'Суши': ['Калифорния', 'Филадельфия', 'Дракон'],
    'Напитки': ['Кола', 'Сок', 'Вода'],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start: приветствие и главное меню"""
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat|{cat}")] for cat in MENU]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Привет! Выберите категорию блюда:',
        reply_markup=reply_markup
    )

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем выбор категории или подкатегории"""
    query = update.callback_query
    await query.answer()

    data = query.data.split('|')
    if data[0] == 'cat':
        category = data[1]
        keyboard = [[InlineKeyboardButton(item, callback_data=f"item|{category}|{item}")] for item in MENU[category]]
        keyboard.append([InlineKeyboardButton('⬅️ Назад', callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f'Вы выбрали *{category}*. Теперь выберите блюдо:',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif data[0] == 'item':
        category, item = data[1], data[2]
        user = query.from_user
        order_text = (
            f"📬 *Новый заказ*\n"
            f"Пользователь: @{user.username or user.id}\n"
            f"Категория: {category}\n"
            f"Блюдо: {item}"
        )
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=order_text,
            parse_mode='Markdown'
        )
        await query.edit_message_text(
            text=f'✅ Ваш заказ *{item}* отправлен!',
            parse_mode='Markdown'
        )

    elif query.data == 'back':
        keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat|{cat}")] for cat in MENU]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text='Выберите категорию блюда:',
            reply_markup=reply_markup
        )

# Основная функция теперь обычная, а не асинхронная
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_menu_selection))

    # Запуск polling или webhook в зависимости от окружения
    if os.environ.get('RAILWAY'):
        WEBHOOK_URL = os.environ['WEBHOOK_URL']
        PORT = int(os.environ.get('PORT', '8443'))
        app.run_webhook(
            listen='0.0.0.0',
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}{TOKEN}"
        )
    else:
        app.run_polling()

if __name__ == '__main__':
    main()
