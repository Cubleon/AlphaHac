from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Леонид", "Кубинский"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Меню проекта", reply_markup=reply_markup)
    context.user_data["menu"] = "main_menu"
    context.user_data["section"] = "project_section"

# меню вопросов
async def user_questions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Назад", "Главная"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Задай свой вопрос", reply_markup=reply_markup)
    context.user_data["menu"] = "user_questions_menu"
