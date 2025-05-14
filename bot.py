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
    keyboard = []
    for category in MENU.keys():
        keyboard.append([InlineKeyboardButton(category, callback_data=f"cat|{category}")])
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
    level = data[0]  # 'cat' или 'item'

    if level == 'cat':
        # Показать подкатегории для выбранной категории
        category = data[1]
        keyboard = []
        for item in MENU[category]:
            keyboard.append([
                InlineKeyboardButton(
                    item,
                    callback_data=f"item|{category}|{item}"
                )
            ])
        # Кнопка назад в главное меню
        keyboard.append([
            InlineKeyboardButton('⬅️ Назад', callback_data='back')
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f'Вы выбрали *{category}*. Теперь выберите блюдо:',
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    elif level == 'item':
        # Пользователь выбрал конкретное блюдо -> отправка админу
        category = data[1]
        item = data[2]
        user = query.from_user
        order_text = (
            f"📬 *Новый заказ*\n"
            f"Пользователь: @{user.username or user.id}\n"
            f"Категория: {category}\n"
            f"Блюдо: {item}"
        )
        # Пересылаем админу
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=order_text,
            parse_mode='Markdown'
        )
        # Уведомляем пользователя
        await query.edit_message_text(
            text=f'✅ Ваш заказ *{item}* отправлен!',
            parse_mode='Markdown'
        )

    elif query.data == 'back':
        # Возврат к главному меню
        keyboard = []
        for category in MENU.keys():
            keyboard.append([
                InlineKeyboardButton(category, callback_data=f"cat|{category}")
            ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text='Выберите категорию блюда:',
            reply_markup=reply_markup
        )

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Команда /start
    app.add_handler(CommandHandler('start', start))
    # Обработка нажатий кнопок
    app.add_handler(CallbackQueryHandler(handle_menu_selection))

    # Запуск polling (для Railway можно использовать webhook)
    if os.environ.get('RAILWAY'):
        # Настройка webhook, если развернуто на Railway
        WEBHOOK_URL = os.environ['WEBHOOK_URL']
        app.run_webhook(
            listen='0.0.0.0',
            port=int(os.environ.get('PORT', '8443')),
            webhook_url=WEBHOOK_URL + TOKEN
        )
    else:
        app.run_polling()

if __name__ == '__main__':
    main()
