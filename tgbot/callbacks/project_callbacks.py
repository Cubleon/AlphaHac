from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes, filters

from tgbot.callbacks.menus import manage_projects_menu, project_menu


async def choose_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project_name = update.message.text
    db = context.application.bot_data["db"]
    projects = [p[2] for p in db.list_projects(update.effective_user.id)]
    if project_name in projects:
        await update.message.reply_text(f"Выбран проект: {project_name}")
        context.user_data["current_project"] = project_name
        await project_menu(update, context)
    else:
        await update.message.reply_text("Проект не найден.")


async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши имя нового проекта:")

    context.user_data["state"] = "creating_project"


async def name_project_to_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    name = update.message.text.strip()
    projects = [p[2] for p in db.list_projects(update.effective_user.id)]
    if name in projects:
        await update.message.reply_text("Проект с таким именем уже существует.")
    else:
        db.create_project(update.effective_user.id, name, "[]")
        await update.message.reply_text(f"Проект '{name}' создан!")

    await manage_projects_menu(update, context)


async def delete_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]

    projects = db.list_projects(update.effective_user.id)
    if not projects:
        await update.message.reply_text("Нет проектов, чтобы удалить")
    else:
        keyboard = [[p[2]] for p in projects] + [["Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выбери проект, который хочешь удалить", reply_markup=reply_markup)

        context.user_data["state"] = "deleting_project"


async def name_project_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    db = context.application.bot_data["db"]
    projects = db.list_projects(update.effective_user.id)
    projects_names = [p[2] for p in projects]


    if name not in projects_names:
        await update.message.reply_text("Нет проекта с таким именем.")
    else:
        db.delete_project(update.effective_user.id, name)
        await update.message.reply_text(f"Проект '{name}' удалён!")

    await manage_projects_menu(update, context)
