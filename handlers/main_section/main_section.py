from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Мои проекты", "Настройки", "О боте", "В начало", "Задать вопрос", "Уведомления"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Главное меню", reply_markup=reply_markup)
    context.user_data["menu"] = "start"
    context.user_data["section"] = "main_section"


# кнопка помощи
async def help_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Я такой-то такой-то умею то-то тото"
    )
    await update.message.reply_text(text)
    await start(update, context)