import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes, filters
from tgbot.callbacks.menus import notifications_menu
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from services.db_service import db

TZ = ZoneInfo("Europe/Moscow")


async def show_all_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = await db.ensure_user({
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code
    })

    notifs = await db.list_notifications(user_id, unread_only=False, limit=100)
    if notifs:
        lines = []
        for n in notifs:
            due = n["due_at"].isoformat() if n["due_at"] else "—"
            lines.append(f"{n['title']}: {due} (id={n['id']})")
        text = "Мои уведомления:\n" + "\n".join(lines)
    else:
        text = "У вас пока нет уведомлений."

    await update.message.reply_text(text)

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
    h, m = map(int, update.message.text.strip().split(":"))
    context.user_data["notification_time"] = (h, m)
    await update.message.reply_text("Введите текст уведомления:")
    context.user_data["state"] = "waiting_text"
    context.user_data["menu"] = "notifications_menu"


async def save_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = context.user_data.get("notification_name")
        time_tuple = context.user_data.get("notification_time")
        # поддержка двух путей: текст может быть в user_data или в текущем сообщении
        message = context.user_data.get("notification_text") or (update.message.text if update.message else None)

        if not (name and time_tuple and message):
            await update.message.reply_text("Ошибка: не все данные уведомления заполнены.")
            return

        h, m = time_tuple
        user = update.effective_user
        user_id = await db.ensure_user({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code
        })

        # Нормализация TZ: если TZ — строка, попробуем ZoneInfo; если None — используем UTC
        tz = globals().get("TZ", None)
        if isinstance(tz, str):
            try:
                tz = ZoneInfo(tz)
            except Exception:
                tz = None
        if tz is None:
            # безопасный fallback
            from datetime import timezone
            tz = timezone.utc

        # вычислим ближайшую дату-время для due_at (aware datetime)
        now_local = datetime.now(tz)
        due_local = datetime(now_local.year, now_local.month, now_local.day, h, m, tzinfo=tz)
        if due_local <= now_local:
            due_local = due_local + timedelta(days=1)

        # сохраняем в базе (due_at — aware datetime)
        notif_id = await db.create_notification(
            user_id=user_id,
            title=name,
            body=message,
            payload={"text": message},
            due_at=due_local,
            ntype="scheduled"
        )

        # создаём job в job_queue; имя job = notif_id
        # run_daily ожидает объект datetime.time с tzinfo
        job = context.application.job_queue.run_daily(
            send_notification,
            time=time(h, m, tzinfo=tz),
            chat_id=update.effective_chat.id,
            data=message,
            name=str(notif_id)
        )

        # сохраняем association job id -> notification id в user_data (для быстрой отмены)
        context.user_data.setdefault("notifications_jobs", {})[str(notif_id)] = job.job_id

        await update.message.reply_text(
            f"Уведомление '{name}' установлено на {h:02d}:{m:02d} (следующая: {due_local.strftime('%Y-%m-%d %H:%M %Z')})"
        )

        # Сброс временных данных
        context.user_data.pop("notification_name", None)
        context.user_data.pop("notification_time", None)
        context.user_data.pop("notification_text", None)
        context.user_data["state"] = None
        context.user_data["menu"] = "notifications_menu"

    except Exception as e:
        # логируем и аккуратно сообщаем пользователю об ошибке
        import traceback
        tb = traceback.format_exc()
        # лог в контейнер/stdout
        print("Error in save_notification:", tb)
        # ответ пользователю (коротко)
        if update.message:
            await update.message.reply_text(f"Неверный ввод / ошибка: {e}")


# Шаг 3: задаём текст уведомления и создаём задачу
async def show_notifications_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = await db.ensure_user({
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code
    })

    notifs = await db.list_notifications(user_id, unread_only=False, limit=100)
    if notifs:
        # показываем текст + запоминаем mapping id->title
        keyboard = [[f"{n['title']}: {n['due_at'].strftime('%Y-%m-%d %H:%M') if n['due_at'] else '—'} ({n['id']})"] for
                    n in notifs]
        keyboard += [["Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        # сохраняем mapping для удаления
        context.user_data["notifs_map"] = {
            f"{n['title']}: {n['due_at'].strftime('%Y-%m-%d %H:%M') if n['due_at'] else '—'} ({n['id']})": str(n['id'])
            for n in notifs}
        context.user_data["menu"] = "notifications_menu"
        context.user_data["state"] = "notification_to_delete"
        await update.message.reply_text("Выберите уведомление для удаления", reply_markup=reply_markup)
    else:
        await update.message.reply_text("У вас нет уведомлений.")
        # вернуться в меню
        from tgbot.callbacks.menus import notifications_menu
        await notifications_menu(update, context)


async def delete_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sel = update.message.text.strip()
    mapping = context.user_data.get("notifs_map", {})
    nid = mapping.get(sel)
    if not nid:
        await update.message.reply_text("Уведомление не найдено.")
        from tgbot.callbacks.menus import notifications_menu
        await notifications_menu(update, context)
        return

    # помечаем read/delivered в БД
    await db.mark_notification_read(nid)
    await db.mark_delivered(nid)

    # пытаемся отменить job по имени (job.name == notif_id) или по job_id сохранённому ранее
    jobs = context.application.job_queue.get_jobs_by_name(str(nid))
    for job in jobs:
        job.schedule_removal()

    # если в user_data есть запись job_id — удалим
    njobs = context.user_data.get("notifications_jobs", {})
    job_id = njobs.pop(str(nid), None)
    # (в PTB нет прямого remove по job_id удобного интерфейса, но мы уже попытались удалить по name)

    await update.message.reply_text("Уведомление удалено.")
    # обновляем меню
    from tgbot.callbacks.menus import notifications_menu
    await notifications_menu(update, context)


async def send_notification(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    text = "Уведомление:\n" + context.job.data
    await context.bot.send_message(chat_id=chat_id, text=text)
