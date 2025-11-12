from telegram import Update
from telegram.ext import CallbackContext
from handlers.project_choosing.projects_choosing_menu import projects_choosing_menu, project_chosen, create_project, save_new_project


async def project_choosing_handler(update: Update, context: CallbackContext):
    message = update.message.text
    menu = context.user_data["menu"]
    if menu == "creating_project":
        await save_new_project(update, context)
    elif message == "Мои проекты":
        await projects_choosing_menu(update, context)
    elif message == "Создать новый проект":
        await create_project(update, context)

