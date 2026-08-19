import json
import os
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8816183730:AAEtiaif9ixe1fZNyieLuZDw89Gk_jjv1Fo")
CURATORS_FILE = "curators_ids.json"

# ===== FLASK ДЛЯ RENDER =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

@app.route('/health')
def health():
    return "OK"

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ID =====
def load_curators():
    if os.path.exists(CURATORS_FILE):
        with open(CURATORS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_curator(user_id, username, full_name):
    curators = load_curators()
    curators[str(user_id)] = {
        "username": username,
        "full_name": full_name,
        "added_at": datetime.now().strftime('%d.%m.%Y %H:%M')
    }
    with open(CURATORS_FILE, 'w', encoding='utf-8') as f:
        json.dump(curators, f, ensure_ascii=False, indent=2)
    return curators

# ===== ОБРАБОТЧИКИ БОТА =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    curators = load_curators()
    if str(user.id) in curators:
        await update.message.reply_text(
            f"✦ С возвращением, {user.first_name}! ✦\n\n"
            f"Ты уже зарегистрирован в системе.\n\n"
            f"Бот будет присылать уведомления о назначении мастера.\n\n"
            f"📍 По вопросам: @dzufear | @Pashtetboss",
            parse_mode='Markdown'
        )
        return
    
    keyboard = [[InlineKeyboardButton("✅ Начать регистрацию", callback_data="register")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✦ Привет, на связи Vanta Bikes ✦\n\n"
        f"Нажми на кнопку ниже, чтобы зарегистрироваться в системе.\n"
        f"Это нужно для получения уведомлений о ремонте твоих велосипедов.",
        reply_markup=reply_markup
    )

async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    save_curator(user.id, user.username or "Не указан", user.full_name or "Не указан")
    
    await query.edit_message_text(
        f"✦ Привет, на связи Vanta Bikes ✦\n\n"
        f"✅ Ты успешно зарегистрирован!\n\n"
        f"Этот бот будет держать тебя в курсе всего, что касается ремонта твоих велосипедов.\n\n"
        f"📌 Что ты здесь получишь:\n"
        f"▸ уведомления, когда к тебе назначат мастера — больше не нужно перепроверять вручную;\n"
        f"▸ анонимные опросы о качестве сервиса — говори как есть, это никуда не уйдёт;\n"
        f"▸ новые функции, которые мы будем добавлять.\n\n"
        f"🛠 По всем заявкам на ремонт работаем через сайт:\n"
        f"https://vantabikes.com/form-vv\n\n"
        f"Там же можно посмотреть статус текущих заявок и список велосипедов в твоём парке.\n\n"
        f"📍 Если вопрос срочный или нестандартный — пиши в личку:\n"
        f"@dzufear | @Pashtetboss\n\n"
        f"Бот только начинает работу, так что в ближайшее время здесь появится ещё больше полезного.\n\n"
        f"Оставайся на связи ✦",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    curators = load_curators()
    if str(user.id) in curators:
        await update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n\n"
            f"Ты уже зарегистрирован. Уведомления будут приходить автоматически.\n\n"
            f"📍 По вопросам: @dzufear | @Pashtetboss"
        )
    else:
        await update.message.reply_text(
            f"✦ Привет, на связи Vanta Bikes ✦\n\n"
            f"Похоже, ты ещё не зарегистрирован.\n"
            f"Напиши /start, чтобы начать."
        )

async def show_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🆔 Ваш ID: `{user.id}`\n\n"
        f"Сохраните его для связи с поддержкой.",
        parse_mode='Markdown'
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = 7367165004  # ЗАМЕНИТЕ НА СВОЙ ID!
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет прав на эту команду.")
        return
    curators = load_curators()
    count = len(curators)
    message = f"📊 Статистика бота:\n\n👥 Всего кураторов: {count}\n\n"
    if count > 0:
        message += "📋 Последние зарегистрированные:\n"
        for i, (user_id, data) in enumerate(list(curators.items())[-10:], 1):
            message += f"{i}. {data.get('full_name', 'Без имени')} (@{data.get('username', 'нет')}) — {data.get('added_at', '')}\n"
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📖 Доступные команды:\n\n"
        f"/start — начать регистрацию\n"
        f"/myid — показать мой ID\n"
        f"/help — показать эту справку\n"
        f"/stats — статистика (только для администратора)\n\n"
        f"📍 По вопросам: @dzufear | @Pashtetboss"
    )

# ===== ФУНКЦИЯ ЗАПУСКА БОТА В ПОТОКЕ =====

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", show_my_id))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(register_callback, pattern="register"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

# ===== ЗАПУСК =====

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем Flask для Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
