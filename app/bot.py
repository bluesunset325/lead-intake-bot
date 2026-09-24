import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from app.state import (
    get_user_session, clear_user_session, update_user_state, 
    check_rate_limit, UserState, LeadData
)
from app.config import (
    load_client_config, get_welcome_text, get_thank_you_text,
    get_budget_choices, get_urgency_choices
)
from app.validators import validate_phone, validate_name, validate_text
from app.sheets import append_lead_to_sheet


BUTTON_LEAVE_REQUEST = "Оставить заявку"
BUTTON_ASK_QUESTION = "Задать вопрос"
BUTTON_SKIP = "Пропустить"
BUTTON_CONFIRM_YES = "Да, отправить"
BUTTON_CONFIRM_NO = "Нет, начать заново"


def get_manager_chat_id(config: dict) -> str:
    return config.get("manager_chat_id") or os.getenv("MANAGER_CHAT_ID", "")


def is_admin(chat_id: int) -> bool:
    admin_ids_str = os.getenv("ADMIN_CHAT_IDS", "")
    if not admin_ids_str:
        return False
    admin_ids = [int(x.strip()) for x in admin_ids_str.split(",")]
    return chat_id in admin_ids


def build_summary_text(lead: LeadData) -> str:
    comment_display = lead.comment if lead.comment else "Не указан"
    return (
        "Проверьте данные заявки:\n\n"
        f"👤 Имя: {lead.name}\n"
        f"📱 Телефон: {lead.phone}\n"
        f"📍 Город: {lead.city}\n"
        f"💰 Бюджет: {lead.budget}\n"
        f"⏰ Срочность: {lead.urgency}\n"
        f"📋 Что нужно: {lead.what_needed}\n"
        f"💬 Комментарий: {comment_display}\n\n"
        "Всё верно?"
    )


def build_manager_message(lead: LeadData, config: dict, username: str = "") -> str:
    comment_display = lead.comment if lead.comment else "Не указан"
    user_link = f"https://t.me/{username}" if username else f"ID: {lead.chat_id}"
    
    return (
        "🆕 Новая заявка!\n\n"
        f"Клиент: {lead.client_name} ({lead.client_key})\n\n"
        f"👤 Имя: {lead.name}\n"
        f"📱 Телефон: {lead.phone}\n"
        f"📍 Город: {lead.city}\n"
        f"💰 Бюджет: {lead.budget}\n"
        f"⏰ Срочность: {lead.urgency}\n"
        f"📋 Что нужно: {lead.what_needed}\n"
        f"💬 Комментарий: {comment_display}\n\n"
        f"Связь: {user_link}\n"
        f"Chat ID: {lead.chat_id}"
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    allowed, message = check_rate_limit(chat_id)
    if not allowed:
        if message:
            await update.message.reply_text(message)
        return
    
    # client_key приходит из t.me/bot?start=<client_key>
    args = context.args
    client_key = args[0] if args else "default"
    
    config = load_client_config(client_key)
    
    session = get_user_session(chat_id)
    session.lead_data.client_key = client_key
    session.lead_data.client_name = config.get("client_name", "Без названия")
    session.state = UserState.IDLE
    
    welcome_text = get_welcome_text(config)
    
    keyboard = [
        [BUTTON_LEAVE_REQUEST, BUTTON_ASK_QUESTION]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    allowed, message = check_rate_limit(chat_id)
    if not allowed:
        if message:
            await update.message.reply_text(message)
        return
    
    clear_user_session(chat_id)
    
    keyboard = [["/start"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Состояние сброшено. Вы можете начать заново с команды /start",
        reply_markup=reply_markup
    )


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not is_admin(chat_id):
        # молча, чтобы не палить, что команда есть
        return
    
    await update.message.reply_text("ok")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    allowed, message = check_rate_limit(chat_id)
    if not allowed:
        if message:
            await update.message.reply_text(message)
        return
    
    session = get_user_session(chat_id)
    config = load_client_config(session.lead_data.client_key)
    
    if text == BUTTON_LEAVE_REQUEST:
        await start_request_flow(update, context, session, config)
        return
    
    if text == BUTTON_ASK_QUESTION:
        await start_question_flow(update, context, session, config)
        return
    
    if session.state == UserState.AWAITING_NAME:
        await process_name(update, context, session, text)
    elif session.state == UserState.AWAITING_PHONE:
        await process_phone(update, context, session, text, config)
    elif session.state == UserState.AWAITING_CITY:
        await process_city(update, context, session, text)
    elif session.state == UserState.AWAITING_WHAT_NEEDED:
        await process_what_needed(update, context, session, text)
    elif session.state == UserState.AWAITING_COMMENT:
        await process_comment(update, context, session, text, config)
    elif session.state == UserState.QUESTION:
        await process_question(update, context, session, text, config)
    elif session.state == UserState.CONFIRM:
        await process_confirmation(update, context, session, text, config)
    else:
        await update.message.reply_text(
            "Используйте /start чтобы начать или выберите действие из меню."
        )


async def start_request_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, session, config):
    update_user_state(update.effective_chat.id, UserState.AWAITING_NAME)
    await update.message.reply_text(
        "Отлично! Давайте заполним заявку.\n\nВведите ваше имя:",
        reply_markup=ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)
    )


async def process_name(update: Update, context: ContextTypes.DEFAULT_TYPE, session, text: str):
    is_valid, error = validate_name(text)
    if not is_valid:
        await update.message.reply_text(error)
        return
    
    session.lead_data.name = text.strip()
    update_user_state(update.effective_chat.id, UserState.AWAITING_PHONE)
    
    await update.message.reply_text(
        "Введите ваш номер телефона:\n"
        "(например: +79991234567 или 89991234567)"
    )


async def process_phone(update: Update, context: ContextTypes.DEFAULT_TYPE, session, text: str, config):
    is_valid, normalized, error = validate_phone(text)
    if not is_valid:
        await update.message.reply_text(error)
        return
    
    session.lead_data.phone = normalized
    update_user_state(update.effective_chat.id, UserState.AWAITING_CITY)
    
    await update.message.reply_text("Укажите ваш город:")


async def process_city(update: Update, context: ContextTypes.DEFAULT_TYPE, session, text: str):
    is_valid, error = validate_text(text, "город")
    if not is_valid:
        await update.message.reply_text(error)
        return
    
    session.lead_data.city = text.strip()
    update_user_state(update.effective_chat.id, UserState.AWAITING_WHAT_NEEDED)
    
    await update.message.reply_text("Опишите, что вам нужно:")


async def process_what_needed(update: Update, context: ContextTypes.DEFAULT_TYPE, session, text: str):
    is_valid, error = validate_text(text, "описание")
    if not is_valid:
        await update.message.reply_text(error)
        return
    
    session.lead_data.what_needed = text.strip()
    
    budget_choices = get_budget_choices(load_client_config(session.lead_data.client_key))
    keyboard = [[InlineKeyboardButton(choice, callback_data=f"budget:{choice}")] for choice in budget_choices]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update_user_state(update.effective_chat.id, UserState.AWAITING_BUDGET)
    
    await update.message.reply_text(
        "Какой у вас бюджет?",
        reply_markup=reply_markup
    )


async def process_budget_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    session = get_user_session(chat_id)
    
    budget = query.data.replace("budget:", "")
    session.lead_data.budget = budget
    
    update_user_state(chat_id, UserState.AWAITING_URGENCY)
    
    urgency_choices = get_urgency_choices(load_client_config(session.lead_data.client_key))
    keyboard = [[InlineKeyboardButton(choice, callback_data=f"urgency:{choice}")] for choice in urgency_choices]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"Бюджет: {budget}\n\nКогда вам нужно начать?",
        reply_markup=reply_markup
    )


async def process_urgency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    session = get_user_session(chat_id)
    
    urgency = query.data.replace("urgency:", "")
    session.lead_data.urgency = urgency
    
    update_user_state(chat_id, UserState.AWAITING_COMMENT)
    
    keyboard = [[BUTTON_SKIP]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Срочность: {urgency}\n\nХотите добавить комментарий? (или нажмите 'Пропустить')",
        reply_markup=reply_markup
    )


async def process_comment(update: Update, context: ContextTypes.DEFAULT_TYPE, session, text: str, config):
    if text == BUTTON_SKIP:
        session.lead_data.comment = ""
    else:
        session.lead_data.comment = text.strip()
    
    summary = build_summary_text(session.lead_data)
    
    keyboard = [[BUTTON_CONFIRM_YES, BUTTON_CONFIRM_NO]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    update_user_state(update.effective_chat.id, UserState.CONFIRM)
    
    await update.message.reply_text(summary, reply_markup=reply_markup)


async def process_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, session, text: str, config):
    if text == BUTTON_CONFIRM_YES:
        session.lead_data.username = update.effective_user.username or ""
        session.lead_data.chat_id = update.effective_chat.id
        
        success = append_lead_to_sheet(
            timestamp_iso=datetime.now().isoformat(),
            client_key=session.lead_data.client_key,
            client_name=session.lead_data.client_name,
            name=session.lead_data.name,
            phone=session.lead_data.phone,
            city=session.lead_data.city,
            budget=session.lead_data.budget,
            urgency=session.lead_data.urgency,
            what_needed=session.lead_data.what_needed,
            comment=session.lead_data.comment,
            username=session.lead_data.username,
            chat_id=session.lead_data.chat_id
        )
        
        manager_chat_id = get_manager_chat_id(config)
        if manager_chat_id:
            try:
                manager_message = build_manager_message(
                    session.lead_data, 
                    config,
                    session.lead_data.username
                )
                await context.bot.send_message(
                    chat_id=int(manager_chat_id),
                    text=manager_message
                )
            except Exception as e:
                # Не ломаем работу если не удалось отправить менеджеру
                print(f"Ошибка отправки менеджеру: {e}")
        
        thank_you_text = get_thank_you_text(config)
        keyboard = [[BUTTON_LEAVE_REQUEST, BUTTON_ASK_QUESTION]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        clear_user_session(update.effective_chat.id)
        
        await update.message.reply_text(thank_you_text, reply_markup=reply_markup)
        
    elif text == BUTTON_CONFIRM_NO:
        clear_user_session(update.effective_chat.id)
        keyboard = [[BUTTON_LEAVE_REQUEST, BUTTON_ASK_QUESTION]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "Заявка отменена. Вы можете начать заново.",
            reply_markup=reply_markup
        )


async def start_question_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, session, config):
    update_user_state(update.effective_chat.id, UserState.QUESTION)
    await update.message.reply_text(
        "Напишите ваш вопрос, и менеджер ответит вам.\n\nВведите вопрос:"
    )


async def process_question(update: Update, context: ContextTypes.DEFAULT_TYPE, session, text: str, config):
    manager_chat_id = get_manager_chat_id(config)
    username = update.effective_user.username or ""
    
    client_name = session.lead_data.client_name
    user_link = f"@{username}" if username else f"ID: {update.effective_chat.id}"
    
    manager_message = (
        "❓ Новый вопрос от клиента!\n\n"
        f"Клиент: {client_name} ({session.lead_data.client_key})\n"
        f"Пользователь: {user_link}\n"
        f"Chat ID: {update.effective_chat.id}\n\n"
        f"Вопрос:\n{text}"
    )
    
    if manager_chat_id:
        try:
            await context.bot.send_message(
                chat_id=int(manager_chat_id),
                text=manager_message
            )
        except Exception as e:
            print(f"Ошибка отправки вопроса менеджеру: {e}")
    
    clear_user_session(update.effective_chat.id)
    keyboard = [[BUTTON_LEAVE_REQUEST, BUTTON_ASK_QUESTION]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Принято! Менеджер получил ваш вопрос и ответит вам в ближайшее время.",
        reply_markup=reply_markup
    )


def create_application() -> Application:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("ping", ping_command))
    
    application.add_handler(CallbackQueryHandler(process_budget_callback, pattern="^budget:"))
    application.add_handler(CallbackQueryHandler(process_urgency_callback, pattern="^urgency:"))
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_message
    ))
    
    return application
