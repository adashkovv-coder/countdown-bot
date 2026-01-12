import telebot
from datetime import datetime, timedelta
import random
import time
import threading
import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler()  # Для Render важно использовать StreamHandler
    ]
)

# --- КОНФИГУРАЦИЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
# Получаем токен бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("❌ BOT_TOKEN не установлен! Установи в настройках Render")
    exit(1)

# Получаем ID пользователей
YOUR_CHAT_ID = os.environ.get('YOUR_CHAT_ID')
GIRLFRIEND_CHAT_ID = os.environ.get('GIRLFRIEND_CHAT_ID', '')

# Список получателей
TARGET_CHAT_IDS = []
if YOUR_CHAT_ID:
    TARGET_CHAT_IDS.append(YOUR_CHAT_ID)
    logging.info(f"✅ Твой ID добавлен: {YOUR_CHAT_ID}")
if GIRLFRIEND_CHAT_ID:
    TARGET_CHAT_IDS.append(GIRLFRIEND_CHAT_ID)
    logging.info(f"✅ ID девушки добавлен: {GIRLFRIEND_CHAT_ID}")

if not TARGET_CHAT_IDS:
    logging.warning("⚠️ Нет получателей! Установи YOUR_CHAT_ID")

# Целевая дата (1 июня 2028)
TARGET_DATE = datetime(2028, 6, 1, 0, 0, 0)

# --- ИНИЦИАЛИЗАЦИЯ БОТА ---
bot = telebot.TeleBot(BOT_TOKEN)

# --- КРАСИВЫЕ ШАБЛОНЫ СООБЩЕНИЙ ---
MESSAGE_TEMPLATES = [
    """✨ *ДО НАШЕГО ПЕРЕЕЗДА ОСТАЛОСЬ* ✨

📅 {days} дней
⏰ {hours} часов
⏳ {minutes} минут

🎯 Цель: {date}
💖 Каждый день — шаг к нашей мечте!""",

    """🏡 *Отсчет до нового дома* 🏡

⏳ Осталось: {days} дней, {hours} часов, {minutes} минут
📌 Дата переезда: {date}

✨ Скоро начнется новая глава нашей жизни!""",

    """❤️ *Наш отсчет* ❤️

До переезда ({date}) осталось:
📆 {days} дней
🕐 {hours} часов
⏱ {minutes} минут

💕 Мечты сбываются!"""
]

HEART_EMOJIS = ["💖", "❤️", "💕", "💗", "💓", "😍", "🥰", "💑"]

# --- ФУНКЦИИ БОТА ---

def get_countdown_message():
    """Создает красивое сообщение с отсчетом."""
    now = datetime.now()
    remaining = TARGET_DATE - now

    if remaining.total_seconds() <= 0:
        return "🎉🎊 *УРА! ПЕРЕЕЗД СОСТОЯЛСЯ!* 🎊🎉\n\nНаше счастливое будущее начинается сегодня! 🏡💕"

    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Выбираем случайный шаблон
    template = random.choice(MESSAGE_TEMPLATES)
    heart = random.choice(HEART_EMOJIS)
    
    message = template.format(
        days=days,
        hours=hours,
        minutes=minutes,
        date=TARGET_DATE.strftime("%d %B %Y")
    )
    
    return f"{heart} {message} {heart}"

def send_daily_countdown():
    """Отправляет ежедневное сообщение."""
    try:
        if not TARGET_CHAT_IDS:
            logging.warning("Пропускаю отправку: нет получателей")
            return

        message_text = get_countdown_message()
        logging.info(f"📤 Отправляю сообщение...")

        for chat_id in TARGET_CHAT_IDS:
            try:
                bot.send_message(chat_id, message_text, parse_mode="Markdown")
                logging.info(f"✅ Отправлено на {chat_id}")
            except Exception as e:
                logging.error(f"❌ Ошибка отправки на {chat_id}: {str(e)[:50]}...")

    except Exception as e:
        logging.error(f"❌ Ошибка при отправке: {e}")
    finally:
        # Планируем следующую отправку
        schedule_next_countdown()

def schedule_next_countdown():
    """Планирует следующее сообщение."""
    now = datetime.now()
    
    # Завтра в случайное время (8:00-22:00)
    tomorrow = now + timedelta(days=1)
    send_hour = random.randint(8, 22)
    send_minute = random.randint(0, 59)
    
    next_time = tomorrow.replace(hour=send_hour, minute=send_minute, second=0)
    delay = (next_time - now).total_seconds()
    
    logging.info(f"⏰ Следующая отправка: {next_time.strftime('%H:%M %d.%m')}")
    logging.info(f"⏳ Ожидание: {delay/3600:.1f} часов")
    
    # Таймер для следующей отправки
    timer = threading.Timer(delay, send_daily_countdown)
    timer.daemon = True
    timer.start()

# --- КОМАНДЫ БОТА ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome = """🤖 *Бот-отсчет до переезда* 🏡

Я буду напоминать вам каждый день, сколько осталось до вашего переезда!

✨ *Команды:*
/start - это сообщение
/countdown - сколько осталось прямо сейчас
/id - узнать свой ID для настройки
/status - статус бота
/next - когда следующее сообщение

💌 *Сообщения приходят каждый день в случайное время!*"""
    
    bot.reply_to(message, welcome, parse_mode="Markdown")
    logging.info(f"👋 Приветствие отправлено пользователю {message.chat.id}")

@bot.message_handler(commands=['countdown'])
def send_countdown(message):
    countdown_msg = get_countdown_message()
    bot.reply_to(message, countdown_msg, parse_mode="Markdown")
    logging.info(f"📊 Отправлен отсчет пользователю {message.chat.id}")

@bot.message_handler(commands=['id'])
def send_id(message):
    user_info = f"""📋 *Твой ID для настройки:*

`{message.chat.id}`

👤 *Имя:* {message.from_user.first_name or '-'}
📛 *Фамилия:* {message.from_user.last_name or '-'}
🏷 *Username:* @{message.from_user.username or 'нет'}

🔧 *Отправь этот ID для добавления в бота*"""
    
    bot.reply_to(message, user_info, parse_mode="Markdown")
    logging.info(f"🆔 ID запрошен пользователем {message.chat.id}")

@bot.message_handler(commands=['status'])
def send_status(message):
    # Проверяем, что это ты
    if str(message.chat.id) == YOUR_CHAT_ID:
        now = datetime.now()
        status_msg = f"""🔧 *Статус бота:*

✅ *Работает:* Да
🕐 *Серверное время:* {now.strftime('%H:%M:%S %d.%m.%Y')}
🎯 *Целевая дата:* {TARGET_DATE.strftime('%d %B %Y')}
👥 *Получатели:* {len(TARGET_CHAT_IDS)}
🚀 *Хостинг:* Render.com
📊 *Пинг:* Активен"""
        
        bot.reply_to(message, status_msg, parse_mode="Markdown")
        logging.info(f"📈 Статус отправлен тебе")

@bot.message_handler(commands=['next'])
def send_next_time(message):
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    hour = random.randint(8, 22)
    minute = random.randint(0, 59)
    
    next_time = tomorrow.replace(hour=hour, minute=minute)
    time_left = next_time - now
    
    hours_left = time_left.total_seconds() / 3600
    
    next_msg = f"""⏰ *Следующее сообщение:*

🕐 *Время:* {next_time.strftime('%H:%M %d.%m.%Y')}
⏳ *Через:* {hours_left:.1f} часов
📅 *Это будет:* завтра

💌 *Ждите напоминание!*"""
    
    bot.reply_to(message, next_msg, parse_mode="Markdown")

# --- ЗАПУСК БОТА ---
def start_bot():
    """Запускает бота."""
    logging.info("=" * 50)
    logging.info("🚀 ЗАПУСК БОТА ДЛЯ ОТСЧЕТА ПЕРЕЕЗДА")
    logging.info("=" * 50)
    logging.info(f"🎯 Целевая дата: {TARGET_DATE.strftime('%d.%m.%Y')}")
    logging.info(f"👤 Получателей: {len(TARGET_CHAT_IDS)}")
    
    # Запускаем планировщик
    schedule_next_countdown()
    
    logging.info("✅ Бот запущен и готов к работе!")
    logging.info("=" * 50)
    
    # Запускаем веб-сервер для Render
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return f"""
        <html>
            <head>
                <title>🤖 Бот-отсчет до переезда</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        min-height: 100vh;
                    }}
                    .container {{
                        background: rgba(255, 255, 255, 0.1);
                        backdrop-filter: blur(10px);
                        padding: 30px;
                        border-radius: 20px;
                        margin-top: 50px;
                    }}
                    h1 {{ color: #FFD700; }}
                    .status {{ 
                        background: rgba(0, 0, 0, 0.2); 
                        padding: 15px; 
                        border-radius: 10px;
                        margin: 15px 0;
                    }}
                    .emoji {{ font-size: 2em; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="emoji">🤖</h1>
                    <h1>Бот-отсчет до переезда</h1>
                    <div class="status">
                        <p><strong>🎯 Цель:</strong> {TARGET_DATE.strftime('%d %B %Y')}</p>
                        <p><strong>👥 Получателей:</strong> {len(TARGET_CHAT_IDS)}</p>
                        <p><strong>✅ Статус:</strong> Бот работает</p>
                        <p><strong>🚀 Хостинг:</strong> Render.com</p>
                    </div>
                    <p>Бот отправляет ежедневные напоминания о переезде!</p>
                    <p>💌 Напишите боту в Telegram команду /start</p>
                </div>
            </body>
        </html>
        """
    
    # Запускаем Flask в отдельном потоке
    def run_flask():
        app.run(host='0.0.0.0', port=10000, debug=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем бота
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=10)
    except Exception as e:
        logging.error(f"❌ Ошибка бота: {e}")
        time.sleep(10)
        start_bot()  # Перезапуск

if __name__ == '__main__':
    start_bot()