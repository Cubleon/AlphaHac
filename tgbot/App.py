from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
from callbacks.menus import *
from callbacks.user_input_callback import main_callback


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(MessageHandler(filters.TEXT, main_callback))
    app.run_polling()


if __name__ == "__main__":
    main()
