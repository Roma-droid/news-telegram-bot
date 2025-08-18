import telebot
import requests
import json

# Настройки
BOT_TOKEN = '8164909440:AAHemeo02iKSmQaTev7Q7k_W8tEeMJ7IrxE'  # Замените на токен от @BotFather
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"  # URL LM Studio API
HEADERS = {"Content-Type": "application/json"}

# Создаем экземпляр бота
bot = telebot.TeleBot(BOT_TOKEN)

def generate_news_with_ai(topic="новость"):
    """Генерирует новость с помощью LM Studio API по заданной теме"""
    # Создаем уникальные промпты для разных тем
    prompts = {
        "новость": (
            "Напиши реальную новость на актуальную тему. "
            "Используй достоверные факты и нейтральный стиль изложения. "
            "Формат: краткий заголовок, затем 2-3 абзаца содержания."
        ),
        "глобальное потепление": (
            "Напиши новость о последних исследованиях в области глобального потепления. "
            "Включи реальные научные данные, последние события и прогнозы ученых. "
            "Особое внимание удели последствиям для экосистем и человечества. "
            "Формат: краткий заголовок, затем 2-3 абзаца содержания."
        ),
        "наводнение": (
            "Напиши новость о серьезном наводнении в каком-либо регионе мира. "
            "Укажи реальное место, причины наводнения (ливни, таяние ледников, ураган и т.д.), "
            "количество пострадавших, масштабы разрушений и действия спасательных служб. "
            "Добавь информацию о последствиях и мерах по предотвращению будущих катастроф. "
            "Формат: краткий заголовок, затем 2-3 абзаца содержания."
        )
    }
    
    prompt = prompts.get(topic, prompts["новость"])
    
    data = {
        "messages": [
            {"role": "system", "content": "Ты профессиональный журналист, специализирующийся на природных катастрофах и климате."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 650,
        "stop": ["<|im_end|>"]
    }
    
    try:
        response = requests.post(LM_STUDIO_URL, headers=HEADERS, data=json.dumps(data))
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Ошибка генерации новости: {e}")
        return None

# Обработчик команд
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🌍 Привет! Я новостной бот с искусственным интеллектом.\n\n"
        "Доступные команды:\n"
        "/news - Случайная актуальная новость\n"
        "/global_warming - Новости о глобальном потеплении\n"
        "/flood - Новости о наводнениях и паводках\n\n"
        "Все новости генерируются нейросетью в реальном времени!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['news'])
def send_news(message):
    """Отправка случайной новости"""
    msg = bot.send_message(message.chat.id, "📡 Запрашиваю последние новости...")
    news_text = generate_news_with_ai()
    
    if news_text:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=f"📰 **Свежий выпуск**\n\n{news_text}",
            parse_mode='Markdown'
        )
    else:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text="⚠️ Не удалось получить новости. Попробуйте позже."
        )

@bot.message_handler(commands=['global_warming'])
def send_climate_news(message):
    """Отправка новости о глобальном потеплении"""
    msg = bot.send_message(message.chat.id, "🌡️ Анализирую климатические данные...")
    news_text = generate_news_with_ai("глобальное потепление")
    
    if news_text:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=f"🔥 **Климатический отчет**\n\n{news_text}",
            parse_mode='Markdown'
        )
    else:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text="⚠️ Не удалось получить климатические данные. Попробуйте позже."
        )

@bot.message_handler(commands=['flood'])
def send_flood_news(message):
    """Отправка новости о наводнении"""
    msg = bot.send_message(message.chat.id, "🌧️ Анализирую гидрологическую обстановку...")
    news_text = generate_news_with_ai("наводнение")
    
    if news_text:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=f"🌊 **Экстренные новости: Наводнение**\n\n{news_text}",
            parse_mode='Markdown'
        )
    else:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text="⚠️ Не удалось получить информацию о наводнениях. Попробуйте позже."
        )

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()