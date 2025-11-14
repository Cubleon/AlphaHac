from telegram import Update
from telegram.ext import CallbackContext
from handlers.GPT_processing.GPT_processing_handler import GPT_processing_handler
from handlers.main_section.main_section import main_section_handler
from handlers.project_choosing.projects_choosing import project_choosing_handler
from handlers.project.project_menu import project_handler

section_handlers = {
    "main_section": main_section_handler,
    "project_section": project_handler,
    "projects_choosing_section": project_choosing_handler,
    "GPT_processing_section": GPT_processing_handler
}

async def handler(update: Update, context: CallbackContext):
    section = context.user_data.get("section")
    if section_handlers.get(section):
        await section_handlers[section](update, context)
    else:
        await update.message.reply_text("Проект не найден.")