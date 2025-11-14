# handlers/__init__.py
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from services.db_service import db
from handlers import commands, messages
from config import BOT_TOKEN

async def on_startup(app):
    # инициализируем DB пул
    await db.init()

async def on_shutdown(app):
    await db.close()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", commands.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages.handle_message))
    app.post_init(on_startup)
    app.on_stop.append(on_shutdown)  # корректно закроем пул при остановке
    app.run_polling()

if __name__ == "__main__":
    main()

# Инициализирует пул соединений PostgreSQL при старте.
# Закрывает соединения при остановке.
# Регистрирует хэндлеры /start и текстовых сообщений.