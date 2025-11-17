import io
import json

from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes, filters

from tgbot.callbacks.menus import *
from services.llm_service import LMStudioClient

import asyncio


async def llm_answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = context.application.bot_data["db"]

    cur_project_name = context.user_data.get("current_project", "")

    if cur_project_name == "":
        context.user_data.setdefault("history", None)
        client = LMStudioClient(chat_from_history=context.user_data["history"])
        sent = await update.message.reply_text("⏳ thinking...")

    cur_project = db.get_project_by_name(update.effective_user.id, context.user_data["current_project"])
    history = json.loads(cur_project[3])
    print(history)


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

    answer = None

    msg = update.message

    if msg.document:
        doc = msg.document
        file_obj = await doc.get_file()
        bio = io.BytesIO()
        await file_obj.download_to_memory(out=bio)
        bio.seek(0)

        if msg.document.mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            answer = client.respond_docx_document_to_text("Срезюмируй данный документ: ", bio)
        elif msg.document.mime_type == "application/pdf":
            answer = client.respond_pdf_document_to_text("Срезюмируй данный документ: ", bio)
        else:
            raise Exception
    elif msg.text:
        prompt = "Срезюмируй следующий текст: \n" + update.message.text
        answer = client.respond_text_to_text(prompt)

    await update.message.reply_text(answer)

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


async def llm_analyse_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("history", None)
    client = LMStudioClient(chat_from_history=context.user_data["history"])

    msg = update.message

    await update.message.reply_text("⏳ thinking...")
    doc = msg.document
    file_obj = await doc.get_file()
    bio = io.BytesIO()
    await file_obj.download_to_memory(out=bio)
    bio.seek(0)

    answer = None

    if msg.document.mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        answer = client.respond_docx_document_to_text("Проанализируй данный документ: ", bio)
    elif msg.document.mime_type == "application/pdf":
        answer = client.respond_pdf_document_to_text("Проанализируй данный документ: ", bio)
    else:
        raise Exception

    await update.message.reply_text(answer)

    context.user_data["history"] = client.get_chat()
    await llm_base_menu(update, context)


async def llm_analyse_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("history", None)
    client = LMStudioClient(chat_from_history=context.user_data["history"])

    msg = update.message

    await update.message.reply_text("⏳ thinking...")
    doc = msg.document
    file_obj = await doc.get_file()
    bio = io.BytesIO()
    await file_obj.download_to_memory(out=bio)
    bio.seek(0)

    if msg.document.mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        answer = client.respond_xlsx_table_to_text("Проанализируй данную таблицу: ", bio)
    else:
        raise Exception

    await update.message.reply_text(answer)
    context.user_data["history"] = client.get_chat()
    await llm_base_menu(update, context)


async def llm_analyse_presentation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("history", None)
    client = LMStudioClient(chat_from_history=context.user_data["history"])

    msg = update.message

    await update.message.reply_text("⏳ thinking...")
    doc = msg.document
    file_obj = await doc.get_file()
    bio = io.BytesIO()
    await file_obj.download_to_memory(out=bio)
    bio.seek(0)

    answer = None
    if msg.document.mime_type == "application/pdf":
        answer = client.respond_pdf_presentation_to_text("Проанализируй данную презентацию", bio)
    else:
        raise Exception

    await update.message.reply_text(answer)
    context.user_data["history"] = client.get_chat()
    await llm_base_menu(update, context)
