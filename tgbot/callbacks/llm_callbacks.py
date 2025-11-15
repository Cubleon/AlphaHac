from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes,  filters

from callbacks.menus import llm_menu

async def llm_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    answer = "Я ответ нейронки"
    await update.message.reply_text(answer)
    await llm_menu(update, context)


