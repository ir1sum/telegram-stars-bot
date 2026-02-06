#!/usr/bin/env python3
"""
Telegram Stars Bot для Railway.app
Простой бот с вводом любого количества звезд
"""

import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = os.getenv('BOT_TOKEN')
BANK_CARD = os.getenv('BANK_CARD', '2200 0000 0000 0000')
BANK_CARD_HOLDER = os.getenv('BANK_CARD_HOLDER', 'ИВАН ИВАНОВ')
STAR_PRICE = float(os.getenv('STAR_PRICE', '1.6'))
MIN_STARS = int(os.getenv('MIN_STARS', '50'))
MAX_STARS = 5000

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== СОСТОЯНИЯ =====
WAITING_STARS = 1

# ===== УТИЛИТЫ =====
def generate_order_id(user_id):
    return f"ST{datetime.now().strftime('%m%d%H%M')}{user_id % 1000:03d}"

def calculate_price(stars):
    return round(stars * STAR_PRICE, 2)

# ===== КОМАНДЫ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    keyboard = [
        [InlineKeyboardButton("⭐ Купить звёзды", callback_data='buy')],
        [InlineKeyboardButton("💰 Калькулятор", callback_data='calculator')],
        [InlineKeyboardButton("💳 Реквизиты", callback_data='details')],
        [InlineKeyboardButton("📞 Поддержка", callback_data='support')]
    ]
    
    text = (
        f"🚀 *Telegram Stars Bot*\n\n"
        f"💎 *Цена:* {STAR_PRICE}₽ за 1 звезду\n"
        f"📦 *Диапазон:* от {MIN_STARS} до {MAX_STARS} звезд\n\n"
        f"💳 *Оплата картой РФ*\n"
        f"⚡ *Доставка:* мгновенно\n\n"
        f"Нажмите *'Купить звёзды'* для заказа"
    )
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def buy_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать покупку"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"🎛 *Введите количество звезд*\n\n"
        f"💎 Цена: *{STAR_PRICE}₽* за 1 звезду\n"
        f"📦 От *{MIN_STARS}* до *{MAX_STARS}* звезд\n\n"
        f"*Пример:* 100 звезд = *{calculate_price(100)}₽*\n\n"
        f"Введите любое число:"
    )
    return WAITING_STARS

async def receive_stars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить количество от пользователя"""
    try:
        stars = int(update.message.text)
        
        if stars < MIN_STARS:
            await update.message.reply_text(
                f"❌ *Минимум {MIN_STARS} звезд*\n\n"
                f"Введите число от {MIN_STARS}:",
                parse_mode='Markdown'
            )
            return WAITING_STARS
        
        if stars > MAX_STARS:
            await update.message.reply_text(
                f"❌ *Максимум {MAX_STARS} звезд*\n\n"
                f"Введите число до {MAX_STARS}:",
                parse_mode='Markdown'
            )
            return WAITING_STARS
        
        price = calculate_price(stars)
        order_id = generate_order_id(update.effective_user.id)
        
        text = (
            f"✅ *Заказ #{order_id}*\n\n"
            f"⭐ Звёзд: *{stars}*\n"
            f"💰 Стоимость: *{price}₽*\n\n"
            f"💳 *Переведите на карту:*\n"
            f"`{BANK_CARD}`\n"
            f"👤 *Получатель:* {BANK_CARD_HOLDER}\n\n"
            f"📝 *ИНСТРУКЦИЯ:*\n"
            f"1. Переведите *{price}₽*\n"
            f"2. В комментарии укажите: *{order_id}*\n"
            f"3. Сохраните скриншот\n"
            f"4. Нажмите *'Я оплатил'* ниже\n\n"
            f"⚠️ *Без комментария платеж не зачислится!*"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Я оплатил", callback_data=f'paid_{order_id}')],
            [InlineKeyboardButton("📞 Поддержка", callback_data='support')],
            [InlineKeyboardButton("🔄 Новый заказ", callback_data='buy')]
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ *Введите ЧИСЛО!*\n\n"
            f"Например: 100, 250, 500\n"
            f"Диапазон: от {MIN_STARS} до {MAX_STARS}",
            parse_mode='Markdown'
        )
        return WAITING_STARS

async def mark_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отметить как оплачено"""
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.replace('paid_', '')
    
    await query.edit_message_text(
        f"✅ *Заказ #{order_id} принят!*\n\n"
        f"⏱ *Статус:* Ожидает проверки\n"
        f"🕐 *Время:* 1-10 минут\n\n"
        f"📞 *Поддержка:* @ваш_никнейм\n"
        f"🔄 *Новый заказ:* /start"
    )

async def calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Калькулятор стоимости"""
    query = update.callback_query
    await query.answer()
    
    examples = ""
    for stars in [50, 100, 250, 500, 1000, 2000, 5000]:
        if MIN_STARS <= stars <= MAX_STARS:
            price = calculate_price(stars)
            examples += f"• *{stars}* звезд = *{price}₽*\n"
    
    text = (
        f"🧮 *Калькулятор стоимости*\n\n"
        f"💎 Цена за 1 звезду: *{STAR_PRICE}₽*\n"
        f"📦 Диапазон: от *{MIN_STARS}* до *{MAX_STARS}*\n\n"
        f"*Примеры:*\n{examples}\n"
        f"📝 *Формула:* Количество × {STAR_PRICE} = Стоимость"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛒 Купить сейчас", callback_data='buy')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Реквизиты"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"💳 *Реквизиты для оплаты*\n\n"
        f"🏦 *Карта:*\n`{BANK_CARD}`\n"
        f"👤 *Получатель:* {BANK_CARD_HOLDER}\n\n"
        f"📝 *Как оплатить:*\n"
        f"1. Сделайте заказ через бота\n"
        f"2. Получите код заказа\n"
        f"3. Переведите сумму на карту\n"
        f"4. Укажите код в комментарии\n"
        f"5. Нажмите 'Я оплатил'\n\n"
        f"⚠️ *Без кода платеж не будет зачислен!*"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛒 Сделать заказ", callback_data='buy')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поддержка"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "📞 *Поддержка*\n\n"
        "👤 *Менеджер:* @ваш_никнейм\n"
        "⏱ *Время ответа:* 5-15 минут\n\n"
        "*При обращении укажите:*\n"
        "1. Код заказа\n"
        "2. Сумма платежа\n"
        "3. Дата и время\n"
        "4. Скриншот перевода\n\n"
        "*Работаем 24/7*"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назад в меню"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⭐ Купить звёзды", callback_data='buy')],
        [InlineKeyboardButton("💰 Калькулятор", callback_data='calculator')],
        [InlineKeyboardButton("💳 Реквизиты", callback_data='details')],
        [InlineKeyboardButton("📞 Поддержка", callback_data='support')]
    ]
    
    await query.edit_message_text(
        "🚀 *Главное меню*\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ===== ОСНОВНАЯ ФУНКЦИЯ =====
def main():
    """Запуск бота на Railway"""
    if not BOT_TOKEN:
        logger.error("❌ ОШИБКА: BOT_TOKEN не установлен!")
        logger.info("📝 Установите в Railway: Variables → BOT_TOKEN")
        return
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_stars, pattern='^buy$')],
        states={
            WAITING_STARS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_stars)
            ]
        },
        fallbacks=[
            CommandHandler('start', start),
            CallbackQueryHandler(back_to_menu, pattern='^back$')
        ]
    )
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(calculator, pattern='^calculator$'))
    app.add_handler(CallbackQueryHandler(payment_details, pattern='^details$'))
    app.add_handler(CallbackQueryHandler(support, pattern='^support$'))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back$'))
    app.add_handler(CallbackQueryHandler(mark_paid, pattern='^paid_'))
    
    # Запускаем бота
    logger.info("=" * 50)
    logger.info("🚀 Telegram Stars Bot запускается на Railway!")
    logger.info(f"💰 Цена: {STAR_PRICE}₽ за звезду")
    logger.info(f"📦 Диапазон: {MIN_STARS}-{MAX_STARS} звезд")
    logger.info("=" * 50)
    
    app.run_polling()

if __name__ == '__main__':
    main()
