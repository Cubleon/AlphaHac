from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes, filters

from tgbot.callbacks.menus import *
from services.llm_service import LMStudioClient

import asyncio


async def llm_answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("history", None)
    client = LMStudioClient(chat_from_history=context.user_data["history"])
    sent = await update.message.reply_text("⏳ thinking...")
    last_edit_time = asyncio.get_event_loop().time()
    buffer = ""

    prompt = update.message.text

    for chunk in client.respond_text_to_stream(prompt):
        buffer += chunk
        now = asyncio.get_event_loop().time()
        if len(buffer) > 100 or (now - last_edit_time) > 0.1:
            try:
                await sent.edit_text(buffer)
            except Exception:
                pass
            last_edit_time = now

    context.user_data["history"] = client.get_chat()
    await llm_base_menu(update, context)

async def llm_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("history", None)
    client = LMStudioClient(chat_from_history=context.user_data["history"])
    sent = await update.message.reply_text("⏳ thinking...")
    last_edit_time = asyncio.get_event_loop().time()
    buffer = ""

    prompt = "Срезюмируй следующий текст: \n" + update.message.text

    for chunk in client.respond_text_to_stream(prompt):
        buffer += chunk
        now = asyncio.get_event_loop().time()
        if len(buffer) > 100 or (now - last_edit_time) > 0.1:
            try:
                await sent.edit_text(buffer)
            except Exception:
                pass
            last_edit_time = now

    context.user_data["history"] = client.get_chat()
    await llm_base_menu(update, context)

async def llm_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("history", None)
    client = LMStudioClient(chat_from_history=context.user_data["history"])
    sent = await update.message.reply_text("⏳ thinking...")
    last_edit_time = asyncio.get_event_loop().time()
    buffer = ""

    prompt = "Составь письмо, удовлетворяющее следующим требованиям: \n" + update.message.text

    for chunk in client.respond_text_to_stream(prompt):
        buffer += chunk
        now = asyncio.get_event_loop().time()
        if len(buffer) > 100 or (now - last_edit_time) > 0.1:
            try:
                await sent.edit_text(buffer)
            except Exception:
                pass
            last_edit_time = now

    context.user_data["history"] = client.get_chat()
    await llm_base_menu(update, context)

async def llm_generate_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("history", None)
    client = LMStudioClient(chat_from_history=context.user_data["history"])
    await update.message.reply_text("⏳ thinking...")

    prompt = "Составь таблицу, удовлетворяющее следующим требованиям: \n" + update.message.text

    excel_bytes = client.respond_text_to_table(prompt)

    await update.message.reply_document(document=InputFile(excel_bytes, filename="answer.xlsx"))

    context.user_data["history"] = client.get_chat()

    await llm_base_menu(update, context)

async def llm_generate_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("history", None)
    client = LMStudioClient(chat_from_history=context.user_data["history"])
    await update.message.reply_text("⏳ thinking...")

    prompt = "Составь документ, удовлетворяющее следующим требованиям: \n" + update.message.text

    pdf_bytes = client.respond_text_to_pdf(prompt)

    await update.message.reply_document(document=InputFile(pdf_bytes, filename="answer.pdf"))

    context.user_data["history"] = client.get_chat()

    await llm_base_menu(update, context)