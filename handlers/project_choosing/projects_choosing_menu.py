from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# меню выбора проекта
async def projects_choosing_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = context.user_data.get("projects", [])
    if not projects:
        keyboard = [[p] for p in projects] + [["Создать новый проект"]] + [["Назад"]]
    else:
        keyboard = [[p] for p in projects]  + [["Создать новый проект"]] + [["Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выбери действие", reply_markup=reply_markup)
    context.user_data["menu"] = "projects_choosing_menu"
    context.user_data["section"] = "projects_choosing_section"

# выбор конкретного проекта
async def project_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project_name = update.message.text
    if project_name in context.user_data.get("projects", []):
        await update.message.reply_text(f"Выбран проект: {project_name}")
        context.user_data["current_project"] = project_name
        # Здесь можно показать меню действий для проекта
    else:
        await update.message.reply_text("Проект не найден.")

# создание нового проекта
async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши имя нового проекта:")
    context.user_data["menu"] = "creating_project"

async def save_new_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    projects = context.user_data.setdefault("projects", [])
    if name in projects:
        await update.message.reply_text("Проект с таким именем уже существует.")
    else:
        projects.append(name)
        await update.message.reply_text(f"Проект '{name}' создан!")

    context.user_data["menu"] = "projects_choosing_menu"
    context.user_data["section"] = "projects_choosing_section"

    await projects_choosing_menu(update, context)