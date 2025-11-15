from telegram import Update
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes,  filters

from callbacks.project_callbacks import name_project_to_create, name_project_to_delete, choose_project
from callbacks.llm_callbacks import llm_answer

actions = {
    "manage_projects_menu": {
        "default": choose_project,
        "creating_project": name_project_to_create,
        "deleting_project": name_project_to_delete
    },
    "llm_menu": {
        "asking_llm": llm_answer
    }
}

async def main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await actions[context.user_data["menu"]][context.user_data["state"]](update, context)
    except:
        await update.message.reply_text("Неверный ввод")

