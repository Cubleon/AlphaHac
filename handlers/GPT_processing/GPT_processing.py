from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

async def gpt_ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Назад", "В начало"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Задай свой вопрос", reply_markup=reply_markup)
    context.user_data["menu"] = "gpt_ask_question"
    context.user_data["section"] = "GPT_processing"


async def gpt_process_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # запрос в нейронку
    answer = "Я ответ нейронки"
    await update.message.reply_text(answer)

    # сразу снова показываем меню задавания вопроса
    await gpt_ask_question(update, context)
