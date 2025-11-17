from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes, filters
from tgbot.callbacks.menus import notifications_menu
from datetime import time
from datetime import datetime
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Europe/Moscow")


async def show_all_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    text = ""
    for notif in db.list_notifications(update.effective_user.id):
        h, m = map(int, notif[5].split(":"))
        if time(datetime.now(tz=TZ).hour, datetime.now(tz=TZ).minute, tzinfo=TZ) > time(h, m, tzinfo=TZ):
            db.update_notification_id(notif[0])
        if not notif[6]:
            text += f"Уведомление '{notif[2]}' установлено на {notif[5]}:\n{notif[3]}\n"

    if not text:
        await update.message.reply_text("У вас пока нет активных уведомлений")
    else:
        await update.message.reply_text(text)

async def ask_notification_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите имя уведомления:")
    context.user_data["state"] = "waiting_name"
    context.user_data["menu"] = "notifications_menu"


async def ask_notification_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data["notification_name"] = name
    await update.message.reply_text("Введите время уведомления в формате чч:мм:")
    context.user_data["state"] = "waiting_time"
    context.user_data["menu"] = "notifications_menu"


async def ask_notification_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    h, m = map(int, update.message.text.split(":"))
    context.user_data["notification_time"] = (h, m)
    await update.message.reply_text("Введите текст уведомления:")
    context.user_data["state"] = "waiting_text"
    context.user_data["menu"] = "notifications_menu"


async def save_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data.get("notification_name")
    time_tuple = context.user_data.get("notification_time")
    message = context.user_data.get("notification_text") or update.message.text  # на случай если текст ещё не сохранён

    db = context.application.bot_data["db"]
    db.create_notification(update.effective_user.id, name, message, f"{time_tuple[0]:02d}:{time_tuple[1]:02d}")

    if not (name and time_tuple and message):
        await update.message.reply_text("Ошибка: не все данные уведомления заполнены.")
        return

    h, m = time_tuple

    job = context.application.job_queue.run_once(
        send_notification,
        when=time(h, m, tzinfo=TZ),
        chat_id=update.effective_chat.id,
        data=message,
        name=name
    )
    context.user_data["notifications"].append(job)

    await update.message.reply_text(f"Уведомление '{name}' установлено на {h:02d}:{m:02d}:\n{message}")
    await notifications_menu(update, context)


async def show_notifications_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    notifications_list = []
    for notif in db.list_notifications(update.effective_user.id):
        h, m = map(int, notif[5].split(":"))
        if time(datetime.now(tz=TZ).hour, datetime.now(tz=TZ).minute, tzinfo=TZ) > time(h, m, tzinfo=TZ):
            db.update_notification_id(notif[0])
        if not notif[6]:
            notifications_list.append(f"{notif[2]}: {h:02d}:{m:02d}")

    context.user_data["menu"] = "notifications_menu"
    context.user_data["state"] = "notification_to_delete"
    if notifications_list:
        text = "Выберите уведомление для удаления"
        keyboard = [notifications_list] + [["Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await notifications_menu(update, context)


async def delete_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name, time = update.message.text.split(": ")

    db = context.application.bot_data["db"]

    for num, notif in enumerate(context.user_data.get("notifications")):
        h, m = notif.next_t.hour, notif.next_t.minute
        if (name, time) == (notif.name, f"{h:02d}:{m:02d}"):
            notif.schedule_removal()
            context.user_data.get("notifications").pop(num)
            db.update_notification(name, time)

            text = f"Уведомление {name} удалено"
            await update.message.reply_text(text)
            break
    else:
        await update.message.reply_text("Уведомление не найдено")

    await notifications_menu(update, context)

async def send_notification(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    text = "Уведомление:\n" + context.job.data
    await context.bot.send_message(chat_id=chat_id, text=text)


def run_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]
    context.user_data.setdefault("notifications", [])
    for notif in db.list_notifications(update.effective_user.id):
        h, m = map(int, notif[5].split(":"))
        if time(datetime.now(tz=TZ).hour, datetime.now(tz=TZ).minute, tzinfo=TZ) > time(h, m, tzinfo=TZ):
            db.update_notification_id(notif[0])
        if not notif[6]:
            job = context.application.job_queue.run_once(
                send_notification,
                when=time(h, m, tzinfo=TZ),
                chat_id=update.effective_chat.id,
                data=notif[3],
                name=notif[2]
            )
            context.user_data["notifications"].append(job)