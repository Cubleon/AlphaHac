from telegram import Update
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes, filters
from tgbot.callbacks.project_callbacks import name_project_to_create, name_project_to_delete, choose_project
from tgbot.callbacks.notifications_callbacks import *
from tgbot.callbacks.llm_callbacks import llm_text_to_text

actions = {
    "manage_projects_menu": {
        "default": choose_project,
        "creating_project": name_project_to_create,
        "deleting_project": name_project_to_delete
    },
    "llm_menu": {
        "asking_llm": llm_text_to_text
    },
    "notifications_menu": {
        "waiting_name": ask_notification_time,
        "waiting_time": ask_notification_text,
        "waiting_text": save_notification,
        "notification_to_delete": delete_notification
    }
}


async def main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await actions[context.user_data["menu"]][context.user_data["state"]](update, context)
    # try:
    #
    # except:
    #     await update.message.reply_text("Неверный ввод")
