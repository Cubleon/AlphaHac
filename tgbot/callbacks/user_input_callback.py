from telegram import Update
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes, filters
from tgbot.callbacks.notifications_callbacks import *
from tgbot.callbacks.llm_callbacks import *
from tgbot.callbacks.back_callback import back
from tgbot.callbacks.help_callback import help
from tgbot.callbacks.begin_callback import begin
from tgbot.callbacks.project_callbacks import *

from tgbot.callbacks.menus import *

handlers = {
    "Мои проекты": manage_projects_menu,
    "Создать новый проект": create_project,
    "Уведомления": notifications_menu,
    "Добавить уведомление": ask_notification_name,
    "Удалить уведомление": show_notifications_to_delete,
    "Показать все уведомления": show_all_notifications,
    "Удалить проект": delete_project,
    "Назад": back,
    "О боте": help,
    "Задать вопрос": llm_base_menu,
    "Резюмировать": llm_base_menu,
    "Письмо": llm_base_menu,
    "Таблица": llm_table_menu,
    "Сгенерировать таблицу": llm_base_menu,
    "Анализировать таблицу": llm_base_menu,
    "Сгенерировать документ": llm_base_menu,
    "Анализировать документ": llm_base_menu,
    "Документ": llm_document_menu,
    "Презентация": llm_base_menu,
    "В начало": begin
}

actions = {
    "manage_projects_menu": {
        "default": choose_project,
        "creating_project": name_project_to_create,
        "deleting_project": name_project_to_delete
    },
    "llm_base_menu": {
        "llm_answer_question": llm_answer_question,
        "llm_summarize": llm_summarize,
        "llm_letter": llm_letter,
        "llm_generate_table": llm_generate_table,
        "llm_analyse_table": llm_analyse_table,
        "llm_generate_document": llm_generate_document,
        "llm_analyse_document": llm_analyse_document,
        "llm_analyse_presentation": llm_analyse_presentation
    },
    "notifications_menu": {
        "waiting_name": ask_notification_time,
        "waiting_time": ask_notification_text,
        "waiting_text": save_notification,
        "notification_to_delete": delete_notification
    }
}



async def main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text in handlers:
        await handlers[update.message.text](update, context)
    else:
        try:
            await actions[context.user_data["menu"]][context.user_data["state"]](update, context)
        except:
            await update.message.reply_text("Неверный ввод")



