import telebot
import requests
import json
import pycountry
import sqlite3
import time

# Настройки
BOT_TOKEN = 'YOURTOKEN'  # Замените на токен от @BotFather
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"  # URL LM Studio API
HEADERS = {"Content-Type": "application/json"}
NOMINATIM_API = "https://nominatim.openstreetmap.org/reverse"  # API для определения страны
DATABASE_NAME = "news_bot_users.db"

# Создаем экземпляр бота
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация базы данных
def init_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            country TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_user_country(chat_id):
    """Получает страну пользователя из базы данных"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT country FROM users WHERE chat_id = ?", (chat_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Ошибка при получении страны пользователя: {e}")
        return None
    finally:
        conn.close()

def set_user_country(chat_id, country):
    """Устанавливает страну пользователя в базе данных"""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (chat_id, country) 
            VALUES (?, ?)
        ''', (chat_id, country))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при сохранении страны пользователя: {e}")
        return False
    finally:
        conn.close()

def get_country_name(lat, lon):
    """Определяет страну по координатам с помощью Nominatim API"""
    try:
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
            'accept-language': 'en'
        }
        
        headers = {
            'User-Agent': 'TelegramNewsBot/1.0'
        }
        
        # Добавляем задержку для соблюдения политики использования
        time.sleep(1)
        
        response = requests.get(NOMINATIM_API, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('address'):
            country = data['address'].get('country')
            country_code = data['address'].get('country_code', '').upper()
            
            # Если есть код страны, пытаемся получить официальное название
            if country_code and len(country_code) == 2:
                try:
                    country_obj = pycountry.countries.get(alpha_2=country_code)
                    return country_obj.name
                except:
                    pass
            
            # Если не получилось через код, возвращаем название из ответа
            if country:
                return country
    except Exception as e:
        print(f"Ошибка определения страны: {e}")
    return None

def generate_news_with_ai(topic="новость", country=None):
    """Генерирует новость с помощью LM Studio API"""
    prompts = {
        "новость": (
            "Напиши реальную новость на актуальную тему. "
            "{country_context} "
            "Формат: Заголовок\n\nАбзац 1\n\nАбзац 2\n\nАбзац 3"
        ),
        "глобальное потепление": (
            "Напиши новость о глобальном потеплении. "
            "{country_context} "
            "Используй последние научные данные. "
            "Формат: Заголовок\n\nАбзац 1\n\nАбзац 2"
        ),
        "наводнение": (
            "Напиши новость о наводнении {country_article}. "
            "Укажи место, причины, последствия. "
            "Формат: Заголовок\n\nАбзац 1\n\nАбзац 2"
        )
    }
    
    country_context = f"Сфокусируйся на {country}. " if country else ""
    country_article = f"в {country}" if country else "в мире"
    
    prompt = prompts.get(topic, prompts["новость"]).format(
        country_context=country_context,
        country_article=country_article
    )
    
    data = {
        "messages": [
            {"role": "system", "content": "Ты профессиональный журналист."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 600,
        "stop": ["<|im_end|>"]
    }
    
    try:
        response = requests.post(LM_STUDIO_URL, headers=HEADERS, data=json.dumps(data))
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Ошибка генерации новости: {e}")
        return None

# Команды бота
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "🌍 Привет! Я новостной бот.\n\n"
        "Отправь местоположение или используй команды:\n"
        "/news - Новости\n"
        "/global_warming - Климатические новости\n"
        "/flood - Новости о наводнениях\n"
        "/set_country - Установить страну\n"
        "/my_country - Текущая страна"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['set_country'])
def set_country(message):
    msg = bot.send_message(message.chat.id, "Введите название страны:")
    bot.register_next_step_handler(msg, process_country)

def process_country(message):
    try:
        country = pycountry.countries.search_fuzzy(message.text.strip())[0]
        if set_user_country(message.chat.id, country.name):
            bot.send_message(message.chat.id, f"Страна установлена: {country.name}")
        else:
            bot.send_message(message.chat.id, "Ошибка сохранения")
    except:
        bot.send_message(message.chat.id, "Страна не распознана")

@bot.message_handler(commands=['my_country'])
def show_country(message):
    country = get_user_country(message.chat.id)
    if country:
        bot.send_message(message.chat.id, f"Ваша страна: {country}")
    else:
        bot.send_message(message.chat.id, "Страна не установлена")

@bot.message_handler(content_types=['location'])
def handle_location(message):
    country = get_country_name(message.location.latitude, message.location.longitude)
    if country and set_user_country(message.chat.id, country):
        bot.send_message(message.chat.id, f"Определена страна: {country}")
    else:
        bot.send_message(message.chat.id, "Не удалось определить страну")

def send_news(message, topic):
    country = get_user_country(message.chat.id)
    msg = bot.send_message(message.chat.id, "⌛ Генерирую новость...")
    
    news = generate_news_with_ai(topic, country)
    if news:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text=f"📌 {news}",
            parse_mode='Markdown'
        )
    else:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=msg.message_id,
            text="❌ Ошибка генерации"
        )

@bot.message_handler(commands=['news'])
def news_command(message):
    send_news(message, "новость")

@bot.message_handler(commands=['global_warming'])
def climate_command(message):
    send_news(message, "глобальное потепление")

@bot.message_handler(commands=['flood'])
def flood_command(message):
    send_news(message, "наводнение")

# Запуск бота
if __name__ == '__main__':
    init_database()
    print("Бот запущен")

    bot.infinity_polling()
