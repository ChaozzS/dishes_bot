import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Токен бота и ID администратора (жестко через переменные окружения или здесь)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
ADMIN_CHAT_ID = int(os.environ.get('ADMIN_CHAT_ID', '123456789'))  # замените на ваш ID

# Структура категорий и блюд
MENU = {
    'Пицца': ['Маргарита', 'Пепперони', 'Гавайская'],
    'Суши': ['Калифорния', 'Филадельфия', 'Дракон'],
    'Напитки': ['Кола', 'Сок', 'Вода'],
}

# Словарь ингредиентов для каждого блюда
INGREDIENTS = {
    'Маргарита': ['Томатный соус', 'Сыр Моцарелла', 'Базилик'],
    'Пепперони': ['Томатный соус', 'Сыр Моцарелла', 'Пепперони'],
    'Гавайская': ['Томатный соус', 'Сыр Моцарелла', 'Ветчина', 'Ананасы'],
    'Калифорния': ['Рис', 'Нори', 'Крабовое мясо', 'Авокадо', 'Огурец'],
    'Филадельфия': ['Рис', 'Нори', 'Лосось', 'Сыр Филадельфия', 'Авокадо'],
    'Дракон': ['Рис', 'Нори', 'Угорь', 'Авокадо', 'Огурец', 'Икра масаго'],
    'Кола': ['Вода', 'Карамельный краситель', 'Кофеин', 'Газ'],
    'Сок': ['Фруктовый концентрат', 'Вода', 'Сахар'],
    'Вода': ['Вода'],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start: показываем главное меню категорий"""
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat|{cat}")] for cat in MENU]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Привет! Выберите категорию блюда:',
        reply_markup=reply_markup
    )

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем выбор категории и блюда"""
    query = update.callback_query
    await query.answer()
    data = query.data.split('|')

    # Выбор категории
    if data[0] == 'cat':
        category = data[1]
        keyboard = [[InlineKeyboardButton(
            item, callback_data=f"item|{item}")
        ] for item in MENU[category]]
        keyboard.append([InlineKeyboardButton('⬅️ Назад', callback_data='back')])
        await query.edit_message_text(
            text=f'Вы выбрали *{category}*. Теперь выберите блюдо:',
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    # Выбор блюда
    elif data[0] == 'item':
        item = data[1]
        ingredients = INGREDIENTS.get(item, [])
        ingredients_text = ', '.join(ingredients) if ingredients else 'Неизвестно'
        order_text = f"🍽 *{item}*\nИнгредиенты: {ingredients_text}"
        # Пересылаем владельцу
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=order_text,
            parse_mode='Markdown'
        )
        # Уведомление пользователю
        await query.edit_message_text(
            text='✅ Ваш заказ отправлен!',
            parse_mode='Markdown'
        )

    # Кнопка назад к выбору категории
    elif query.data == 'back':
        keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat|{cat}")] for cat in MENU]
        await query.edit_message_text(
            text='Выберите категорию блюда:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_menu_selection))

    # Запуск: polling или webhook для Railway
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
