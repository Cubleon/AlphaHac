from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import BOT_TOKEN
from tgbot.callbacks.menus import *
from tgbot.callbacks.notifications_callbacks import ask_notification_name, show_notifications_to_delete, show_all_notifications
from tgbot.callbacks.project_callbacks import create_project, delete_project
from tgbot.callbacks.user_input_callback import main_callback
from tgbot.callbacks.back_callback import back
from tgbot.callbacks.help_callback import help

from services.db_service import db
from tgbot.scheduler import restore_scheduled_notifications
from config import BOT_TOKEN
import asyncio

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
    "Задать вопрос": llm_menu,
    "Резюмировать": llm_menu,
    "Письмо": llm_menu,
    "Таблица": llm_menu,
    "Документ": llm_menu
}

async def on_startup(app):
    # инициализируем пул и создаём таблицы
    await db.init()
    # восстановим задачи уведомлений из БД
    await restore_scheduled_notifications(app)

async def on_shutdown(app):
    await db.close()

def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(on_startup)     # запускается после инициализации
        .post_stop(on_shutdown)    # запускается при остановке
        .build()
    )

    app.add_handler(CommandHandler("start", main_menu))

    for msg in handlers:
        app.add_handler(MessageHandler(filters.TEXT & filters.Regex(msg), handlers[msg]))

    app.add_handler(MessageHandler(filters.TEXT, main_callback))

    app.run_polling()

if __name__ == "__main__":
    main()
