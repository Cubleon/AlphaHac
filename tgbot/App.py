from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
from callbacks.menus import *
from callbacks.notifications_callbacks import ask_notification_name, show_notifications_to_delete
from callbacks.project_callbacks import create_project, delete_project
from callbacks.user_input_callback import main_callback
from callbacks.back_callback import back
from callbacks.help_callback import help

handlers = {
    "Мои проекты": manage_projects_menu,
    "Создать новый проект": create_project,
    "Уведомления": notifications_menu,
    "Добавить уведомление": ask_notification_name,
    "Удалить уведомление": show_notifications_to_delete,
    "Удалить проект": delete_project,
    "Общий чат": llm_menu,
    "Назад": back,
    "О боте": help,
}

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", main_menu))

    for msg in handlers:
        app.add_handler(MessageHandler(filters.TEXT & filters.Regex(msg), handlers[msg]))

    app.add_handler(MessageHandler(filters.TEXT, main_callback))
    app.run_polling()


if __name__ == "__main__":
    main()
