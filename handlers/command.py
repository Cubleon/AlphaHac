from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-помощник. Напиши мне любой вопрос, и я постараюсь ответить."
    )

def main():
    app = Application.builder().token("ТОКЕН_БОТА").build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
