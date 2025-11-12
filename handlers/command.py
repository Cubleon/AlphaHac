from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import TELEGRAM_TOKEN
from handlers.main_handler import handler as main_handler
from project_choosing.command_handler import project_choosing_handler
from main_handler import handler as main_handler


# меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Мои проекты", "Настройки", "О боте", "В начало"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Главное меню", reply_markup=reply_markup)
    context.user_data["menu"] = "start"
    context.user_data["section"] = "main_section"

# кнопка назад
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #TODO make normal transitions for back button (add requests history)
    await start(update, context)

# кнопка помощи
async def help_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Я такой-то такой-то умею то-то тото"
    )
    await update.message.reply_text(text)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Главная$"), help_info))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("О боте$"), help_info))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Назад$"), back))
    app.add_handler(MessageHandler(filters.TEXT, main_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
