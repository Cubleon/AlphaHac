from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes, filters

from tgbot.callbacks.menus import llm_menu
from services.llm_service import LMStudioClient

import asyncio

async def llm_text_to_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("history", None)
    client = LMStudioClient(chat_history=context.user_data["history"])
    sent = await update.message.reply_text("⏳ thinking...")
    last_edit_time = asyncio.get_event_loop().time()
    buffer = ""
    for chunk in client.respond_text_to_stream(update.message.text):
        buffer += chunk
        now = asyncio.get_event_loop().time()
        if len(buffer) > 100 or (now - last_edit_time) > 0.1:
            try:
                await sent.edit_text(buffer)
            except Exception:
                pass
            last_edit_time = now

    context.user_data["history"] = client.get_chat()
    print(context.user_data["history"])
    await llm_menu(update, context)


