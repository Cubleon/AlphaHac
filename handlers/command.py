from telegram import Update
from telegram.ext import ContextTypes
from services.db_service import db

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # гарантируем, что пользователь есть в БД
    user_id = await db.ensure_user({
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code
    })
    # можно создать "стартовую" беседу, если нужно
    convs = await db.list_conversations(user_id, limit=1)
    if not convs:
        await db.create_conversation(user_id, title="Start")
    await update.message.reply_text(f"Привет, {user.first_name}! Я тебя запомнил 😊")
