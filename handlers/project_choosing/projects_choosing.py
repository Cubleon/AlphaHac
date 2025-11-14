from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CallbackContext, CommandHandler, MessageHandler, ContextTypes,  filters
import handlers.project.project_menu as project_section



# меню выбора проекта
async def projects_choosing_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = context.user_data.get("projects", [])
    if not projects:
        keyboard = [[p] for p in projects] + [["Создать новый проект", "Удалить проект"]] + [["Назад"]]
    else:
        keyboard = [[p] for p in projects]  + [["Создать новый проект", "Удалить проект"]] + [["Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выбери действие", reply_markup=reply_markup)
    context.user_data["button"] = "projects_choosing_button"
    context.user_data["section"] = "projects_choosing_section"

# выбор конкретного проекта
async def project_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project_name = update.message.text
    if project_name in context.user_data.get("projects", []):
        await update.message.reply_text(f"Выбран проект: {project_name}")
        context.user_data["current_project"] = project_name
        context.user_data["button"] = "projects_choosing_button"
        await project_section.project_handler(update, context)
    else:
        await update.message.reply_text("Проект не найден.")

# создание нового проекта

async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши имя нового проекта:")
    context.user_data["button"] = "creating_project"

async def save_new_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    projects = context.user_data.setdefault("projects", [])
    if name in projects:
        await update.message.reply_text("Проект с таким именем уже существует.")
    else:
        projects.append(name)
        buttons[name] = project_chosen
        await update.message.reply_text(f"Проект '{name}' создан!")

    context.user_data["button"] = "projects_choosing_button"
    context.user_data["section"] = "projects_choosing_section"

    await projects_choosing_button(update, context)

async def delete_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = context.user_data.get("projects", [])
    if not projects:
        keyboard = [[p] for p in projects] + [["Назад"]]
    else:
        keyboard = [[p] for p in projects] + [["Назад"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выбери проект, который хочешь удалить", reply_markup=reply_markup)
    context.user_data["button"] = "delete_project"

# Функция удаления проекта
async def delete_project_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project_name = update.message.text
    projects = context.user_data.get("projects", [])

    if project_name in projects:
        projects.remove(project_name)
        buttons.pop(project_name)
        await update.message.reply_text(f"Проект '{project_name}' удалён!")
    else:
        await update.message.reply_text(f"Проект '{project_name}' не найден.")

    await projects_choosing_button(update, context)


buttons = {
    "Мои проекты": projects_choosing_button,
    "Создать новый проект": create_project,
    "Удалить проект": delete_project
}

async def project_choosing_handler(update: Update, context: CallbackContext):
    button_name = update.message.text
    prev_button = context.user_data.get("button")

    # Если мы создаем новый проект
    if prev_button == "creating_project":
        await save_new_project(update, context)
    elif prev_button == "delete_project":
        await delete_project_confirm(update, context)
    elif buttons.get(button_name):
        await buttons[button_name](update, context)
    else:
        await update.message.reply_text("Такой команды не существует")
