from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я бот помощник")
