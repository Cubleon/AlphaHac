from telegram import Update
from telegram.ext import CallbackContext

from handlers.GPT_processing.GPT_processing_handler import GPT_processing_handler
from handlers.main_section.main_section_handler import main_section_handler
from handlers.project_choosing.project_choosing_handler import project_choosing_handler
from handlers.project.project_handler import project_handler

async def handler(update: Update, context: CallbackContext):
    section = context.user_data.get("section")
    message = context.user_data.get("message")
    if message == "В начало":
        await main_section_handler(update, context)
    elif section == "main_section":
        await main_section_handler(update, context)
    elif section == "project_section":
        await project_handler(update, context)
    elif section == "projects_choosing_section":
        await project_choosing_handler(update, context)
    elif section == "GPT_processing_section":
        await GPT_processing_handler(update, context)