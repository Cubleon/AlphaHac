from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import TELEGRAM_TOKEN
from telegram import Update, ReplyKeyboardMarkup
from handlers.main_section.main_section import start
from main_handler import handler as main_handler

# кнопка назад
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO make normal transitions for back button (add requests history)
    await start(update, context)

# меню
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("В начало"), start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Главное"), start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Назад"), back))
    app.add_handler(MessageHandler(filters.TEXT, main_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
