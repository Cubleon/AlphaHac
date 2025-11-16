from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

from tgbot.callbacks.menus import *

to = {
    "main_menu": main_menu,
    "manage_projects_menu": manage_projects_menu,
    "llm_base_menu": llm_base_menu,
    "llm_document_menu": llm_document_menu,
    "llm_table_menu": llm_table_menu,
    "project_menu": project_menu,
    "notifications_menu": notifications_menu
}


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menus = context.user_data.get("menus", [])
    menus.pop()
    await to[menus[-1]](update, context)
