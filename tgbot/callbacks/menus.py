from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.ext import CallbackContext

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Мои проекты", "О боте", "Общий чат", "Уведомления"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Главное меню", reply_markup=reply_markup)

    context.user_data["menu"] = "main_menu"
    context.user_data["state"] = "default"

async def manage_projects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = context.user_data.get("projects", [])
    keyboard = [[p] for p in projects] + [["Создать новый проект", "Удалить проект"]] + [["Назад"]]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выбери действие", reply_markup=reply_markup)

    context.user_data["menu"] = "manage_projects_menu"
    context.user_data["state"] = "default"

async def llm_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Назад", "В начало"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Задай свой вопрос", reply_markup=reply_markup)

    context.user_data["menu"] = "llm_menu"
    context.user_data["state"] = "asking_llm"

async def project_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Леонид", "Кубинский"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Меню проекта", reply_markup=reply_markup)

    context.user_data["menu"] = "project_menu"
    context.user_data["state"] = "default"

async def notifications_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Добавить уведомление", "Удалить уведомление", "Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    notifications_list = []
    for notif in context.user_data.get("notifications", []):
        # notif.name и notif.next_t (datetime) → строка вида "Будильник: 2025-11-15 09:00"
        notifications_list.append(f"{notif.name}: {notif.next_t.strftime('%Y-%m-%d %H:%M')}")

    if notifications_list:
        text = "Мои уведомления:\n" + "\n".join(notifications_list)
    else:
        text = "У вас пока нет уведомлений."

    await update.message.reply_text(text, reply_markup=reply_markup)

    context.user_data["menu"] = "notifications_menu"
    context.user_data["state"] = "default"

