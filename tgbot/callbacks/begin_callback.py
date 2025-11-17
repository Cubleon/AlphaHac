from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from tgbot.callbacks.menus import main_menu

async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)