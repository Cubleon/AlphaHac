from telegram import Update
from telegram.ext import CallbackContext

from handlers.GPT_processing.GPT_processing import gpt_ask_question, gpt_process_question


async def GPT_processing_handler(update: Update, context: CallbackContext):
    message = update.message.text
    menu = context.user_data["menu"]
    section = context.user_data["section"]
    if section == "main_section" and message == "Задать вопрос":
        await gpt_ask_question(update, context)
    if section == "GPT_processing" and menu == "gpt_ask_question":
        await gpt_process_question(update, context)


