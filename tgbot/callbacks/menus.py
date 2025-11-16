from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.ext import CallbackContext

answers = {
    "Сгенерировать документ": "Уточни, что должно быть в документе",
    "Сгенерировать таблицу": "Уточни, какая должна быть таблица",
    "Анализировать таблицу": "Пришли файл в формате xlsx для анализа",
    "Анализировать документ": "Пришли файл в формате docx или pdf для анализа",
    "Задать вопрос": "Задай свой вопрос",
    "Резюмировать": "Пришли файл (pdf или docx) или текст, который надо резюмировать",
    "Письмо": "Уточни, какое должно быть письмо",
    "Презентация": "Пришли файл в формате pdf для анализа"
}

states = {
    "Сгенерировать документ": "llm_generate_document",
    "Анализировать документ": "llm_analyse_document",
    "Сгенерировать таблицу": "llm_generate_table",
    "Анализировать таблицу": "llm_analyse_table",
    "Задать вопрос": "llm_answer_question",
    "Резюмировать": "llm_summarize",
    "Письмо": "llm_letter",
    "Презентация": "llm_analyse_presentation"
}

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("menus", ["main_menu"])
    keyboard = [["Мои проекты", "О боте", "Задать вопрос", "Уведомления"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Главное меню", reply_markup=reply_markup)

    context.user_data["menu"] = "main_menu"
    context.user_data["state"] = "default"


async def manage_projects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menus = context.user_data.get("menus", [])
    if (menus and menus[-1] != "manage_projects_menu") or not menus:
        menus.append("manage_projects_menu")
    context.user_data["menus"] = menus

    if context.user_data["menu"] != "manage_projects_menu":
        context.user_data["prev_menu"] = context.user_data["menu"]

    projects = context.user_data.get("projects", [])
    keyboard = [[p] for p in projects] + [["Создать новый проект", "Удалить проект"]] + [["Назад"]]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выбери действие", reply_markup=reply_markup)

    context.user_data["menu"] = "manage_projects_menu"
    context.user_data["state"] = "default"


async def llm_base_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menus = context.user_data.get("menus", [])
    if (menus and menus[-1] != "llm_base_menu") or not menus:
        menus.append("llm_base_menu")
    context.user_data["menus"] = menus

    request = update.message.text

    keyboard = [["Назад", "В начало"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if request in answers:
        await update.message.reply_text(answers[request], reply_markup=reply_markup)

    context.user_data["menu"] = "llm_base_menu"
    if request in states:
        context.user_data["state"] = states[request]

async def llm_table_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menus = context.user_data.get("menus", [])
    if (menus and menus[-1] != "llm_table_menu") or not menus:
        menus.append("llm_table_menu")
    context.user_data["menus"] = menus

    request = update.message.text
    keyboard = [["Сгенерировать таблицу", "Анализировать таблицу"]] + [["Назад", "В начало"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Меню для работы с таблицами", reply_markup=reply_markup)

    context.user_data["menu"] = "llm_table_menu"
    context.user_data["state"] = "default"

async def llm_document_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menus = context.user_data.get("menus", [])
    if (menus and menus[-1] != "llm_document_menu") or not menus:
        menus.append("llm_document_menu")
    context.user_data["menus"] = menus

    request = update.message.text
    keyboard = [["Сгенерировать документ", "Анализировать документ"]] + [["Назад", "В начало"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Меню для работы с документами", reply_markup=reply_markup)

    context.user_data["menu"] = "llm_document_menu"
    context.user_data["state"] = "default"

async def project_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menus = context.user_data.get("menus", [])
    if (menus and menus[-1] != "project_menu") or not menus:
        menus.append("project_menu")
    context.user_data["menus"] = menus

    keyboard = [["Задать вопрос", "Резюмировать", "Письмо", "Таблица", "Документ", "Презентация", "Назад"]]
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
