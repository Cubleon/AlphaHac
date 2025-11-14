# handlers/message.py
from telegram import Update
from telegram.ext import ContextTypes
from services.db_service import db

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = await db.ensure_user({
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code
    })

    # возьмём последнюю беседу или создадим новую
    convs = await db.list_conversations(user_id, limit=1)
    if convs:
        conv_id = str(convs[0]['id'])
    else:
        conv_id = await db.create_conversation(user_id, title="Диалог")

    text = update.message.text
    # сохраняем сообщение пользователя
    await db.save_message(conv_id, role="user", content=text, token_count=0)

    # заглушка LLM-ответа (здесь разместишь вызов llm_service)
    reply = f"Эхо: {text}"

    # сохраняем ответ ассистента
    await db.save_message(conv_id, role="assistant", content=reply, token_count=0)
    await update.message.reply_text(reply)
