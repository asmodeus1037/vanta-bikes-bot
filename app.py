import os
import json
import re
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CURATORS_FILE = "curators_ids.json"

# ===== FLASK =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

@app.route('/health')
def health():
    return "OK"

# ===== ФУНКЦИИ =====
def load_curators():
    if os.path.exists(CURATORS_FILE):
        with open(CURATORS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_curator(user_id, username, full_name, darkstore):
    curators = load_curators()
    curators[str(user_id)] = {
        "username": username,
        "full_name": full_name,
        "darkstore": darkstore,
        "registered_at": datetime.now().strftime('%d.%m.%Y %H:%M')
    }
    with open(CURATORS_FILE, 'w', encoding='utf-8') as f:
        json.dump(curators, f, ensure_ascii=False, indent=2)
    return curators

def is_registered(user_id):
    curators = load_curators()
    return str(user_id) in curators

def get_curator(user_id):
    curators = load_curators()
    return curators.get(str(user_id))

# ===== ОБРАБОТЧИКИ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — начало регистрации"""
    user = update.effective_user
    user_id = user.id
    
    # Если уже зарегистрирован — показываем меню
    if is_registered(user_id):
        await show_main_menu(update, context)
        return
    
    # Если регистрация уже начата (ждём ввод номера)
    if context.user_data.get("waiting_for_darkstore"):
        await update.message.reply_text(
            "📦 Введи номер своего даркстора (4 цифры).\n"
            "Пример: `1234`",
            parse_mode='Markdown'
        )
        return
    
    # Начинаем регистрацию
    context.user_data["waiting_for_darkstore"] = True
    
    await update.message.reply_text(
        "✦ Привет, на связи Vanta Bikes ✦\n\n"
        "Я бот для кураторов. Чтобы начать работу, нужно зарегистрироваться.\n\n"
        "📦 **Введи номер своего даркстора** — это 4 цифры.\n"
        "Пример: `1234`\n\n"
        "_Никакой другой текст не принимается._",
        parse_mode='Markdown'
    )

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод номера даркстора"""
    user = update.effective_user
    text = update.message.text.strip()
    
    # Проверяем, что это ровно 4 цифры
    if not re.match(r'^\d{4}$', text):
        await update.message.reply_text(
            "❌ Неверный формат!\n\n"
            "Номер даркстора — это **ровно 4 цифры**.\n"
            "Пример: `1234`\n\n"
            "Попробуй ещё раз:",
            parse_mode='Markdown'
        )
        return
    
    # Сохраняем номер
    darkstore = text
    username = user.username or "Не указан"
    full_name = user.full_name or "Не указан"
    
    save_curator(user.id, username, full_name, darkstore)
    context.user_data["waiting_for_darkstore"] = False
    
    # Отправляем приветствие с инструкцией
    await update.message.reply_text(
        f"✦ Привет, на связи Vanta Bikes ✦\n\n"
        f"✅ Ты успешно зарегистрирован!\n"
        f"📦 Твой даркстор: `{darkstore}`\n\n"
        f"📌 **Что ты здесь получишь:**\n"
        f"▸ уведомления, когда к тебе назначат мастера;\n"
        f"▸ анонимные опросы о качестве сервиса;\n"
        f"▸ новые функции, которые мы будем добавлять.\n\n"
        f"🛠 **Заявки на ремонт** — только через сайт:\n"
        f"https://vantabikes.com/form-vv\n\n"
        f"Там же можно посмотреть статус заявок и список твоего парка.\n\n"
        f"📍 **По срочным вопросам:**\n"
        f"@dzufear | @Pashtetboss\n\n"
        f"⚠️ **Важное правило:**\n"
        f"Аккумуляторы Vanta Bikes запрещено использовать на других велосипедах.\n"
        f"Нарушение = отказ в гарантии.\n\n"
        f"Бот только начинает работу, так что в ближайшее время здесь появится ещё больше полезного.\n\n"
        f"Оставайся на связи ✦",
        parse_mode='Markdown'
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню для зарегистрированных пользователей"""
    user = update.effective_user
    curator = get_curator(user.id)
    darkstore = curator.get("darkstore", "не указан") if curator else "не указан"
    
    await update.message.reply_text(
        f"✦ С возвращением, {user.first_name}! ✦\n\n"
        f"📦 Твой даркстор: `{darkstore}`\n\n"
        f"📌 **Доступные команды:**\n"
        f"/start — главное меню\n"
        f"/myid — показать мой ID\n"
        f"/help — справка\n"
        f"/info — памятка куратора\n\n"
        f"📍 По вопросам: @dzufear | @Pashtetboss",
        parse_mode='Markdown'
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /info — показывает памятку куратора"""
    user = update.effective_user
    
    if not is_registered(user.id):
        await update.message.reply_text("Сначала зарегистрируйся: /start")
        return
    
    await update.message.reply_text(
        f"📋 **ПАМЯТКА КУРАТОРА**\n\n"
        f"📍 **Связь с нами**\n"
        f"Срочные вопросы → @dzufear | @Pashtetboss\n\n"
        f"🤖 **Телеграм-бот**\n"
        f"Уведомления о мастере, опросы, новые функции.\n\n"
        f"🛠 **Заявки на ремонт**\n"
        f"Только через сайт: https://vantabikes.com/form-vv\n"
        f"Там же: статус заявок и список твоего парка.\n\n"
        f"✅ **Как заполнять заявку**\n"
        f"❌ «Велосипед сломался»\n"
        f"✅ «Замена покрышки, колодок»\n"
        f"Чётко = быстро.\n\n"
        f"⚠️ **Важное правило**\n"
        f"АКБ Vanta Bikes — только на наших велосипедах.\n"
        f"Нарушение = отказ в гарантии.\n\n"
        f"📌 **Коротко**\n"
        f"1. Статус заявок и парк — на сайте.\n"
        f"2. Нестандартное — в личку.\n"
        f"3. АКБ — только на наших великах.",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений"""
    user = update.effective_user
    user_id = user.id
    
    # Если пользователь в процессе регистрации
    if context.user_data.get("waiting_for_darkstore"):
        await handle_registration(update, context)
        return
    
    # Если зарегистрирован — просто отвечаем
    if is_registered(user_id):
        await update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n\n"
            f"Ты уже зарегистрирован.\n"
            f"Команды: /start — меню, /info — памятка, /help — справка"
        )
    else:
        await update.message.reply_text(
            "✦ Привет, на связи Vanta Bikes ✦\n\n"
            "Ты ещё не зарегистрирован.\n"
            "Напиши /start, чтобы начать."
        )

async def show_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /myid — показывает ID пользователя"""
    user = update.effective_user
    await update.message.reply_text(
        f"🆔 Твой ID: `{user.id}`\n\n"
        f"Сохрани его для связи с поддержкой.",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help — справка"""
    user = update.effective_user
    
    if not is_registered(user.id):
        await update.message.reply_text("Сначала зарегистрируйся: /start")
        return
    
    await update.message.reply_text(
        f"📖 **Доступные команды:**\n\n"
        f"/start — главное меню\n"
        f"/info — памятка куратора\n"
        f"/myid — показать мой ID\n"
        f"/help — эта справка\n\n"
        f"📍 По вопросам: @dzufear | @Pashtetboss",
        parse_mode='Markdown'
    )

# ===== ЗАПУСК БОТА =====

def run_bot():
    import multiprocessing
    import asyncio
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", show_my_id))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен и работает")
    application.run_polling()

# ===== ЗАПУСК =====

if __name__ == "__main__":
    import multiprocessing
    
    # Запускаем бота в отдельном процессе
    bot_process = multiprocessing.Process(target=run_bot)
    bot_process.start()
    
    # Запускаем Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
