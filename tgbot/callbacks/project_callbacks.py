from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes,  filters

from callbacks.menus import manage_projects_menu, project_menu


async def choose_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project_name = update.message.text
    if project_name in context.user_data.get("projects", []):
        await update.message.reply_text(f"Выбран проект: {project_name}")
        context.user_data["current_project"] = project_name
    else:
        await update.message.reply_text("Проект не найден.")

    await project_menu(update, context)


async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши имя нового проекта:")

    context.user_data["state"] = "creating_project"

async def name_project_to_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    projects = context.user_data.setdefault("projects", [])
    if name in projects:
        await update.message.reply_text("Проект с таким именем уже существует.")
    else:
        projects.append(name)
        await update.message.reply_text(f"Проект '{name}' создан!")

    await manage_projects_menu(update, context)
async def delete_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = context.user_data.get("projects", [])
    if not projects:
        await update.message.reply_text("Нет проектов, чтобы удалить")
    else:
        keyboard = [[p] for p in projects] + [["Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выбери проект, который хочешь удалить", reply_markup=reply_markup)

        context.user_data["state"] = "deleting_project"

async def name_project_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    projects = context.user_data.setdefault("projects", [])
    if name not in projects:
        await update.message.reply_text("Нет проекта с таким именем.")
    else:
        projects.remove(name)
        await update.message.reply_text(f"Проект '{name}' удалён!")

    await manage_projects_menu(update, context)



