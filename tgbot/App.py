from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
from callbacks.menus import main_menu
from callbacks.user_input_callback import main_callback

from services.db_service import Database


async def on_startup(app: Application):
    app.bot_data["db"] = Database()


async def on_shutdown(app: Application) -> None:
    db = app.bot_data.get("db")
    db.close()


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(on_startup).post_shutdown(on_shutdown).build()
    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, main_callback))
    app.run_polling()


if __name__ == "__main__":
    main()
