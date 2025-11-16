from telegram import Update
from telegram.ext import ContextTypes

from services.db_service import db
from tgbot.callbacks.menus import llm_menu


async def llm_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    tg_user = update.effective_user

    user_id = await db.ensure_user({
        "id": tg_user.id,
        "username": tg_user.username,
        "first_name": tg_user.first_name,
        "last_name": tg_user.last_name,
        "language_code": tg_user.language_code
    })

    project = context.user_data.get("current_project")
    project_id = project["id"] if project else None

    conversation_id = await db.get_or_create_conversation(
        user_id=user_id,
        project_id=project_id
    )

    await db.add_message(
        conversation_id=conversation_id,
        role="user",
        content=user_text
    )

    answer = "Я ответ нейронки"

    await db.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer
    )

    await update.message.reply_text(answer)

    await llm_menu(update, context)
