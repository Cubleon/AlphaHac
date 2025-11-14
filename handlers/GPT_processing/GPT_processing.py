from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

async def gpt_ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
    #TODO


async def gpt_process_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # запрос в нейронку
    answer = "Я ответ нейронки"
    await update.message.reply_text(answer)

    # сразу снова показываем меню задавания вопроса
    await gpt_ask_question(update, context)
