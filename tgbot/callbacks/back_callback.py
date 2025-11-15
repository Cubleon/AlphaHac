from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from callbacks.menus import main_menu

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)