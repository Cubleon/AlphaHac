from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.ext import CallbackContext
from services.db_service import db


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("menus", ["main_menu"])
    keyboard = [["Мои проекты", "О боте", "Задать вопрос", "Уведомления"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Главное меню", reply_markup=reply_markup)

    context.user_data["menu"] = "main_menu"
    context.user_data["state"] = "default"


async def manage_projects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = await db.ensure_user({
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code
    })

    projects = await db.list_projects(user_id, limit=50)

    project_names = [p["name"] for p in projects]

    menus = context.user_data.get("menus", [])
    if (menus and menus[-1] != "manage_projects_menu") or not menus:
        menus.append("manage_projects_menu")
    context.user_data["menus"] = menus

    if context.user_data.get("menu") != "manage_projects_menu":
        context.user_data["prev_menu"] = context.user_data.get("menu")

    context.user_data["projects"] = [{"id": str(p["id"]), "name": p["name"]} for p in projects]

    keyboard = [[p] for p in project_names] + [["Создать новый проект", "Удалить проект"]] + [["Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выбери действие", reply_markup=reply_markup)

    context.user_data["menu"] = "manage_projects_menu"
    context.user_data["state"] = "default"


answers = {
    "Резюмировать": "Пришли файл или текст, который надо резюмировать",
    "Задать вопрос": "Задай свой вопрос",
    "Письмо": "Уточни детали письма, например, цель, контекст и т.д.",
    "Таблица": "Уточни, какая должна быть таблица",
    "Документ": "Уточни, что должно быть в документе"
}


async def llm_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menus = context.user_data.get("menus", [])
    if (menus and menus[-1] != "llm_menu") or not menus:
        menus.append("llm_menu")
    context.user_data["menus"] = menus

    request = update.message.text
    keyboard = [["Назад", "В начало"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    try:
        await update.message.reply_text(answers[request], reply_markup=reply_markup)
    except:
        pass

    context.user_data["menu"] = "llm_menu"
    context.user_data["state"] = "asking_llm"


async def project_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menus = context.user_data.get("menus", [])
    if (menus and menus[-1] != "project_menu") or not menus:
        menus.append("project_menu")
    context.user_data["menus"] = menus

    keyboard = [["Задать вопрос", "Резюмировать", "Письмо", "Таблица", "Документ", "Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Меню проекта", reply_markup=reply_markup)

    context.user_data["menu"] = "project_menu"
    context.user_data["state"] = "default"


async def notifications_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menus = context.user_data.get("menus", [])
    if (menus and menus[-1] != "notifications_menu") or not menus:
        menus.append("notifications_menu")
    context.user_data["menus"] = menus

    keyboard = [["Добавить уведомление", "Удалить уведомление", "Показать все уведомления", "Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Выбери действие", reply_markup=reply_markup)

    context.user_data["menu"] = "notifications_menu"
    context.user_data["state"] = "default"
