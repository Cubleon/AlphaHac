from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes, filters

from tgbot.callbacks.menus import manage_projects_menu, project_menu
from services.db_service import db

async def choose_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    projects = context.user_data.get("projects", [])
    found = next((p for p in projects if p["name"] == name), None)
    if not found:
        await update.message.reply_text("Проект не найден.")
        return

    # сохраняем текущий проект в user_data (id и name)
    context.user_data["current_project"] = found
    await update.message.reply_text(f"Выбран проект: {name}")
    await project_menu(update, context)

async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши имя нового проекта:")
    context.user_data["state"] = "creating_project"


async def name_project_to_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    user = update.effective_user
    user_id = await db.ensure_user({
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code
    })

    existing = await db.list_projects(user_id, limit=100)
    if any(p["name"] == name for p in existing):
        await update.message.reply_text("Проект с таким именем уже существует.")
    else:
        project_id = await db.create_project(user_id, name)
        await update.message.reply_text(f"Проект '{name}' создан! (id: {project_id})")

    # обновляем меню (оно подтянет проекты из БД)
    await manage_projects_menu(update, context)


async def delete_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = await db.ensure_user({
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code
    })

    projects = await db.list_projects(user_id, limit=100)
    if not projects:
        await update.message.reply_text("Нет проектов, чтобы удалить")
        return

    keyboard = [[p["name"]] for p in projects] + [["Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выбери проект, который хочешь удалить", reply_markup=reply_markup)
    context.user_data["state"] = "deleting_project"
    # сохраняем mapping (name -> id)
    context.user_data["projects_to_delete"] = {p["name"]: str(p["id"]) for p in projects}


async def name_project_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    mapping = context.user_data.get("projects_to_delete", {})
    project_id = mapping.get(name)
    if not project_id:
        await update.message.reply_text("Нет проекта с таким именем.")
    else:
        await db.delete_project(project_id)
        await update.message.reply_text(f"Проект '{name}' удалён!")

    # сброс состояния и показ меню
    context.user_data.pop("projects_to_delete", None)
    await manage_projects_menu(update, context)
