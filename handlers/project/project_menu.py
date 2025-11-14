from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from telegram import Update
from telegram.ext import CallbackContext


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Леонид", "Кубинский"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Меню проекта", reply_markup=reply_markup)
    context.user_data["menu"] = "main_menu"
    context.user_data["section"] = "project_section"

# меню вопросов
async def user_questions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Назад", "Главная"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Задай свой вопрос", reply_markup=reply_markup)
    context.user_data["menu"] = "user_questions_menu"

# Функция удаления проекта
async def delete_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project_name = update.message.text.strip()
    projects = context.user_data.get("projects", [])

    if project_name in projects:
        projects.remove(project_name)
        await update.message.reply_text(f"Проект '{project_name}' удалён!")
    else:
        await update.message.reply_text(f"Проект '{project_name}' не найден.")

    # Обновляем меню проектов после удаления
    await main_menu(update, context)


buttons = {
    "Мои проекты": main_menu,
    "Создать новый проект": user_questions_menu,

}

async def project_handler(update: Update, context: CallbackContext):
    button_name = update.message.text
    prev_button = context.user_data.get("button")

    # Если мы создаем новый проект
    if prev_button == "projects_choosing_button":
        await main_menu(update, context)
    elif buttons.get(button_name):
        await buttons[button_name](update, context)
    else:
        await update.message.reply_text("Такой команды не существует")
