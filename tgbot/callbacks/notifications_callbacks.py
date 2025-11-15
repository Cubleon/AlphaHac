from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes, filters
from tgbot.callbacks.menus import notifications_menu
from datetime import time
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Moscow")

# Шаг 1: задаём имя уведомления
async def ask_notification_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите имя уведомления:")
    context.user_data["state"] = "waiting_name"
    context.user_data["menu"] = "notifications_menu"

# Шаг 2: задаём время
async def ask_notification_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data["notification_name"] = name
    await update.message.reply_text("Введите время уведомления в формате чч:мм:")
    context.user_data["state"] = "waiting_time"
    context.user_data["menu"] = "notifications_menu"

# Шаг 3: задаём текст уведомления и создаём задачу
async def ask_notification_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        h, m = map(int, update.message.text.split(":"))
    except:
        await update.message.reply_text("Неверный формат времени. Попробуйте снова.")
        return

    context.user_data["notification_time"] = (h, m)
    await update.message.reply_text("Введите текст уведомления:")
    context.user_data["state"] = "waiting_text"
    context.user_data["menu"] = "notifications_menu"

async def save_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Берём данные из user_data
    name = context.user_data.get("notification_name")
    time_tuple = context.user_data.get("notification_time")
    message = context.user_data.get("notification_text") or update.message.text  # на случай если текст ещё не сохранён

    if not (name and time_tuple and message):
        await update.message.reply_text("Ошибка: не все данные уведомления заполнены.")
        return

    h, m = time_tuple

    # создаём ежедневную задачу
    job = context.application.job_queue.run_daily(
        send_notification,
        time=time(h, m, tzinfo=TZ),
        chat_id=update.effective_chat.id,
        data=message,
        name=name
    )

    # сохраняем job в user_data
    if "notifications" in context.user_data:
        context.user_data["notifications"].append(job)
    else:
        context.user_data["notifications"] = [job]

    await update.message.reply_text(f"Уведомление '{name}' установлено на {h:02d}:{m:02d}:\n{message}")

    # Сброс временных данных
    context.user_data.pop("notification_name", None)
    context.user_data.pop("notification_time", None)
    context.user_data.pop("notification_text", None)
    context.user_data["state"] = None
    context.user_data["menu"] = "notifications_menu"

    await notifications_menu(update, context)

# Шаг 3: задаём текст уведомления и создаём задачу
async def show_notifications_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notifications_list = []
    for notif in context.user_data.get("notifications", []):
        # notif.name и notif.next_t (datetime) → строка вида "Будильник: 2025-11-15 09:00"
        notifications_list.append(f"{notif.name}: {notif.next_t.strftime('%Y-%m-%d %H:%M')}")

    context.user_data["menu"] = "notifications_menu"
    context.user_data["state"] = "notification_to_delete"
    if notifications_list:
        text = "Выберите уведомление для удаления"
        keyboard = [notifications_list] + [["Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(text, reply_markup = reply_markup)
    else:
        await notifications_menu(update, context)

async def delete_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name, time = update.message.text.split(": ", 1)
    for num, notif in enumerate(context.user_data.get("notifications")):
        if (name, time) == (notif.name, notif.next_t.strftime('%Y-%m-%d %H:%M')):
            notif.schedule_removal()
            del context.user_data.get("notifications")[num]
            text = f"Уведомление {name} удалено"
            await update.message.reply_text(text)
            await notifications_menu(update, context)
            break
    else:
        text = "Уведомление не найдено"
        await update.message.reply_text(text)
        await notifications_menu(update, context)

async def send_notification(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    text = "Уведомление:\n" + context.job.data
    await context.bot.send_message(chat_id=chat_id, text=text)
