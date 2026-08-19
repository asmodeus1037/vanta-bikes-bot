import os
import json
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

# ===== ОБРАБОТЧИКИ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    curators = load_curators()
    if str(user.id) in curators:
        await update.message.reply_text(
            f"✦ С возвращением, {user.first_name}! ✦\n\n"
            f"Ты уже зарегистрирован в системе.\n\n"
            f"📍 По вопросам: @dzufear | @Pashtetboss",
            parse_mode='Markdown'
        )
        return
    keyboard = [[InlineKeyboardButton("✅ Начать регистрацию", callback_data="register")]]
    await update.message.reply_text(
        f"✦ Привет, на связи Vanta Bikes ✦\n\n"
        f"Нажми на кнопку ниже, чтобы зарегистрироваться в системе.\n"
        f"Это нужно для получения уведомлений.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    save_curator(user.id, user.username or "Не указан", user.full_name or "Не указан")
    await query.edit_message_text(
        f"✦ Привет, на связи Vanta Bikes ✦\n\n"
        f"✅ Ты успешно зарегистрирован!\n\n"
        f"📍 По вопросам: @dzufear | @Pashtetboss",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    curators = load_curators()
    if str(user.id) in curators:
        await update.message.reply_text(f"👋 Привет, {user.first_name}! Ты зарегистрирован.")
    else:
        await update.message.reply_text("Напиши /start для регистрации.")

async def show_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Ваш ID: `{update.effective_user.id}`", parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📖 Доступные команды:\n"
        f"/start — регистрация\n"
        f"/myid — показать ID\n"
        f"/help — справка\n\n"
        f"📍 По вопросам: @dzufear | @Pashtetboss"
    )

# ===== ОТДЕЛЬНЫЙ ЗАПУСК БОТА (БЕЗ FLASK) =====
def run_bot():
    """Запускает бота в отдельном процессе без signal handlers"""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", show_my_id))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(register_callback, pattern="register"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен и работает")
    application.run_polling()

# ===== ЗАПУСК =====
if __name__ == "__main__":
    import multiprocessing
    import sys
    
    # Запускаем бота в отдельном процессе (а не потоке)
    bot_process = multiprocessing.Process(target=run_bot)
    bot_process.start()
    
    # Запускаем Flask в основном процессе
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
