from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.ext import CallbackContext
from handlers.GPT_processing.GPT_processing_handler import GPT_processing_handler
from handlers.project_choosing.projects_choosing import project_choosing_handler


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Мои проекты", "Настройки", "О боте", "В начало", "Задать вопрос", "Уведомления"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Главное меню", reply_markup=reply_markup)
    context.user_data["button"] = "start"
    context.user_data["section"] = "main_section"

# кнопка помощи
async def help_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Я такой-то такой-то умею то-то тото"
    )
    await update.message.reply_text(text)
    await start(update, context)

buttons = {
    "Мои проекты": project_choosing_handler,
    "Задать вопрос": GPT_processing_handler,
    "В начало": GPT_processing_handler,
    "О боте": help_info,
}

async def main_section_handler(update: Update, context: CallbackContext):
    button_name = update.message.text
    if buttons.get(button_name):
        await buttons[button_name](update, context)
    else:
        await update.message.reply_text("Такой команды не существует")



