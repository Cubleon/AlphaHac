from telegram import Update
from telegram.ext import CallbackContext
from handlers.project_choosing.command_handler import project_choosing_handler
from handlers.project.command_handler import project_handler

async def handler(update: Update, context: CallbackContext):
    section = context.user_data.get("section")
    if section == "main_section":
        message = update.message.text
        if message == "Мои проекты":
            await project_choosing_handler(update, context)
    elif section == "project_section":
        await project_handler(update, context)
    elif section == "projects_choosing_section":
        await project_choosing_handler(update, context)