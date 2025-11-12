from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Обработка файлов
async def document_processing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Обработать документ", "Создать документ", "Загрузить документ", "Назад", "Главное меню"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Обработка документов", reply_markup=reply_markup)
    context.user_data["menu"] = "document_processing"
    context.user_data["section"] = "file_processing"

# меню загрузки
async def upload_document_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Назад", "Главная"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Отправь файл для обработки:", reply_markup=reply_markup)
    context.user_data["menu"] = "upload_menu"
    context.user_data["section"] = "file_processing"

async def upload_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("menu") == "upload":
        file = await update.message.document.get_file()
        await file.download_to_drive(f"./{update.message.document.file_name}")
        await update.message.reply_text(f"Файл {update.message.document.file_name} сохранён!")
    else:
        await update.message.reply_text("Сначала выбери 'Загрузить файл' в меню.")
