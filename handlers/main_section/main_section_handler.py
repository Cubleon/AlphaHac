from telegram import Update
from telegram.ext import CallbackContext
from handlers.main_section.main_section import start, help_info
from handlers.GPT_processing.GPT_processing_handler import GPT_processing_handler
from handlers.project_choosing.project_choosing_handler import project_choosing_handler

async def main_section_handler(update: Update, context: CallbackContext):
    message = update.message.text
    menu = context.user_data["menu"]
    if menu == "start" and message == "Мои проекты":
        context.user_data["section"] = "project_choosing_section"
        await project_choosing_handler(update, context)
    elif message == "Задать вопрос":
        await GPT_processing_handler(update, context)
    elif message == "В начало":
        await  start(update, context)
    elif message == "О боте":
        await help_info(update, context)

